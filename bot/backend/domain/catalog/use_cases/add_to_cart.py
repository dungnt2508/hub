"""
Add to Cart Use Case
"""
from typing import Optional
from ....schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ....shared.logger import logger
from ....shared.exceptions import InvalidInputError


class AddToCartUseCase(CatalogUseCase):
    """
    Add product to shopping cart.
    
    Use case: User wants to add a product to their cart.
    Cart is stored in session state for persistence across turns.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize add to cart use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute add to cart.
        
        Args:
            request: Domain request with product_id and quantity in slots
            
        Returns:
            Domain response with cart status
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract required slots
            product_id = request.slots.get("product_id")
            quantity_str = request.slots.get("quantity", "1")
            
            # Validate product_id
            if not product_id:
                # Try to get from product_name
                product_name = request.slots.get("product_name") or request.slots.get("product")
                if product_name:
                    # Search for product by name
                    products = await self.repository.search(
                        tenant_id=tenant_id,
                        query=product_name,
                        limit=1
                    )
                    if products:
                        product_id = products[0].id
                    else:
                        return DomainResponse(
                            status=DomainResult.NEED_MORE_INFO,
                            message=f"Không tìm thấy sản phẩm '{product_name}'. Vui lòng cung cấp ID sản phẩm hoặc tên chính xác.",
                            next_action="ASK_SLOT",
                            next_action_params={
                                "slot_name": "product_id",
                                "all_missing": ["product_id"]
                            }
                        )
                else:
                    return DomainResponse(
                        status=DomainResult.NEED_MORE_INFO,
                        message="Vui lòng cho biết sản phẩm nào bạn muốn thêm vào giỏ hàng (tên hoặc ID sản phẩm).",
                        next_action="ASK_SLOT",
                        next_action_params={
                            "slot_name": "product_id",
                            "all_missing": ["product_id"]
                        }
                    )
            
            # Validate and parse quantity
            try:
                quantity = int(quantity_str) if isinstance(quantity_str, str) else int(quantity_str)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except (ValueError, TypeError):
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message="Số lượng không hợp lệ. Vui lòng nhập số nguyên dương.",
                    error_code="INVALID_QUANTITY"
                )
            
            logger.info(
                "Adding product to cart",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "product_id": product_id,
                    "quantity": quantity,
                }
            )
            
            # Verify product exists
            product = await self.repository.find_by_id(tenant_id, product_id)
            if not product:
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message=f"Sản phẩm với ID '{product_id}' không tồn tại.",
                    error_code="PRODUCT_NOT_FOUND"
                )
            
            # Check availability
            if product.stock_status == "out_of_stock" or (product.stock_quantity is not None and product.stock_quantity < quantity):
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message=f"Sản phẩm '{product.title}' hiện không còn đủ hàng.",
                    error_code="OUT_OF_STOCK"
                )
            
            # Get current cart from session (stored in slots_memory)
            cart = request.user_context.get("cart") or {}
            if not isinstance(cart, dict):
                cart = {}
            
            # Add or update item in cart
            cart_item_key = product_id
            if cart_item_key in cart:
                # Update quantity
                cart[cart_item_key]["quantity"] += quantity
            else:
                # Add new item
                cart[cart_item_key] = {
                    "product_id": product_id,
                    "product_name": product.title,
                    "quantity": quantity,
                    "price": product.price,
                    "currency": product.currency or "USD",
                }
            
            # Calculate total items and total price
            total_items = sum(item["quantity"] for item in cart.values())
            total_price = sum(
                item.get("price", 0) * item["quantity"] 
                for item in cart.values() 
                if item.get("price") is not None
            )
            
            # Generate response message
            if quantity == 1:
                message = f"Đã thêm '{product.title}' vào giỏ hàng."
            else:
                message = f"Đã thêm {quantity} sản phẩm '{product.title}' vào giỏ hàng."
            
            if total_items > quantity:
                message += f" Giỏ hàng của bạn hiện có {total_items} sản phẩm."
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=message,
                data={
                    "cart": cart,
                    "cart_summary": {
                        "total_items": total_items,
                        "total_price": total_price,
                        "currency": product.currency or "USD",
                    },
                    "added_product": {
                        "product_id": product_id,
                        "product_name": product.title,
                        "quantity": quantity,
                    }
                },
                audit={
                    "intent": request.intent,
                    "product_id": product_id,
                    "quantity": quantity,
                    "cart_total_items": total_items,
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid add to cart request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Add to cart use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi thêm sản phẩm vào giỏ hàng. Vui lòng thử lại sau.",
                error_code="ADD_TO_CART_ERROR"
            )
