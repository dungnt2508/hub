"""
Track Order Use Case
"""
from typing import Optional, Dict, Any
from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class TrackOrderUseCase(CatalogUseCase):
    """
    Track order status.
    
    Use case: User wants to check status of their order.
    """
    
    def __init__(self, repository=None):
        """
        Initialize track order use case.
        
        Args:
            repository: Not used for this use case, but required by base class
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute track order.
        
        Args:
            request: Domain request with order_id or order_number in slots
            
        Returns:
            Domain response with order status
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract order identifier
            order_id = request.slots.get("order_id") or request.slots.get("order_number")
            
            if not order_id:
                return DomainResponse(
                    status=DomainResult.NEED_MORE_INFO,
                    message="Vui lòng cung cấp mã đơn hàng để tra cứu.",
                    missing_slots=["order_id"],
                    next_action="ASK_SLOT",
                    next_action_params={
                        "slot_name": "order_id",
                        "all_missing": ["order_id"]
                    }
                )
            
            logger.info(
                "Tracking order",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "order_id": order_id,
                }
            )
            
            # In real implementation, this would call order service API
            # For now, return mock order status
            
            # Mock order statuses
            order_statuses = {
                "pending": "Đang chờ xử lý",
                "confirmed": "Đã xác nhận",
                "processing": "Đang xử lý",
                "shipped": "Đã giao hàng",
                "delivered": "Đã nhận hàng",
                "cancelled": "Đã hủy",
            }
            
            # Mock order data (in real implementation, fetch from order service)
            order_status = "processing"  # Default mock status
            order_data = {
                "order_id": order_id,
                "order_number": order_id,
                "status": order_status,
                "status_display": order_statuses.get(order_status, order_status),
                "estimated_delivery": None,  # Would come from order service
                "tracking_number": None,  # Would come from order service
                "items": [],  # Would come from order service
                "total_price": 0,  # Would come from order service
            }
            
            message = f"Đơn hàng {order_id} đang ở trạng thái: {order_data['status_display']}."
            
            if order_status == "shipped" and order_data.get("tracking_number"):
                message += f"\nMã vận đơn: {order_data['tracking_number']}"
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=message,
                data={
                    "order": order_data,
                    "order_id": order_id,
                    "status": order_status,
                },
                audit={
                    "intent": request.intent,
                    "order_id": order_id,
                    "order_status": order_status,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Track order use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi tra cứu đơn hàng. Vui lòng thử lại sau.",
                error_code="TRACK_ORDER_ERROR"
            )
