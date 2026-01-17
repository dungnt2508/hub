"""Product service - handles product queries"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.catalog import Product, ProductAttribute
from backend.errors.domain_errors import DataNotFoundError


class ProductService:
    """Service for product queries"""
    
    def __init__(self, session: AsyncSession):
        self.catalog_repo = CatalogRepository(session)
    
    async def get_product_info(
        self,
        tenant_id: UUID,
        product_id: Optional[UUID] = None,
        sku: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get product information.
        ONLY from products + product_attributes tables.
        No reasoning, no guessing.
        
        Raises:
            DataNotFoundError: If product not found
        """
        # Get product
        product: Optional[Product] = None
        if product_id:
            product = await self.catalog_repo.get_product(product_id, tenant_id)
        elif sku:
            product = await self.catalog_repo.get_product_by_sku(sku, tenant_id)
        elif slug:
            products = await self.catalog_repo.search_products(
                tenant_id=tenant_id,
                query=slug,
                limit=1
            )
            product = products[0] if products else None
        
        if not product:
            raise DataNotFoundError("Product not found")
        
        # Get attributes
        attributes = await self.catalog_repo.get_product_attributes(
            product.id,
            tenant_id
        )
        
        # Build response - ONLY from database
        return {
            "product": {
                "id": str(product.id),
                "sku": product.sku,
                "slug": product.slug,
                "name": product.name,
                "category": product.category,
                "status": product.status,
            },
            "attributes": [
                {
                    "key": attr.attributes_key,
                    "value": attr.attributes_value,
                    "type": attr.attributes_value_type,
                }
                for attr in attributes
            ]
        }
    
    async def get_price(
        self,
        tenant_id: UUID,
        product_id: Optional[UUID] = None,
        sku: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get product price"""
        try:
            product_info = await self.get_product_info(
                tenant_id=tenant_id,
                product_id=product_id,
                sku=sku
            )
            
            # Find price attribute
            price_attr = next(
                (a for a in product_info["attributes"] 
                 if "price" in a["key"].lower() or "giá" in a["key"].lower()),
                None
            )
            
            if price_attr:
                return {
                    "type": "product_price",
                    "product": product_info["product"],
                    "price": price_attr["value"]
                }
            
            return None
        except DataNotFoundError:
            return None
