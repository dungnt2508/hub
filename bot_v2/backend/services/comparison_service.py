"""Comparison service - handles product comparison"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.catalog import Comparison, Product
from backend.errors.domain_errors import DataNotFoundError


class ComparisonService:
    """Service for product comparison"""
    
    def __init__(self, session: AsyncSession):
        self.catalog_repo = CatalogRepository(session)
    
    async def compare_products(
        self,
        tenant_id: UUID,
        product_a_id: UUID,
        product_b_id: UUID
    ) -> Dict[str, Any]:
        """
        Compare two products.
        ONLY if explicitly defined in comparisons table.
        
        Raises:
            DataNotFoundError: If comparison not allowed or products not found
        """
        # Check if comparison is allowed
        comparison = await self.catalog_repo.get_comparison(
            product_a_id,
            product_b_id,
            tenant_id
        )
        
        if not comparison:
            raise DataNotFoundError("Comparison not allowed for these products")
        
        # Get both products
        product_a = await self.catalog_repo.get_product(product_a_id, tenant_id)
        product_b = await self.catalog_repo.get_product(product_b_id, tenant_id)
        
        if not product_a or not product_b:
            raise DataNotFoundError("One or both products not found")
        
        # Get attributes for both products
        attrs_a = await self.catalog_repo.get_product_attributes(product_a_id, tenant_id)
        attrs_b = await self.catalog_repo.get_product_attributes(product_b_id, tenant_id)
        
        # Filter by allowed_attributes if specified
        allowed_keys = comparison.allowed_attributes or []
        
        if allowed_keys:
            attrs_a = [a for a in attrs_a if a.attributes_key in allowed_keys]
            attrs_b = [a for a in attrs_b if a.attributes_key in allowed_keys]
        
        # Build comparison
        comparison_data = {}
        all_keys = set(a.attributes_key for a in attrs_a) | set(a.attributes_key for a in attrs_b)
        
        for key in all_keys:
            attr_a = next((a for a in attrs_a if a.attributes_key == key), None)
            attr_b = next((a for a in attrs_b if a.attributes_key == key), None)
            
            comparison_data[key] = {
                "product_a": attr_a.attributes_value if attr_a else None,
                "product_b": attr_b.attributes_value if attr_b else None,
            }
        
        return {
            "product_a": {
                "id": str(product_a.id),
                "name": product_a.name,
                "sku": product_a.sku,
            },
            "product_b": {
                "id": str(product_b.id),
                "name": product_b.name,
                "sku": product_b.sku,
            },
            "comparison": comparison_data,
            "allowed_attributes": comparison.allowed_attributes
        }
