import uuid
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import MigrationJobRepository
from app.infrastructure.database.models.knowledge import MigrationJob, MigrationJobStatus, MigrationSourceType
import logging

logger = logging.getLogger(__name__)

class BaseMigrationProvider:
    """Abstract interface for all migration sources (Web, Excel, API)"""
    
    async def fetch_and_parse(self, job: MigrationJob, db: AsyncSession) -> Dict[str, Any]:
        """
        Main logic for the provider:
        1. Fetch raw data (Scrape link / Read file)
        2. Partial standardization (Optional)
        Returns a dict to be stored in staged_data or raw_data
        """
        raise NotImplementedError

class MigrationService:
    """Orchestrates different migration providers and manages Job lifecycle"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MigrationJobRepository(db)
        self._providers: Dict[str, Type[BaseMigrationProvider]] = {}

    def register_provider(self, source_type: str, provider_cls: Type[BaseMigrationProvider]):
        self._providers[source_type] = provider_cls

    async def create_job(self, tenant_id: str, domain_id: str, source_type: str, metadata: Dict[str, Any], bot_id: Optional[str] = None) -> MigrationJob:
        """Create a new migration job record"""
        job = await self.repo.create({
            "domain_id": domain_id,
            "bot_id": bot_id,
            "source_type": source_type,
            "batch_metadata": metadata,
            "status": MigrationJobStatus.PENDING
        }, tenant_id=tenant_id)
        return job

    async def run_job_sync(self, job_id: str, tenant_id: str):
        """
        Synchronous execution (usually called in BackgroundTask).
        Runs the provider's logic and updates status.
        """
        job = await self.repo.get(job_id, tenant_id=tenant_id)
        if not job:
            return

        provider_cls = self._providers.get(job.source_type)
        if not provider_cls:
            await self.repo.update(job, {
                "status": MigrationJobStatus.FAILED,
                "error_log": f"Provider not found for {job.source_type}"
            }, tenant_id=tenant_id)
            return

        try:
            job = await self.repo.update(job, {"status": MigrationJobStatus.PROCESSING}, tenant_id=tenant_id)
            
            # Khởi tạo nếu là Class, hoặc dùng luôn nếu là Instance
            if isinstance(provider_cls, type):
                provider = provider_cls()
            else:
                provider = provider_cls
                
            result = await provider.fetch_and_parse(job, self.db)
            
            await self.repo.update(job, {
                "staged_data": result,
                "status": MigrationJobStatus.STAGED
            }, tenant_id=tenant_id)
        except Exception as e:
            logger.exception(f"Migration job {job_id} failed")
            await self.repo.update(job, {
                "status": MigrationJobStatus.FAILED,
                "error_log": str(e)
            }, tenant_id=tenant_id)

    async def commit_job(self, job_id: str, tenant_id: str):
        """
        Pushes staged data into Offering/Variant/Attribute tables.
        Giống seed: TenantOffering → TenantOfferingVersion → TenantOfferingVariant (+ attributes).
        """
        job = await self.repo.get(job_id, tenant_id=tenant_id)
        if not job or job.status != MigrationJobStatus.STAGED:
            raise Exception("Job không ở trạng thái STAGED để commit")

        from app.infrastructure.database.repositories import (
            OfferingRepository, OfferingVersionRepository, OfferingVariantRepository,
            OfferingAttributeRepository, TenantPriceListRepository, TenantSalesChannelRepository
        )
        from app.infrastructure.database.repositories import DomainAttributeDefinitionRepository
        from app.infrastructure.database.models.offering import (
            OfferingStatus, TenantPriceList, TenantVariantPrice,
            TenantSalesChannel
        )

        offering_repo = OfferingRepository(self.db)
        version_repo = OfferingVersionRepository(self.db)
        variant_repo = OfferingVariantRepository(self.db)
        attr_val_repo = OfferingAttributeRepository(self.db)
        attr_def_repo = DomainAttributeDefinitionRepository(self.db)
        price_list_repo = TenantPriceListRepository(self.db)
        channel_repo = TenantSalesChannelRepository(self.db)

        # 0b. Lấy hoặc tạo default price list (ưu tiên channel WEB) để lưu giá variant
        price_lists = await price_list_repo.get_multi(tenant_id=tenant_id)
        default_price_list = None
        if price_lists:
            ch_web = await channel_repo.get_by_code("WEB", tenant_id)
            web_pl = next((pl for pl in price_lists if getattr(pl, "channel_id", None) and ch_web and getattr(pl, "channel_id") == ch_web.id), None)
            default_price_list = web_pl or price_lists[0]
        if not default_price_list:
            channel = await channel_repo.get_by_code("WEB", tenant_id)
            if not channel:
                ch = TenantSalesChannel(tenant_id=tenant_id, code="WEB", name="Web Chat", is_active=True)
                self.db.add(ch)
                await self.db.flush()
                channel = ch
            pl = TenantPriceList(tenant_id=tenant_id, code="migration-default", channel_id=channel.id)
            self.db.add(pl)
            await self.db.flush()
            default_price_list = pl
        if not default_price_list:
            logger.warning(f"Commit job {job_id}: No price list. Variant prices will NOT be saved.")

        # 0. Fetch Attribute Definitions for this domain to map types
        attr_defs = {}
        if job.domain_id:
            defs = await attr_def_repo.get_by_domain(job.domain_id)
            attr_defs = {ad.key: ad for ad in defs}

        staged_data = job.staged_data or {}
        offerings = staged_data.get("offerings", [])
        if not offerings:
            logger.warning(f"Commit job {job_id}: staged_data has no offerings. Keys: {list(staged_data.keys())}")
            raise Exception("Staged data không có offerings. Không thể commit.")

        logger.info(f"Commit job {job_id}: inserting {len(offerings)} offerings into catalog (tenant={tenant_id}, domain={job.domain_id})")

        for o_data in offerings:
            code = o_data.get("code") or f"MIG-{uuid.uuid4().hex[:8].upper()}"
            name = o_data.get("name") or "Offering"
            if not code or not name:
                logger.warning(f"Skipping offering with empty code/name: {o_data}")
                continue
            # 1. Create TenantOffering (như seed)
            offering_obj = await offering_repo.create({
                "domain_id": job.domain_id,
                "bot_id": job.bot_id,
                "code": code,
                "status": OfferingStatus.ACTIVE
            }, tenant_id=job.tenant_id)

            # 2. Create Initial Version (TenantOfferingVersion - như seed)
            version_obj = await version_repo.create({
                "offering_id": offering_obj.id,
                "version": 1,
                "name": name,
                "description": o_data.get("description"),
                "status": OfferingStatus.ACTIVE
            })

            # 3. Create Attributes (Ontology Mapping)
            o_attrs = o_data.get("attributes", {}) or {}
            # Filter out None/null values to prevent constraint violations
            o_attrs = {k: v for k, v in o_attrs.items() if v is not None}
            
            for key, val in o_attrs.items():
                attr_def = attr_defs.get(key)
                if not attr_def:
                    continue
                
                # Validate domain boundary: attribute phải thuộc cùng domain với offering
                if attr_def.domain_id != job.domain_id:
                    logger.warning(f"Skipping attribute '{key}' - domain mismatch: attr.domain_id={attr_def.domain_id} != job.domain_id={job.domain_id}")
                    continue
                
                # Validate và coerce value với type safety (không fallback)
                from app.core.services.attribute_validator import AttributeValueValidator
                try:
                    # Build attr_data with only the required fields
                    attr_data = {
                        "offering_version_id": version_obj.id,
                        "attribute_def_id": attr_def.id
                    }
                    # Merge validated data - validator returns dict with only ONE value_* key
                    attr_data.update(AttributeValueValidator.validate_and_coerce(val, attr_def))
                    # Validate the data structure (ensure exactly 1 value column)
                    attr_data = AttributeValueValidator.ensure_single_value(attr_data)
                    await attr_val_repo.create(attr_data)
                except Exception as e:
                    logger.error(f"Failed to create attribute '{key}' for offering '{o_data.get('code')}': {str(e)}")
                    # Continue với offering khác thay vì fail toàn bộ job
                    continue

            # 4. Create Variants (theo seed: TenantOfferingVariant) + TenantVariantPrice
            variants_raw = o_data.get("variants") or []
            offering_price = o_data.get("price")  # Price cấp offering khi không có variants
            if not variants_raw:
                variants_raw = [{"sku": f"{code}-STD", "name": name, "price": offering_price}]
            for idx, v_data in enumerate(variants_raw):
                v_data = v_data if isinstance(v_data, dict) else {}
                variant_obj = await variant_repo.create({
                    "offering_id": offering_obj.id,
                    "sku": v_data.get("sku") or f"{code}-V{idx+1}",
                    "name": v_data.get("name") or name,
                    "status": OfferingStatus.ACTIVE
                }, tenant_id=job.tenant_id)
                # 5. Lưu giá vào TenantVariantPrice (price_list gắn channel)
                amount = v_data.get("price") if v_data.get("price") is not None else offering_price
                if default_price_list and amount is not None:
                    try:
                        amt = float(amount) if not isinstance(amount, (int, float)) else amount
                        if amt >= 0:
                            vp = TenantVariantPrice(
                                price_list_id=default_price_list.id,
                                variant_id=variant_obj.id,
                                amount=amt,
                                currency="VND"
                            )
                            self.db.add(vp)
                    except (TypeError, ValueError):
                        logger.warning(f"Invalid price for variant {v_data.get('sku')}: {amount}")

        await self.db.flush()
        await self.repo.update(job, {"status": MigrationJobStatus.COMPLETED}, tenant_id=job.tenant_id)
        await self.db.flush()
        logger.info(f"Commit job {job_id}: done. {len(offerings)} offerings created (session will commit on request end).")
