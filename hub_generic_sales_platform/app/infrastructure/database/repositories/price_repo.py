from typing import Optional, List, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.offering import (
    TenantVariantPrice as VariantPriceModel,
    TenantOfferingVariant as OfferingVariantModel,
    TenantSalesChannel as SalesChannelModel,
    TenantPriceList as PriceListModel
)

# Domain Entities
from app.core import domain
from app.core.interfaces.knowledge_repo import ISalesChannelRepository, IPriceListRepository


class TenantSalesChannelRepository(BaseRepository[SalesChannelModel], ISalesChannelRepository):
    """Repository quản lý kênh bán hàng với Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(SalesChannelModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantSalesChannel]:
        db_obj = await super().get(id, tenant_id)
        # Note: SalesChannel entity should be defined in domain, if not I'll use generic
        # For now assume it is in domain.Knowledge
        return domain.TenantSalesChannel.model_validate(db_obj) if db_obj else None

    async def get_by_code(self, code: str, tenant_id: str) -> Optional[domain.TenantSalesChannel]:
        stmt = select(SalesChannelModel).where(
            SalesChannelModel.code == code,
            SalesChannelModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantSalesChannel.model_validate(db_obj) if db_obj else None


class TenantPriceListRepository(BaseRepository[PriceListModel], IPriceListRepository):
    """Repository quản lý các bảng giá với Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(PriceListModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantPriceList]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantPriceList.model_validate(db_obj) if db_obj else None

    async def get_prices_for_offering(self, tenant_id: str, channel_code: str, offering_id: str) -> List[domain.TenantVariantPrice]:
        """Lấy giá của variants thuộc một offering cho channel cụ thể
        
        Chỉ lấy giá từ channel được request, KHÔNG fallback
        """
        from app.infrastructure.database.models.offering import TenantOfferingVariant
        now = datetime.now()
        
        # Lấy PriceList ids cho channel cụ thể
        pl_stmt = select(PriceListModel.id).where(
            PriceListModel.tenant_id == tenant_id,
            PriceListModel.channel_id.in_(
                select(SalesChannelModel.id).where(
                    SalesChannelModel.code == channel_code,
                    SalesChannelModel.tenant_id == tenant_id
                )
            ),
            # Valid time range
            (PriceListModel.valid_from == None) | (PriceListModel.valid_from <= now),
            (PriceListModel.valid_to == None) | (PriceListModel.valid_to >= now)
        )
        pl_ids = (await self.db.execute(pl_stmt)).scalars().all()
        
        if not pl_ids:
            return []

        # Lấy giá của tất cả variants của offering này
        price_stmt = select(VariantPriceModel).join(
            TenantOfferingVariant, VariantPriceModel.variant_id == TenantOfferingVariant.id
        ).where(
            VariantPriceModel.price_list_id.in_(pl_ids),
            TenantOfferingVariant.offering_id == offering_id
        ).order_by(VariantPriceModel.amount.asc())
        
        result = await self.db.execute(price_stmt)
        return [domain.TenantVariantPrice.model_validate(obj) for obj in result.scalars().all()]

class VariantPriceRepository(BaseRepository[VariantPriceModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(VariantPriceModel, db)

    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantVariantPrice]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantVariantPrice.model_validate(db_obj) if db_obj else None
