"""
Place Order Use Case
"""
from typing import Optional, Dict, Any
from datetime import datetime
from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import CatalogUseCase
from ....shared.logger import logger
from ....shared.exceptions import InvalidInputError


class PlaceOrderUseCase(CatalogUseCase):
    """
    Place order with cart items and customer info.
    
    Use case: User wants to complete checkout and place order.
    Validates cart and customer info, then creates order.
    """
    
    def __init__(self, repository=None):
        """
        Initialize place order use case.
        
        Args:
            repository: Not used for this use case, but required by base class
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute place order.
        
        Args:
            request: Domain request with cart and customer info
            
        Returns:
            Domain response with order confirmation
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Get cart from user_context or slots
            cart = request.user_context.get("cart") or request.slots.get("cart") or {}
            if not isinstance(cart, dict) or not cart:
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message="Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi đặt hàng.",
                    error_code="EMPTY_CART"
                )
            
            # Get customer info from user_context or slots
            customer_info = request.user_context.get("customer_info") or request.slots.get("customer_info") or {}
            if not isinstance(customer_info, dict):
                customer_info = {}
            
            # Validate customer info
            required_fields = ["name", "email", "phone", "address"]
            missing_fields = [f for f in required_fields if not customer_info.get(f)]
            
            if missing_fields:
                field_names = {
                    "name": "tên",
                    "email": "email",
                    "phone": "số điện thoại",
                    "address": "địa chỉ giao hàng"
                }
                missing_list = [field_names.get(f, f) for f in missing_fields]
                return DomainResponse(
                    status=DomainResult.NEED_MORE_INFO,
                    message=f"Vui lòng cung cấp thông tin: {', '.join(missing_list)} trước khi đặt hàng.",
                    missing_slots=missing_fields,
                    next_action="ASK_SLOT",
                    next_action_params={
                        "slot_name": missing_fields[0],
                        "all_missing": missing_fields
                    },
                    data={
                        "missing_customer_info": missing_fields
                    }
                )
            
            # Calculate order total
            total_items = sum(item.get("quantity", 0) for item in cart.values())
            total_price = sum(
                item.get("price", 0) * item.get("quantity", 0)
                for item in cart.values()
                if item.get("price") is not None
            )
            
            # Get payment and shipping method
            payment_method = (
                request.slots.get("payment_method") or
                customer_info.get("payment_method") or
                "cash_on_delivery"  # Default
            )
            shipping_method = request.slots.get("shipping_method") or "standard"
            
            logger.info(
                "Placing order",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "total_items": total_items,
                    "total_price": total_price,
                    "customer_email": customer_info.get("email"),
                }
            )
            
            # Generate order ID (in real implementation, this would come from order service)
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{request.trace_id[:8].upper()}"
            order_number = order_id
            
            # Create order data structure
            order_data = {
                "order_id": order_id,
                "order_number": order_number,
                "customer_info": customer_info,
                "cart": cart,
                "order_summary": {
                    "total_items": total_items,
                    "total_price": total_price,
                    "currency": "USD",  # Default, should come from cart
                    "payment_method": payment_method,
                    "shipping_method": shipping_method,
                },
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            
            # In real implementation, this would call order service API
            # For now, we just return success with order data
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=f"Đơn hàng của bạn đã được đặt thành công! Mã đơn hàng: {order_number}. Chúng tôi sẽ liên hệ với bạn qua email {customer_info['email']} để xác nhận đơn hàng.",
                data={
                    "order": order_data,
                    "order_id": order_id,
                    "order_number": order_number,
                },
                audit={
                    "intent": request.intent,
                    "order_id": order_id,
                    "total_items": total_items,
                    "total_price": total_price,
                    "customer_email": customer_info.get("email"),
                }
            )
            
        except Exception as e:
            logger.error(
                f"Place order use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi đặt hàng. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.",
                error_code="PLACE_ORDER_ERROR"
            )
