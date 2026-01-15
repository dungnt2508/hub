"""
Compare Products Use Case
"""
from typing import List
from ....schemas import DomainRequest, DomainResponse, DomainResult
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class CompareProductsUseCase(CatalogUseCase):
    """
    Compare multiple products.
    
    Use case: User wants to compare features/prices of multiple products.
    """
    
    def __init__(self, repository: ICatalogRepository):
        """
        Initialize compare products use case.
        
        Args:
            repository: Catalog repository
        """
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute product comparison.
        
        Args:
            request: Domain request with product names/IDs in slots
        
        Returns:
            Domain response with comparison results
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract product names/IDs from slots
            product_names = request.slots.get("product_names", [])
            product_ids = request.slots.get("product_ids", [])
            query = request.slots.get("query") or request.slots.get("question", "")
            
            logger.info(
                "Comparing products",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "product_names": product_names,
                    "product_ids": product_ids,
                }
            )
            
            products: List[Product] = []
            
            # Find products by IDs first
            if product_ids:
                found_products = await self.repository.find_by_ids(tenant_id, product_ids)
                products.extend(found_products)
            
            # Find products by names
            if product_names:
                for name in product_names:
                    found_products = await self.repository.search(
                        tenant_id=tenant_id,
                        query=name,
                        limit=1
                    )
                    if found_products:
                        # Avoid duplicates
                        if not any(p.id == found_products[0].id for p in products):
                            products.append(found_products[0])
            
            # If no products found and have query, try to extract from query
            if not products and query:
                # Try to find products mentioned in query
                found_products = await self.repository.search(
                    tenant_id=tenant_id,
                    query=query,
                    limit=5
                )
                products.extend(found_products[:2])  # Limit to 2 for comparison
            
            if len(products) < 2:
                return DomainResponse(
                    status=DomainResult.NEED_MORE_INFO,
                    message="Để so sánh sản phẩm, vui lòng cung cấp ít nhất 2 tên sản phẩm.",
                    error_code="INSUFFICIENT_PRODUCTS",
                    missing_slots=["product_names"]
                )
            
            # Limit to 3 products for comparison
            products = products[:3]
            
            # Generate comparison answer
            answer = self._generate_comparison(products)
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=answer,
                data={
                    "products": [p.to_dict() for p in products],
                    "comparison": self._format_comparison(products),
                },
                audit={
                    "intent": request.intent,
                    "products_compared": len(products),
                }
            )
            
        except ValueError as e:
            logger.warning(
                f"Invalid compare products request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT"
            )
        except Exception as e:
            logger.error(
                f"Compare products use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi so sánh sản phẩm. Vui lòng thử lại sau.",
                error_code="COMPARE_ERROR"
            )
    
    def _generate_comparison(self, products: List[Product]) -> str:
        """Generate comparison answer"""
        if len(products) == 2:
            p1, p2 = products
            parts = [f"So sánh '{p1.title}' và '{p2.title}':"]
            
            # Price comparison
            if p1.price and p2.price and p1.price.is_known() and p2.price.is_known():
                if p1.price.is_free() and p2.price.is_free():
                    parts.append("Cả hai đều miễn phí")
                elif p1.price.amount is not None and p2.price.amount is not None:
                    if p1.price.amount < p2.price.amount:
                        parts.append(f"'{p1.title}' rẻ hơn ({p1.get_price_display()} vs {p2.get_price_display()})")
                    elif p1.price.amount > p2.price.amount:
                        parts.append(f"'{p2.title}' rẻ hơn ({p2.get_price_display()} vs {p1.get_price_display()})")
                    else:
                        parts.append(f"Cả hai có cùng giá: {p1.get_price_display()}")
            else:
                parts.append("Không đủ dữ liệu giá để so sánh")
            
            # Availability
            parts.append(f"'{p1.title}': {p1.get_availability_display()}")
            parts.append(f"'{p2.title}': {p2.get_availability_display()}")
            
            return " ".join(parts)
        else:
            # Multiple products
            product_names = [p.title for p in products]
            return f"So sánh {len(products)} sản phẩm: {', '.join(product_names)}"
    
    def _format_comparison(self, products: List[Product]) -> dict:
        """Format comparison data"""
        return {
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "price": p.get_price_display(),
                    "is_free": p.is_free(),
                    "is_available": p.is_available(),
                    "features": p.features,
                }
                for p in products
            ]
        }

