from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import ContextSlotRepository
from app.core import domain


class ValidationSlotStatus(str, Enum):
    """Trạng thái kiểm tra slot"""
    SLOT_OK = "SLOT_OK"
    SLOT_MISSING = "SLOT_MISSING"
    SLOT_AMBIGUOUS = "SLOT_AMBIGUOUS"
    SLOT_CONFLICT = "SLOT_CONFLICT"


class SlotValidator:
    """
    Validate context slots (Bước 6)
    
    Kiểm tra tính đầy đủ và logic của các slots.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.slot_repo = ContextSlotRepository(db)
    
    async def validate_slots(
        self,
        session_id: str,
        required_keys: Optional[List[str]] = None
    ) -> Dict[str, ValidationSlotStatus]:
        """Kiểm tra tất cả slots của session"""
        slots = await self.slot_repo.get_by_session(session_id)
        
        # Group slots by key
        slots_by_key: Dict[str, List[domain.RuntimeContextSlot]] = {}
        for slot in slots:
            if slot.key not in slots_by_key:
                slots_by_key[slot.key] = []
            slots_by_key[slot.key].append(slot)
        
        validation_results: Dict[str, ValidationSlotStatus] = {}
        
        all_keys = set(slots_by_key.keys())
        if required_keys:
            all_keys.update(required_keys)
        
        for key in all_keys:
            key_slots = slots_by_key.get(key, [])
            
            if not key_slots:
                validation_results[key] = ValidationSlotStatus.SLOT_MISSING
                continue
            
            if len(key_slots) > 1:
                values = [s.value for s in key_slots]
                if len(set(values)) == 1:
                    validation_results[key] = ValidationSlotStatus.SLOT_AMBIGUOUS
                else:
                    validation_results[key] = ValidationSlotStatus.SLOT_CONFLICT
                continue
            
            validation_results[key] = ValidationSlotStatus.SLOT_OK
        
        return validation_results
    
    def get_overall_status(self, validation_results: Dict[str, ValidationSlotStatus]) -> ValidationSlotStatus:
        """Lấy trạng thái tổng quát"""
        if ValidationSlotStatus.SLOT_CONFLICT in validation_results.values():
            return ValidationSlotStatus.SLOT_CONFLICT
        
        if ValidationSlotStatus.SLOT_AMBIGUOUS in validation_results.values():
            return ValidationSlotStatus.SLOT_AMBIGUOUS
        
        if ValidationSlotStatus.SLOT_MISSING in validation_results.values():
            return ValidationSlotStatus.SLOT_MISSING
        
        return ValidationSlotStatus.SLOT_OK
