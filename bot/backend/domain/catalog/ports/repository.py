"""
Catalog Repository Interface (Port)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.product import Product


class ICatalogRepository(ABC):
    """
    Catalog repository interface (port).
    
    This defines the contract for product data access.
    Implementations should be in adapters/ layer.
    
    Following Clean Architecture:
    - Domain layer defines interface (port)
    - Infrastructure layer implements interface (adapter)
    """
    
    @abstractmethod
    async def find_by_id(self, tenant_id: str, product_id: str) -> Optional[Product]:
        """
        Find product by ID.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product ID
        
        Returns:
            Product entity or None if not found
        
        Raises:
            ExternalServiceError: If repository access fails
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[Product]:
        """
        Search products by query.
        
        Args:
            tenant_id: Tenant UUID
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters (e.g., {"is_free": True, "status": "published"})
        
        Returns:
            List of Product entities matching query
        
        Raises:
            ExternalServiceError: If repository access fails
        """
        pass
    
    @abstractmethod
    async def find_by_attribute(
        self,
        tenant_id: str,
        attribute: str,
        value: Optional[str] = None,
        limit: int = 10
    ) -> List[Product]:
        """
        Find products by specific attribute.
        
        Args:
            tenant_id: Tenant UUID
            attribute: Attribute name (e.g., "price", "feature", "tag")
            value: Optional value to match
            limit: Maximum number of results
        
        Returns:
            List of Product entities matching attribute
        
        Raises:
            ExternalServiceError: If repository access fails
        """
        pass
    
    @abstractmethod
    async def find_by_ids(
        self,
        tenant_id: str,
        product_ids: List[str]
    ) -> List[Product]:
        """
        Find multiple products by IDs.
        
        Args:
            tenant_id: Tenant UUID
            product_ids: List of product IDs
        
        Returns:
            List of Product entities (may be shorter than input if some not found)
        
        Raises:
            ExternalServiceError: If repository access fails
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        tenant_id: str,
        filters: Optional[dict] = None
    ) -> int:
        """
        Count products with optional filters.
        
        Args:
            tenant_id: Tenant UUID
            filters: Optional filters (e.g., {"is_free": True, "status": "published"})
        
        Returns:
            Count of products matching filters
        
        Raises:
            ExternalServiceError: If repository access fails
        """
        pass

