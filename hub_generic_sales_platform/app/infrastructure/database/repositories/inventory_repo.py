from typing import Optional, List, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.offering import (
    TenantInventoryItem as InventoryItemModel,
    TenantInventoryLocation as LocationModel
)

# Domain Entities
from app.core import domain
from app.core.interfaces.knowledge_repo import IInventoryRepository


class InventoryRepository(BaseRepository[InventoryItemModel], IInventoryRepository):
    """Inventory repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InventoryItemModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantInventoryItem]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantInventoryItem.model_validate(db_obj) if db_obj else None

    async def get_stock_status(self, tenant_id: str, sku: str) -> Optional[Dict[str, Any]]:
        """Lấy trạng thái tồn kho của SKU bằng truy vấn trực tiếp (Báo cáo tổng hợp)"""
        stmt = text("""
            SELECT 
                ov.id,
                ov.tenant_id,
                ov.sku,
                ov.name as variant_name,
                COALESCE(SUM(ii.stock_qty), 0) as aggregate_qty,
                COALESCE(SUM(ii.safety_stock), 0) as aggregate_safety_stock,
                CASE 
                    WHEN COALESCE(SUM(ii.stock_qty), 0) > COALESCE(SUM(ii.safety_stock), 0) THEN 'in_stock'
                    WHEN COALESCE(SUM(ii.stock_qty), 0) > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status
            FROM tenant_offering_variant ov
            LEFT JOIN tenant_inventory_item ii ON ov.id = ii.variant_id
            WHERE ov.tenant_id = :tenant_id AND ov.sku = :sku
            GROUP BY ov.id, ov.tenant_id, ov.sku, ov.name
        """)
        
        result = await self.db.execute(stmt, {"tenant_id": tenant_id, "sku": sku})
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_all_stock_status(self, tenant_id: str, bot_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy trạng thái tồn kho của tất cả offering trong tenant/bot"""
        query = """
            SELECT 
                ov.id,
                ov.tenant_id,
                ov.sku,
                ov.name as variant_name,
                COALESCE(SUM(ii.stock_qty), 0) as aggregate_qty,
                COALESCE(SUM(ii.safety_stock), 0) as aggregate_safety_stock,
                CASE 
                    WHEN COALESCE(SUM(ii.stock_qty), 0) > COALESCE(SUM(ii.safety_stock), 0) THEN 'in_stock'
                    WHEN COALESCE(SUM(ii.stock_qty), 0) > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status
            FROM tenant_offering_variant ov
            JOIN tenant_offering o ON ov.offering_id = o.id
            LEFT JOIN tenant_inventory_item ii ON ov.id = ii.variant_id
            WHERE ov.tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id}
        # Bot_id filtering would need linking via Offering if needed, but Offering currently doesn't have bot_id directly.
        # Bots usually link to Offerings via BotUseCase or similar, but for stock status we might just filter by tenant.
            
        query += " GROUP BY ov.id, ov.tenant_id, ov.sku, ov.name"
        
        stmt = text(query)
        result = await self.db.execute(stmt, params)
        return [dict(r) for r in result.mappings().all()]


class InventoryLocationRepository(BaseRepository[LocationModel]):
    """Repository cho các điểm lưu kho/cửa hàng với Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(LocationModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantInventoryLocation]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantInventoryLocation.model_validate(db_obj) if db_obj else None

    async def get_by_code(self, code: str, tenant_id: str) -> Optional[domain.TenantInventoryLocation]:
        stmt = select(LocationModel).where(
            LocationModel.code == code,
            LocationModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantInventoryLocation.model_validate(db_obj) if db_obj else None
