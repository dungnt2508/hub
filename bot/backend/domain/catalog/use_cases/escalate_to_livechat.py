"""
Escalate to Livechat Use Case
"""
from typing import Optional, Dict, Any
from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class EscalateToLivechatUseCase(CatalogUseCase):
    """
    Escalate conversation to human support.
    
    Use case: User needs human assistance, bot escalates to livechat.
    Sets escalation flag in session and provides handoff message.
    """
    
    def __init__(self, repository=None):
        """
        Initialize escalate to livechat use case.
        
        Args:
            repository: Not used for this use case, but required by base class
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute escalate to livechat.
        
        Args:
            request: Domain request with optional reason and context
            
        Returns:
            Domain response with escalation confirmation
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract escalation reason and context
            reason = request.slots.get("reason") or request.slots.get("escalation_reason") or "User requested human support"
            context = request.slots.get("context") or request.slots.get("conversation_context")
            
            logger.info(
                "Escalating to livechat",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "reason": reason,
                    "has_context": bool(context),
                }
            )
            
            # Generate handoff message
            message = (
                "Chúng tôi đã chuyển bạn đến đội ngũ hỗ trợ trực tiếp. "
                "Một nhân viên sẽ hỗ trợ bạn trong giây lát. "
                "Vui lòng chờ trong khi chúng tôi kết nối..."
            )
            
            if reason and reason != "User requested human support":
                message += f"\n\nLý do: {reason}"
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=message,
                data={
                    "escalation": {
                        "escalated": True,
                        "reason": reason,
                        "context": context,
                        "timestamp": None,  # Will be set by API handler
                    },
                    "handoff": {
                        "service": "livechat",
                        "status": "connecting"
                    }
                },
                audit={
                    "intent": request.intent,
                    "escalation_reason": reason,
                    "has_context": bool(context),
                }
            )
            
        except Exception as e:
            logger.error(
                f"Escalate to livechat use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi chuyển đến hỗ trợ trực tiếp. Vui lòng thử lại sau.",
                error_code="ESCALATION_ERROR"
            )
