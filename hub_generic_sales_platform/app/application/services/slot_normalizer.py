from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import ContextSlotRepository
from app.core import domain


class SlotNormalizer:
    """
    Normalize slot values (Bước 5)
    
    Chuẩn hóa giá trị các slots (ví dụ: "iphone 15" -> "IPHONE_15").
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.slot_repo = ContextSlotRepository(db)
    
    async def normalize_slot(self, slot: domain.RuntimeContextSlot, mapping_rules: Optional[Dict] = None) -> domain.RuntimeContextSlot:
        """Chuẩn hóa một slot đơn lẻ"""
        if not mapping_rules:
            return slot
        
        normalized_value = mapping_rules.get(slot.value.lower(), slot.value)
        
        if normalized_value != slot.value:
            # Domain object is mutable, but we need to persist it
            slot = await self.slot_repo.update(slot, {"value": normalized_value})
        
        return slot
    
    async def normalize_slots(
        self,
        session_id: str,
        mapping_rules: Optional[Dict] = None
    ) -> List[domain.RuntimeContextSlot]:
        """Chuẩn hóa tất cả active slots của session"""
        slots = await self.slot_repo.get_by_session(session_id)
        
        normalized_slots = []
        for slot in slots:
            normalized = await self.normalize_slot(slot, mapping_rules)
            normalized_slots.append(normalized)
        
        return normalized_slots
