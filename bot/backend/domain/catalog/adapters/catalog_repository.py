"""
Catalog Repository Adapter - Implements ICatalogRepository
"""
from typing import List, Optional
from ..ports.repository import ICatalogRepository
from ..entities.product import Product
from ..value_objects.price import Price
from ..value_objects.availability import Availability
from ...infrastructure.catalog_client import CatalogClient, CatalogProduct
from ...infrastructure.vector_store import get_vector_store
from ...knowledge.catalog_retriever import CatalogRetriever, RetrievedProduct
from ...shared.logger import logger
from ...shared.exceptions import ExternalServiceError


class CatalogRepositoryAdapter(ICatalogRepository):
    """
    Repository adapter - implements ICatalogRepository.
    
    This adapter bridges domain layer with infrastructure layer:
    - Uses CatalogClient to fetch products from catalog service
    - Uses VectorStore for semantic search
    - Converts infrastructure models to domain entities
    """
    
    def __init__(
        self,
        catalog_client: Optional[CatalogClient] = None,
        retriever: Optional[CatalogRetriever] = None,
    ):
        """
        Initialize repository adapter.
        
        Args:
            catalog_client: Optional CatalogClient instance
            retriever: Optional CatalogRetriever instance
        """
        self.catalog_client = catalog_client or CatalogClient()
        self.retriever = retriever or CatalogRetriever()
        logger.info("CatalogRepositoryAdapter initialized")
    
    async def find_by_id(self, tenant_id: str, product_id: str) -> Optional[Product]:
        """Find product by ID from catalog service"""
        try:
            # Fetch product from catalog service
            product_data = await self.catalog_client.get_product(product_id)
            if not product_data:
                return None
            
            return self._to_entity(product_data)
            
        except Exception as e:
            logger.error(
                f"Failed to find product by ID: {e}",
                extra={"tenant_id": tenant_id, "product_id": product_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Failed to fetch product: {e}") from e
    
    async def search(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[Product]:
        """Search products using vector search"""
        try:
            # Use retriever for semantic search
            retrieved_products = await self.retriever.retrieve(
                tenant_id=tenant_id,
                query=query,
                top_k=limit
            )
            
            # Convert to entities
            products = []
            for retrieved in retrieved_products:
                try:
                    # Fetch full product data
                    product_data = await self.catalog_client.get_product(retrieved.product_id)
                    if product_data:
                        product = self._to_entity(product_data)
                        products.append(product)
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch product {retrieved.product_id}: {e}",
                        extra={"tenant_id": tenant_id}
                    )
                    continue
            
            # Apply filters if provided
            if filters:
                products = self._apply_filters(products, filters)
            
            return products[:limit]
            
        except Exception as e:
            logger.error(
                f"Failed to search products: {e}",
                extra={"tenant_id": tenant_id, "query": query[:100]},
                exc_info=True
            )
            raise ExternalServiceError(f"Failed to search products: {e}") from e
    
    async def find_by_attribute(
        self,
        tenant_id: str,
        attribute: str,
        value: Optional[str] = None,
        limit: int = 10
    ) -> List[Product]:
        """
        Find products by specific attribute.
        
        This method uses search and filters by attribute.
        For direct DB queries, use catalog service API if available.
        """
        try:
            # Use search and filter by attribute
            # This is safer than direct DB queries and works with catalog service
            products = await self.search(tenant_id, attribute, limit=limit * 2)
            
            # Filter by attribute
            filtered = []
            for product in products:
                if self._matches_attribute(product, attribute, value):
                    filtered.append(product)
                    if len(filtered) >= limit:
                        break
            
            return filtered
            
        except Exception as e:
            logger.error(
                f"Failed to find products by attribute: {e}",
                extra={"tenant_id": tenant_id, "attribute": attribute},
                exc_info=True
            )
            raise ExternalServiceError(f"Failed to find products by attribute: {e}") from e
    
    async def find_by_ids(
        self,
        tenant_id: str,
        product_ids: List[str]
    ) -> List[Product]:
        """Find multiple products by IDs"""
        products = []
        
        for product_id in product_ids:
            try:
                product = await self.find_by_id(tenant_id, product_id)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch product {product_id}: {e}",
                    extra={"tenant_id": tenant_id}
                )
                continue
        
        return products
    
    async def count(
        self,
        tenant_id: str,
        filters: Optional[dict] = None
    ) -> int:
        """Count products with optional filters"""
        try:
            # For now, use search with large limit and count results
            # TODO: Implement direct count query when catalog service supports it
            products = await self.search(tenant_id, "", limit=1000)
            
            if filters:
                products = self._apply_filters(products, filters)
            
            return len(products)
            
        except Exception as e:
            logger.error(
                f"Failed to count products: {e}",
                extra={"tenant_id": tenant_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Failed to count products: {e}") from e
    
    def _to_entity(self, data: CatalogProduct) -> Product:
        """Convert CatalogProduct to Product entity"""
        # Create Price value object
        price = None
        if data.price is not None:
            try:
                price = Price(
                    amount=float(data.price),
                    currency=data.metadata.get("currency", "VND") if data.metadata else "VND",
                    price_type=data.metadata.get("price_type", "onetime") if data.metadata else "onetime"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to create Price from data: {e}")
                price = None
        
        # Create Availability value object
        availability = Availability(
            in_stock=data.status == "published",
            quantity=None,  # Not available in catalog service
            status=data.status or "published"
        )
        
        # Create Product entity
        return Product(
            id=data.id,
            title=data.title,
            description=data.description or "",
            price=price,
            availability=availability,
            features=data.features or [],
            tags=data.tags or [],
            metadata=data.metadata or {}
        )
    
    def _apply_filters(self, products: List[Product], filters: dict) -> List[Product]:
        """Apply filters to products"""
        filtered = products
        
        if "is_free" in filters:
            is_free = filters["is_free"]
            filtered = [p for p in filtered if p.is_free() == is_free]
        
        if "status" in filters:
            status = filters["status"]
            filtered = [p for p in filtered if p.availability and p.availability.status == status]
        
        if "available" in filters:
            available = filters["available"]
            filtered = [p for p in filtered if p.is_available() == available]
        
        return filtered
    
    def _matches_attribute(self, product: Product, attribute: str, value: Optional[str] = None) -> bool:
        """Check if product matches attribute"""
        attribute_lower = attribute.lower()
        
        if attribute_lower in ["price", "cost", "fee"]:
            return product.price is not None
        
        elif attribute_lower in ["free", "miễn phí"]:
            return product.is_free()
        
        elif attribute_lower in ["feature", "features"]:
            if value:
                return product.has_feature(value)
            return len(product.features) > 0
        
        elif attribute_lower in ["tag", "tags"]:
            if value:
                return product.has_tag(value)
            return len(product.tags) > 0
        
        elif attribute_lower in ["available", "availability"]:
            return product.is_available()
        
        return False

