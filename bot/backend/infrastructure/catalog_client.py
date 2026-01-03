"""
Catalog API Client - Fetch products from catalog service
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..shared.config import config
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


@dataclass
class CatalogProduct:
    """Catalog product data structure"""
    id: str
    seller_id: str
    title: str
    description: str
    long_description: Optional[str] = None
    type: str = "workflow"
    tags: List[str] = None
    features: List[str] = None
    requirements: List[str] = None
    is_free: bool = True
    price: Optional[float] = None
    status: str = "published"
    review_status: str = "approved"
    downloads: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    version: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.tags is None:
            self.tags = []
        if self.features is None:
            self.features = []
        if self.requirements is None:
            self.requirements = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProductsResponse:
    """Products API response"""
    products: List[CatalogProduct]
    total: int
    limit: int
    offset: int


class CatalogClient:
    """
    Client for catalog service API.
    
    Fetches products from catalog service with pagination support.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize catalog client.
        
        Args:
            base_url: Catalog service base URL (defaults to config)
            api_key: API key for authentication (optional)
        """
        self.base_url = base_url or config.CATALOG_API_URL
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        
        if not self.base_url:
            raise ValueError("CATALOG_API_URL must be set in config")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with retry"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, ExternalServiceError)),
    )
    async def get_products(
        self,
        status: str = "published",
        review_status: str = "approved",
        limit: int = 100,
        offset: int = 0,
        **kwargs
    ) -> ProductsResponse:
        """
        Fetch products from catalog API.
        
        Args:
            status: Product status filter (default: "published")
            review_status: Review status filter (default: "approved")
            limit: Number of products per page (default: 100)
            offset: Pagination offset (default: 0)
            **kwargs: Additional query parameters (tags, type, search, etc.)
        
        Returns:
            ProductsResponse with products list and pagination info
        
        Raises:
            ExternalServiceError: If API request fails
        """
        client = await self._get_client()
        
        # Build query parameters
        params = {
            "status": status,
            "review_status": review_status,
            "limit": limit,
            "offset": offset,
        }
        
        # Add additional filters
        params.update(kwargs)
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        url = f"{self.base_url}/api/products"
        
        try:
            logger.debug(
                f"Fetching products from catalog API",
                extra={"url": url, "params": params}
            )
            
            response = await client.get(
                url,
                params=params,
                headers=self._build_headers(),
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            if not data.get("success", True):
                error_msg = data.get("error", "Unknown error")
                raise ExternalServiceError(f"Catalog API error: {error_msg}")
            
            # Extract products data
            response_data = data.get("data", data)
            products_data = response_data.get("products", [])
            
            # Convert to CatalogProduct objects
            products = []
            for product_data in products_data:
                try:
                    product = CatalogProduct(
                        id=product_data.get("id", ""),
                        seller_id=product_data.get("sellerId", ""),
                        title=product_data.get("title", ""),
                        description=product_data.get("description", ""),
                        long_description=product_data.get("longDescription"),
                        type=product_data.get("type", "workflow"),
                        tags=product_data.get("tags", []),
                        features=product_data.get("features", []),
                        requirements=product_data.get("requirements", []),
                        is_free=product_data.get("isFree", True),
                        price=product_data.get("price"),
                        status=product_data.get("status", "published"),
                        review_status=product_data.get("reviewStatus", "approved"),
                        downloads=product_data.get("downloads", 0),
                        rating=product_data.get("rating", 0.0),
                        reviews_count=product_data.get("reviewsCount", 0),
                        version=product_data.get("version"),
                        metadata=product_data.get("metadata", {}),
                        created_at=product_data.get("createdAt"),
                        updated_at=product_data.get("updatedAt"),
                    )
                    products.append(product)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse product: {e}",
                        extra={"product_data": product_data}
                    )
                    continue
            
            return ProductsResponse(
                products=products,
                total=response_data.get("total", len(products)),
                limit=response_data.get("limit", limit),
                offset=response_data.get("offset", offset),
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Catalog API HTTP error: {e.response.status_code}",
                extra={"url": url, "status_code": e.response.status_code}
            )
            raise ExternalServiceError(
                f"Catalog API HTTP error: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(
                f"Catalog API request error: {e}",
                extra={"url": url}
            )
            raise ExternalServiceError(f"Catalog API request failed: {e}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error fetching products: {e}",
                exc_info=True,
                extra={"url": url}
            )
            raise ExternalServiceError(f"Failed to fetch products: {e}") from e
    
    async def get_all_products(
        self,
        status: str = "published",
        review_status: str = "approved",
        batch_size: int = 100,
        **kwargs
    ) -> List[CatalogProduct]:
        """
        Fetch all products with automatic pagination.
        
        Args:
            status: Product status filter
            review_status: Review status filter
            batch_size: Number of products per batch
            **kwargs: Additional query parameters
        
        Returns:
            List of all products
        """
        all_products = []
        offset = 0
        
        while True:
            response = await self.get_products(
                status=status,
                review_status=review_status,
                limit=batch_size,
                offset=offset,
                **kwargs
            )
            
            all_products.extend(response.products)
            
            # Check if we've fetched all products
            if offset + len(response.products) >= response.total:
                break
            
            offset += batch_size
        
        logger.info(
            f"Fetched {len(all_products)} products from catalog",
            extra={"total": len(all_products)}
        )
        
        return all_products
    
    async def get_product(self, product_id: str) -> Optional[CatalogProduct]:
        """
        Fetch single product by ID.
        
        Args:
            product_id: Product UUID
        
        Returns:
            CatalogProduct or None if not found
        """
        client = await self._get_client()
        url = f"{self.base_url}/api/products/{product_id}"
        
        try:
            response = await client.get(
                url,
                headers=self._build_headers(),
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            response_data = data.get("data", data)
            product_data = response_data if isinstance(response_data, dict) else response_data.get("product", {})
            
            return CatalogProduct(
                id=product_data.get("id", ""),
                seller_id=product_data.get("sellerId", ""),
                title=product_data.get("title", ""),
                description=product_data.get("description", ""),
                long_description=product_data.get("longDescription"),
                type=product_data.get("type", "workflow"),
                tags=product_data.get("tags", []),
                features=product_data.get("features", []),
                requirements=product_data.get("requirements", []),
                is_free=product_data.get("isFree", True),
                price=product_data.get("price"),
                status=product_data.get("status", "published"),
                review_status=product_data.get("reviewStatus", "approved"),
                downloads=product_data.get("downloads", 0),
                rating=product_data.get("rating", 0.0),
                reviews_count=product_data.get("reviewsCount", 0),
                version=product_data.get("version"),
                metadata=product_data.get("metadata", {}),
                created_at=product_data.get("createdAt"),
                updated_at=product_data.get("updatedAt"),
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(
                f"Failed to fetch product {product_id}: {e.response.status_code}",
                extra={"product_id": product_id}
            )
            raise ExternalServiceError(
                f"Failed to fetch product: {e.response.status_code}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error fetching product {product_id}: {e}",
                exc_info=True,
                extra={"product_id": product_id}
            )
            raise ExternalServiceError(f"Failed to fetch product: {e}") from e

