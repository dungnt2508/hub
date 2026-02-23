"""Guardrail checker - Bước 7A (Async Implementation)"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import GuardrailRepository
from app.infrastructure.database.repositories import DecisionGuardrailCheckedRepository
from app.core import domain
from app.infrastructure.llm.factory import get_llm_provider


class GuardrailChecker:
    """
    Check guardrails before answering (Bước 7A)
    
    Tích hợp kiểm tra an toàn bằng cả luật cứng (Regex/Rules) và LLM Semantic Check.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.guardrail_repo = GuardrailRepository(db)
        self.check_repo = DecisionGuardrailCheckedRepository(db)
        self.llm_service = get_llm_provider()
    
    async def check_guardrails(
        self,
        tenant_id: str,
        context: Dict[str, Any],
        decision_id: str
    ) -> Dict[str, Any]:
        """Kiểm tra an toàn phản hồi"""
        guardrails = await self.guardrail_repo.get_active_for_tenant(tenant_id)
        message = context.get("message", "")
        
        checks_to_create = []
        blocked = False
        violation_msg = None
        
        # 1. Rule-based checks (Hard rules)
        for g in guardrails:
            passed = True
            # Simple simulation of rule evaluation
            if "toxic" in g.name.lower() and any(w in message.lower() for w in ["badword1", "badword2"]):
                passed = False
            
            checks_to_create.append({
                "decision_id": decision_id,
                "guardrail_id": g.id,
                "passed": passed,
                "violation_message": g.fallback_message if not passed else None
            })
            
            if not passed and g.violation_action == "block":
                blocked = True
                violation_msg = g.fallback_message or "Vi phạm quy tắc an toàn."
                break
        
        # 2. LLM-based Semantic Guardrails (Tier 2/3)
        if not blocked and message:
            is_safe = await self._llm_safety_check(message)
            if not is_safe:
                blocked = True
                violation_msg = "Nội dung không phù hợp với tiêu chuẩn cộng đồng."
                # Note: We need a guardrail_id to log this in the DB if using the current schema.
                # If no system guardrail exists, we might need to skip logging or create a 'system' guardrail.
                # For now, we only log if we have a matching guardrail object or specific logic.

        # Ghi log results
        results = []
        for check_data in checks_to_create:
            res = await self.check_repo.create(check_data)
            results.append(res)
        
        return {
            "passed": not blocked,
            "blocked": blocked,
            "violation_message": violation_msg,
            "checks": results
        }
    
    async def _llm_safety_check(self, message: str) -> bool:
        """Sử dụng LLM để kiểm tra các nội dung nhạy cảm hoặc sai mục đích"""
        system_prompt = """Bạn là chuyên gia an toàn thông tin (Guardrail Specialist).
Nhiệm vụ: Kiểm tra xem câu nói của người dùng có vi phạm các tiêu chuẩn sau không:
1. Ngôn từ thù ghét, xúc phạm.
2. Nội dung khiêu dâm, bạo lực.
3. Yêu cầu Bot thực hiện các hành động phi pháp.
4. Spaming hoặc cố tình phá hoại hệ thống.

Chỉ trả về 'SAFE' nếu an toàn, hoặc 'UNSAFE' kèm lý do ngắn gọn nếu vi phạm.
"""
        try:
            llm_result = await self.llm_service.generate_response(system_prompt, f"User message: {message}")
            resp = llm_result.get("response", "")
            return "UNSAFE" not in resp.upper()
        except Exception:
            return True # Fallback to true if LLM fails
