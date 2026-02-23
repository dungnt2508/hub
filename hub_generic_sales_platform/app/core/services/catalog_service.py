from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.shared.db_utils import transaction_scope
from app.infrastructure.database.repositories import (
    OfferingRepository, OfferingVersionRepository, OfferingVariantRepository,
    OfferingAttributeRepository
)
from app.infrastructure.database.repositories import InventoryRepository, InventoryLocationRepository
from app.infrastructure.database.repositories import TenantPriceListRepository, TenantSalesChannelRepository, VariantPriceRepository
from app.core.services.attribute_resolver import AttributeResolverService
from app.core.services.inventory_extension import InventoryExtension
from app.infrastructure.database.models.offering import (
    TenantOffering, TenantOfferingVersion, TenantOfferingAttributeValue, TenantOfferingVariant, TenantInventoryItem, 
    TenantVariantPrice,
    OfferingStatus
)


class CatalogService:
    """Service xử lý nghiệp vụ Catalog tập trung (Domain Logic)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.offering_repo = OfferingRepository(db)
        self.version_repo = OfferingVersionRepository(db)
        self.variant_repo = OfferingVariantRepository(db)
        self.attr_val_repo = OfferingAttributeRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.price_repo = TenantPriceListRepository(db)
        self.variant_price_repo = VariantPriceRepository(db)
        self.channel_repo = TenantSalesChannelRepository(db)
        self.loc_repo = InventoryLocationRepository(db)
        self.attr_resolver = AttributeResolverService(db)
        self.inventory_ext = InventoryExtension(db)

    async def get_offering_for_bot(
        self, 
        tenant_id: str, 
        offering_code: str, 
        channel_code: str = "WEB",
        domain_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy toàn bộ thông tin 'thực' của offering.
        Kết hợp: Nội dung Active Version + Giá theo Channel + Tồn kho tổng hợp.
        """
        # 1. Lấy Offering
        offering = await self.offering_repo.get_by_code(offering_code, tenant_id, domain_id=domain_id)
        if not offering or offering.status != OfferingStatus.ACTIVE:
            return None

        # 2. Lấy Active Version
        version = await self.version_repo.get_active_version(offering.id, tenant_id=tenant_id)
        if not version:
            return None

        # 3. Lấy Giá từ VARIANT via offering_id (không cần eager load)
        current_price = None
        prices = await self.price_repo.get_prices_for_offering(tenant_id, channel_code, offering.id)
        if prices:
            # Lấy giá thấp nhất (min price cho offering)
            min_price = prices[0]  # Already sorted by amount ASC
            current_price = {
                "amount": float(min_price.amount),
                "currency": min_price.currency,
                "compare_at": float(min_price.compare_at) if min_price.compare_at else None
            }

        # 4. Lấy Tồn kho
        inventory_summary = []
        enabled_capabilities = kwargs.get("enabled_capabilities", [])
        if "inventory" in enabled_capabilities:
            inventory_summary = await self.inventory_ext.get_offering_inventory(tenant_id, offering.id)

        # 5. Lấy các thuộc tính mở rộng
        attributes = await self.attr_val_repo.get_by_version(version.id, tenant_id=tenant_id)
        resolved_attrs = await self.attr_resolver.resolve_attributes(
            tenant_id, 
            attributes, 
            filter_display_only=False
        )
        
        attr_data = {
            attr["key"]: attr["value"] 
            for attr in resolved_attrs
        }
        
        attr_metadata = {
            attr["key"]: {
                "label": attr["label"],
                "is_display": attr["is_display"],
                "display_order": attr["display_order"],
                "is_searchable": attr["is_searchable"]
            }
            for attr in resolved_attrs
        }

        return {
            "id": offering.id,
            "code": offering.code,
            "type": offering.type,
            "domain_id": offering.domain_id,
            "name": version.name,
            "description": version.description,
            "version": version.version,
            "version_id": version.id,
            "attributes": attr_data,
            "attributes_metadata": attr_metadata,
            "price": current_price,
            "inventory": inventory_summary,
            "status": offering.status
        }

    async def update_inventory(
        self, 
        tenant_id: str, 
        sku: str, 
        location_code: str, 
        new_qty: int
    ) -> bool:
        """Cập nhật tồn kho"""
        async with transaction_scope(self.db):
            variant = await self.variant_repo.get_by_sku(sku, tenant_id)
            if not variant:
                return False
                
            location = await self.loc_repo.get_by_code(location_code, tenant_id)
            if not location:
                return False
                
            stmt = select(TenantInventoryItem).where(
                TenantInventoryItem.variant_id == variant.id,
                TenantInventoryItem.location_id == location.id
            )
            item = (await self.db.execute(stmt)).scalar_one_or_none()
            
            if item:
                item.stock_qty = new_qty
            else:
                item = TenantInventoryItem(
                    tenant_id=tenant_id,
                    variant_id=variant.id,
                    location_id=location.id,
                    stock_qty=new_qty
                )
                self.db.add(item)
                
            return True

    async def publish_version(self, offering_id: str, version_number: int, tenant_id: str) -> bool:
        """Kích hoạt một phiên bản offering với tenant isolation"""
        async with transaction_scope(self.db):
            # 1. Verify offering ownership
            offering = await self.offering_repo.get(offering_id, tenant_id=tenant_id)
            if not offering:
                return False

            # 2. Find target version
            stmt = select(TenantOfferingVersion).where(
                TenantOfferingVersion.offering_id == offering_id,
                TenantOfferingVersion.version == version_number
            )
            target = (await self.db.execute(stmt)).scalar_one_or_none()
            if not target:
                return False
                
            # 3. Archive other active versions
            stmt_actives = select(TenantOfferingVersion).where(
                TenantOfferingVersion.offering_id == offering_id, 
                TenantOfferingVersion.status == OfferingStatus.ACTIVE
            )
            current_actives = (await self.db.execute(stmt_actives)).scalars().all()
            for v in current_actives:
                v.status = OfferingStatus.ARCHIVED
                
            target.status = OfferingStatus.ACTIVE

            # 4. Activate offering if not already
            if offering.status != OfferingStatus.ACTIVE:
                offering.status = OfferingStatus.ACTIVE
                
            return True

    async def create_draft_version(self, offering_id: str, tenant_id: str, copy_from_version: Optional[int] = None) -> Optional[TenantOfferingVersion]:
        """Tạo một bản nháp mới cho offering với tenant isolation"""
        async with transaction_scope(self.db):
            # 1. Verify offering ownership
            offering = await self.offering_repo.get(offering_id, tenant_id=tenant_id)
            if not offering:
                raise ValueError("Offering not found or not owned by tenant")

            latest = await self.version_repo.get_latest_version(offering_id, tenant_id=tenant_id)
            next_version = (latest.version + 1) if latest else 1
            
            source = None
            if copy_from_version:
                stmt = select(TenantOfferingVersion).where(TenantOfferingVersion.offering_id == offering_id, TenantOfferingVersion.version == copy_from_version)
                source = (await self.db.execute(stmt)).scalar_one_or_none()
            elif latest:
                source = latest
                
            new_version = TenantOfferingVersion(
                offering_id=offering_id,
                version=next_version,
                name=source.name if source else "New Version",
                description=source.description if source else None,
                status=OfferingStatus.ACTIVE # Defaulting to Active Draft for simplicity here
            )
            self.db.add(new_version)
            await self.db.flush()
            
            # 2. Copy Attributes (Instance Data) with tenant isolation check
            if source:
                old_attrs = await self.attr_val_repo.get_by_version(source.id, tenant_id=tenant_id)
                for oa in old_attrs:
                    # Only copy the value column that's actually set
                    attr_data = {
                        "offering_version_id": new_version.id,
                        "attribute_def_id": oa.attribute_def_id
                    }
                    # Copy only the non-NULL value
                    if oa.value_text is not None:
                        attr_data["value_text"] = oa.value_text
                    elif oa.value_number is not None:
                        attr_data["value_number"] = oa.value_number
                    elif oa.value_bool is not None:
                        attr_data["value_bool"] = oa.value_bool
                    elif oa.value_json is not None:
                        attr_data["value_json"] = oa.value_json
                    
                    new_attr = TenantOfferingAttributeValue(**attr_data)
                    self.db.add(new_attr)
            
            return new_version

    async def create_variant(self, offering_id: str, tenant_id: str, sku: str, name: str) -> TenantOfferingVariant:
        """Tạo một biến thể mới"""
        async with transaction_scope(self.db):
            new_variant = TenantOfferingVariant(
                offering_id=offering_id,
                tenant_id=tenant_id,
                sku=sku,
                name=name,
                status=OfferingStatus.ACTIVE
            )
            self.db.add(new_variant)
            await self.db.flush()
            await self.db.refresh(new_variant)
            return new_variant

    async def update_variant(self, variant_id: str, tenant_id: str, name: Optional[str] = None, status: Optional[str] = None) -> Optional[TenantOfferingVariant]:
        """Cập nhật biến thể với tenant isolation"""
        async with transaction_scope(self.db):
            variant = await self.variant_repo.get(variant_id, tenant_id=tenant_id)
            if not variant:
                return None
            
            if name:
                variant.name = name
            if status:
                variant.status = status
                
            return variant

    async def delete_variant(self, variant_id: str, tenant_id: str) -> bool:
        """Xóa biến thể với tenant isolation"""
        return await self.variant_repo.delete(variant_id, tenant_id=tenant_id)

    async def set_variant_price(
        self,
        variant_id: str,
        price_list_id: str,
        tenant_id: str,
        amount: float,
        currency: str = "VND",
        compare_at: Optional[float] = None
    ) -> TenantVariantPrice:
        """
        Thiết lập hoặc cập nhật giá cho biến thể.
        """
        async with transaction_scope(self.db):
            # 1. Verify variant exists and owned by tenant
            variant = await self.variant_repo.get(variant_id, tenant_id=tenant_id)
            if not variant:
                raise ValueError(f"Variant {variant_id} not found for this tenant")
            
            # 2. Verify price_list exists and owned by tenant
            price_list = await self.price_repo.get(price_list_id, tenant_id=tenant_id)
            if not price_list:
                raise ValueError(f"Price list {price_list_id} not found for this tenant")
            
            # 3. Check if price already exists (upsert logic)
            stmt = select(TenantVariantPrice).where(
                TenantVariantPrice.variant_id == variant_id,
                TenantVariantPrice.price_list_id == price_list_id
            )
            result = await self.db.execute(stmt)
            existing_price = result.scalar_one_or_none()
            
            if existing_price:
                existing_price.amount = amount
                existing_price.currency = currency
                existing_price.compare_at = compare_at
                await self.db.flush()  # ✅ Explicit flush for update
            else:
                existing_price = TenantVariantPrice(
                    variant_id=variant_id,
                    price_list_id=price_list_id,
                    amount=amount,
                    currency=currency,
                    compare_at=compare_at
                )
                self.db.add(existing_price)
                await self.db.flush()  # ✅ Explicit flush for insert
                
            await self.db.refresh(existing_price)
            return existing_price
