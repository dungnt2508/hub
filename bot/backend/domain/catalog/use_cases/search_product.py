"""
Search Product Use Case
"""
from typing import List
from ...schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ...shared.logger import logger


class SearchProductUseCase(CatalogUseCase):
    """
    Search products by query.
    
    Use case: User wants to find products matching a search query.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize search product use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute product search.
        
        Args:
            request: Domain request with query in slots
        
        Returns:
            Domain response with search results
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            query = self._extract_query(request)
            
            logger.info(
                "Searching products",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "query": query[:100],
                }
            )
            
            # Search products
            products = await self.repository.search(
                tenant_id=tenant_id,
                query=query,
                limit=10
            )
            
            if not products:
                return DomainResponse(
                    status=DomainResult.SUCCESS,
                    message="Tôi không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn.",
                    data={
                        "products": [],
                        "count": 0,
                    },
                    audit={
                        "intent": request.intent,
                        "query": query,
                        "products_found": 0,
                    }
                )
            
            # Format response
            products_data = [self._format_product(p) for p in products]
            
            # Generate answer
            answer = self._generate_answer(products, query)
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=answer,
                data={
                    "products": products_data,
                    "count": len(products),
                },
                audit={
                    "intent": request.intent,
                    "query": query,
                    "products_found": len(products),
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid search request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Search product use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi tìm kiếm sản phẩm. Vui lòng thử lại sau.",
                error_code="SEARCH_ERROR"
            )
    
    def _format_product(self, product: Product) -> dict:
        """Format product for response"""
        return product.to_dict()
    
    def _generate_answer(self, products: List[Product], query: str) -> str:
        """Generate human-readable answer"""
        count = len(products)
        
        if count == 1:
            product = products[0]
            return f"Tìm thấy sản phẩm '{product.title}'. {product.description[:100]}..."
        elif count <= 3:
            product_names = [p.title for p in products]
            return f"Tìm thấy {count} sản phẩm: {', '.join(product_names)}"
        else:
            top_products = products[:3]
            product_names = [p.title for p in top_products]
            return f"Tìm thấy {count} sản phẩm. Một số sản phẩm phù hợp: {', '.join(product_names)}..."

