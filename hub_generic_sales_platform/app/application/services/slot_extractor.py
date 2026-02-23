import json
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import ContextSlotRepository
from app.core import domain
from app.infrastructure.llm.factory import get_llm_provider


class SlotExtractor:
    """
    Extract context slots from user message (Bước 4)
    
    Sử dụng LLM để trích xuất thông tin có cấu trúc (key-value) từ tin nhắn.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.slot_repo = ContextSlotRepository(db)
        self.llm_service = get_llm_provider()
    
    async def extract_slots(
        self,
        message: str,
        session_id: str,
        turn_id: str,
        allowed_keys: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Trích xuất slots từ tin nhắn sử dụng LLM. Returns list of dicts for repo creation."""
        
        extracted_data = await self._call_llm_extract(message, allowed_keys)
        slots_data = []
        
        for key, value in extracted_data.items():
            if allowed_keys and key not in allowed_keys:
                continue
                
            slot_data = {
                "session_id": session_id,
                "key": key,
                "value": str(value),
                "status": domain.SlotStatus.ACTIVE,
                "source": domain.SlotSource.INFERRED,
                "source_turn_id": turn_id
            }
            slots_data.append(slot_data)
            
        return slots_data
    
    async def _call_llm_extract(self, message: str, allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Gọi LLM để parse thông tin"""
        keys_hint = f"Các trường cần tìm: {', '.join(allowed_keys)}" if allowed_keys else "Trích xuất tất cả thông tin quan trọng."
        
        system_prompt = f"""Bạn là chuyên gia trích xuất thông tin (Slot Extractor).
Nhiệm vụ: Trích xuất các cặp key-value từ câu nói của người dùng.
{keys_hint}

Yêu cầu:
1. Chỉ trích xuất thông tin có thực trong câu. Không tự suy diễn.
2. Trả về định dạng JSON nguyên bản.
3. Nếu không có thông tin, trả về {{}}.

Ví dụ: "Tôi muốn tìm n8n flow giá dưới 5tr" -> {{"product_type": "n8n_flow", "price_max": 5000000}}
"""
        
        try:
            llm_result = await self.llm_service.generate_response(system_prompt, message)
            resp_str = llm_result.get("response", "")
            if "```json" in resp_str:
                resp_str = resp_str.split("```json")[1].split("```")[0].strip()
            elif "{" in resp_str:
                resp_str = resp_str[resp_str.find("{"):resp_str.rfind("}")+1]
                
            return json.loads(resp_str)
        except Exception:
            return {}

    async def save_slots(self, slots_data: List[Dict[str, Any]]) -> List[domain.RuntimeContextSlot]:
        """Lưu các slots đã trích xuất sử dụng repository"""
        saved_slots = []
        for slot_data in slots_data:
            slot = await self.slot_repo.create(slot_data)
            saved_slots.append(slot)
        return saved_slots
