"""
Check Availability Use Case
"""
from typing import Optional
from ....schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class CheckAvailabilityUseCase(CatalogUseCase):
    """
    Check product availability.
    
    Use case: User wants to know if a product is available/in stock.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize check availability use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute availability check.
        
        Args:
            request: Domain request with product name/ID in slots
        
        Returns:
            Domain response with availability information
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract product identifier
            product_id = request.slots.get("product_id")
            product_name = request.slots.get("product_name") or request.slots.get("product")
            query = request.slots.get("query") or request.slots.get("question", "")
            
            logger.info(
                "Checking product availability",
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
                    data={"available": False},
                    audit={
                        "intent": request.intent,
                        "product_found": False,
                    }
                )
            
            if product.is_available() is None:
                return DomainResponse(
                    status=DomainResult.SUCCESS,
                    message=f"Sản phẩm '{product.title}' chưa có dữ liệu tồn kho.",
                    data={
                        "product_id": product.id,
                        "product_title": product.title,
                        "available": None,
                        "availability": product.get_availability_display(),
                        "availability_status": product.availability.listing_status if product.availability else None,
                        "stock_status": product.availability.stock_status if product.availability else None,
                        "stock_quantity": product.availability.quantity if product.availability else None,
                        "missing_fields": ["stock_status"],
                    },
                    audit={
                        "intent": request.intent,
                        "product_id": product.id,
                        "missing_fields": ["stock_status"],
                    }
                )
            
            # Generate availability answer
            answer = self._generate_answer(product)
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=answer,
                data={
                    "product_id": product.id,
                    "product_title": product.title,
                    "available": product.is_available(),
                    "availability": product.get_availability_display(),
                    "availability_status": product.availability.listing_status if product.availability else None,
                    "stock_status": product.availability.stock_status if product.availability else None,
                    "stock_quantity": product.availability.quantity if product.availability else None,
                },
                audit={
                    "intent": request.intent,
                    "product_id": product.id,
                    "available": product.is_available(),
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid check availability request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Check availability use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi kiểm tra tình trạng sản phẩm. Vui lòng thử lại sau.",
                error_code="AVAILABILITY_ERROR"
            )
    
    def _generate_answer(self, product: Product) -> str:
        """Generate availability answer"""
        if product.is_available() is True:
            return f"Sản phẩm '{product.title}' {product.get_availability_display()}."
        if product.is_available() is False:
            return f"Sản phẩm '{product.title}' {product.get_availability_display()}."
        return f"Sản phẩm '{product.title}' chưa có dữ liệu tồn kho."

