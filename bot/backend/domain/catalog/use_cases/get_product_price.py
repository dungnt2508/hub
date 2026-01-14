"""
Get Product Price Use Case
"""
from typing import Optional
from ...schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ...shared.logger import logger


class GetProductPriceUseCase(CatalogUseCase):
    """
    Get product price information.
    
    Use case: User wants to know the price of a product.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize get product price use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute get product price.
        
        Args:
            request: Domain request with product name/ID in slots
        
        Returns:
            Domain response with price information
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract product identifier
            product_id = request.slots.get("product_id")
            product_name = request.slots.get("product_name") or request.slots.get("product")
            query = request.slots.get("query") or request.slots.get("question", "")
            
            logger.info(
                "Getting product price",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "product_id": product_id,
                    "product_name": product_name,
                }
            )
            
            product: Optional[Product] = None
            
            # Try to find by ID first
            if product_id:
                product = await self.repository.find_by_id(tenant_id, product_id)
            
            # If not found, try to search by name
            if not product and product_name:
                products = await self.repository.search(
                    tenant_id=tenant_id,
                    query=product_name,
                    limit=1
                )
                if products:
                    product = products[0]
            
            # If still not found, try to extract from query
            if not product and query:
                products = await self.repository.search(
                    tenant_id=tenant_id,
                    query=query,
                    limit=1
                )
                if products:
                    product = products[0]
            
            if not product:
                return DomainResponse(
                    status=DomainResult.SUCCESS,
                    message="Tôi không tìm thấy thông tin về sản phẩm này trong catalog.",
                    data={"price": None},
                    audit={
                        "intent": request.intent,
                        "product_found": False,
                    }
                )
            
            # Generate price answer
            answer = self._generate_answer(product)
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=answer,
                data={
                    "product_id": product.id,
                    "product_title": product.title,
                    "price": product.price.amount if product.price else None,
                    "price_display": product.get_price_display(),
                    "currency": product.price.currency if product.price else None,
                    "price_type": product.price.price_type if product.price else "free",
                    "is_free": product.is_free(),
                },
                audit={
                    "intent": request.intent,
                    "product_id": product.id,
                    "is_free": product.is_free(),
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid get product price request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Get product price use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi lấy thông tin giá sản phẩm. Vui lòng thử lại sau.",
                error_code="PRICE_ERROR"
            )
    
    def _generate_answer(self, product: Product) -> str:
        """Generate price answer"""
        if product.is_free():
            return f"Sản phẩm '{product.title}' là miễn phí."
        else:
            return f"Giá của '{product.title}' là {product.get_price_display()}."

