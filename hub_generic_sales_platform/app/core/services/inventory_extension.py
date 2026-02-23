from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database.repositories import InventoryRepository, InventoryLocationRepository
from app.infrastructure.database.models.offering import TenantInventoryItem, TenantOfferingVariant

class InventoryExtension:
    """Extension to handle Physical Offering Inventory capabilities"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.loc_repo = InventoryLocationRepository(db)

    async def get_offering_inventory(self, tenant_id: str, offering_id: str) -> List[Dict[str, Any]]:
        """Lấy tồn kho cho tất cả các variant của một offering"""
        stmt = select(TenantOfferingVariant).where(TenantOfferingVariant.offering_id == offering_id)
        variants = await self.db.execute(stmt)
        variant_list = variants.scalars().all()
        
        inventory_summary = []
        for var in variant_list:
            stock = await self.inventory_repo.get_stock_status(tenant_id, var.sku)
            if stock:
                inventory_summary.append(stock)
        return inventory_summary

    async def update_stock(self, tenant_id: str, sku: str, location_code: str, new_qty: int) -> bool:
        """Cập nhật tồn kho"""
        variant = await self.db.execute(
            select(TenantOfferingVariant).where(
                TenantOfferingVariant.sku == sku, 
                TenantOfferingVariant.tenant_id == tenant_id
            )
        )
        v_obj = variant.scalar_one_or_none()
        if not v_obj:
            return False
            
        location = await self.loc_repo.get_by_code(location_code, tenant_id)
        if not location:
            return False
            
        stmt = select(TenantInventoryItem).where(
            TenantInventoryItem.variant_id == v_obj.id,
            TenantInventoryItem.location_id == location.id
        )
        item = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if item:
            item.stock_qty = new_qty
        else:
            item = TenantInventoryItem(
                tenant_id=tenant_id,
                variant_id=v_obj.id,
                location_id=location.id,
                stock_qty=new_qty
            )
            self.db.add(item)
            
        await self.db.commit()
        return True
