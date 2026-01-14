"""
Get Product Info Use Case
"""
from typing import Optional
from ...schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ...shared.logger import logger


class GetProductInfoUseCase(CatalogUseCase):
    """
    Get detailed product information.
    
    Use case: User wants to know details about a specific product.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize get product info use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute get product info.
        
        Args:
            request: Domain request with product name/ID in slots
        
        Returns:
            Domain response with product information
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Try to get product_id or product_name from slots
            product_id = request.slots.get("product_id")
            product_name = request.slots.get("product_name") or request.slots.get("product")
            query = request.slots.get("query") or request.slots.get("question", "")
            
            logger.info(
                "Getting product info",
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
                    data={"product": None},
                    audit={
                        "intent": request.intent,
                        "product_found": False,
                    }
                )
            
            # Generate detailed answer
            answer = self._generate_answer(product)
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=answer,
                data={
                    "product": product.to_dict(),
                },
                audit={
                    "intent": request.intent,
                    "product_id": product.id,
                    "product_found": True,
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid get product info request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Get product info use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi lấy thông tin sản phẩm. Vui lòng thử lại sau.",
                error_code="GET_INFO_ERROR"
            )
    
    def _generate_answer(self, product: Product) -> str:
        """Generate detailed product information answer"""
        parts = [f"Thông tin về '{product.title}':"]
        
        # Description
        if product.description:
            parts.append(f"Mô tả: {product.description[:200]}...")
        
        # Price
        parts.append(f"Giá: {product.get_price_display()}")
        
        # Availability
        parts.append(f"Tình trạng: {product.get_availability_display()}")
        
        # Features
        if product.features:
            features_text = ", ".join(product.features[:5])
            parts.append(f"Tính năng: {features_text}")
        
        return " ".join(parts)

