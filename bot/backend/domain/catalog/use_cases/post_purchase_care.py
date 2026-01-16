"""
Post-Purchase Care Use Case
"""
from typing import Optional, Dict, Any
from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class PostPurchaseCareUseCase(CatalogUseCase):
    """
    Post-purchase support and care.
    
    Use case: User needs help after purchase (returns, refunds, feedback, etc.)
    """
    
    def __init__(self, repository=None):
        """
        Initialize post-purchase care use case.
        
        Args:
            repository: Not used for this use case, but required by base class
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute post-purchase care.
        
        Args:
            request: Domain request with order_id and issue_type in slots
            
        Returns:
            Domain response with support information
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract order and issue info
            order_id = request.slots.get("order_id") or request.slots.get("order_number")
            issue_type = request.slots.get("issue_type") or request.slots.get("problem_type")
            feedback = request.slots.get("feedback") or request.slots.get("message")
            
            logger.info(
                "Post-purchase care request",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "order_id": order_id,
                    "issue_type": issue_type,
                    "has_feedback": bool(feedback),
                }
            )
            
            # Determine response based on issue type
            if issue_type:
                issue_type_lower = issue_type.lower()
                
                if "return" in issue_type_lower or "trả" in issue_type_lower:
                    message = (
                        "Chúng tôi hiểu bạn muốn trả hàng. "
                        "Vui lòng cung cấp mã đơn hàng và lý do trả hàng. "
                        "Chúng tôi sẽ xử lý yêu cầu của bạn trong vòng 24-48 giờ."
                    )
                    if not order_id:
                        return DomainResponse(
                            status=DomainResult.NEED_MORE_INFO,
                            message="Vui lòng cung cấp mã đơn hàng để xử lý yêu cầu trả hàng.",
                            missing_slots=["order_id"],
                            next_action="ASK_SLOT",
                            next_action_params={
                                "slot_name": "order_id",
                                "all_missing": ["order_id"]
                            }
                        )
                
                elif "refund" in issue_type_lower or "hoàn tiền" in issue_type_lower:
                    message = (
                        "Chúng tôi sẽ xử lý yêu cầu hoàn tiền của bạn. "
                        "Vui lòng cung cấp mã đơn hàng và thông tin tài khoản ngân hàng (nếu cần)."
                    )
                    if not order_id:
                        return DomainResponse(
                            status=DomainResult.NEED_MORE_INFO,
                            message="Vui lòng cung cấp mã đơn hàng để xử lý yêu cầu hoàn tiền.",
                            missing_slots=["order_id"],
                            next_action="ASK_SLOT",
                            next_action_params={
                                "slot_name": "order_id",
                                "all_missing": ["order_id"]
                            }
                        )
                
                elif "feedback" in issue_type_lower or "đánh giá" in issue_type_lower or "review" in issue_type_lower:
                    if feedback:
                        message = f"Cảm ơn bạn đã phản hồi! Chúng tôi đã ghi nhận: '{feedback}'. Phản hồi của bạn rất quan trọng để chúng tôi cải thiện dịch vụ."
                    else:
                        return DomainResponse(
                            status=DomainResult.NEED_MORE_INFO,
                            message="Vui lòng chia sẻ phản hồi của bạn về sản phẩm/dịch vụ.",
                            missing_slots=["feedback"],
                            next_action="ASK_SLOT",
                            next_action_params={
                                "slot_name": "feedback",
                                "all_missing": ["feedback"]
                            }
                        )
                
                else:
                    message = (
                        "Chúng tôi đã ghi nhận yêu cầu hỗ trợ của bạn. "
                        "Đội ngũ chăm sóc khách hàng sẽ liên hệ với bạn sớm nhất có thể."
                    )
            else:
                # Generic post-purchase care
                message = (
                    "Chúng tôi có thể hỗ trợ bạn với:\n"
                    "- Trả hàng/Đổi hàng\n"
                    "- Hoàn tiền\n"
                    "- Phản hồi/Đánh giá\n"
                    "- Hỗ trợ kỹ thuật\n\n"
                    "Bạn cần hỗ trợ về vấn đề gì?"
                )
                return DomainResponse(
                    status=DomainResult.NEED_MORE_INFO,
                    message=message,
                    missing_slots=["issue_type"],
                    next_action="ASK_SLOT",
                    next_action_params={
                        "slot_name": "issue_type",
                        "all_missing": ["issue_type"]
                    }
                )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=message,
                data={
                    "post_purchase_care": {
                        "order_id": order_id,
                        "issue_type": issue_type,
                        "feedback": feedback,
                        "handled": True,
                    }
                },
                audit={
                    "intent": request.intent,
                    "order_id": order_id,
                    "issue_type": issue_type,
                    "has_feedback": bool(feedback),
                }
            )
            
        except Exception as e:
            logger.error(
                f"Post-purchase care use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại sau.",
                error_code="POST_PURCHASE_CARE_ERROR"
            )
