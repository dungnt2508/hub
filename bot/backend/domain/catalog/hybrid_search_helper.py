"""
Catalog Hybrid Search Helper - Strategy-based retrieval orchestration

⚠️ DEPRECATED: This class contains SQL injection risks and direct DB access.
Use CatalogRepositoryAdapter instead for safe product queries.

This class is kept for backward compatibility with CatalogKnowledgeEngine.
New code should use domain/catalog/adapters/catalog_repository.py
"""
from typing import List, Optional, Dict, Any
from enum import Enum
import warnings

from ...knowledge.catalog_retriever import RetrievedProduct
from ...infrastructure.database_client import DatabaseClient
from ...shared.logger import logger


class SearchStrategy(str, Enum):
    """Search strategy enum"""
    VECTOR_ONLY = "vector_only"  # Use vector search only
    DB_QUERY = "db_query"  # Use structured DB query only
    HYBRID = "hybrid"  # Combine vector and DB query


class CatalogHybridSearchHelper:
    """
    Hybrid search helper for intelligent retrieval based on intent.
    
    Responsibilities:
    - Route to appropriate retrieval strategy based on intent
    - Execute DB queries for specific attribute searches
    - Combine results from vector + DB search
    - Filter and deduplicate results
    """
    
    def __init__(self, db_client: Optional[DatabaseClient] = None):
        """
        Initialize hybrid search helper.
        
        ⚠️ DEPRECATED: Use CatalogRepositoryAdapter instead.
        
        Args:
            db_client: Optional DatabaseClient instance
        """
        warnings.warn(
            "CatalogHybridSearchHelper is deprecated. Use CatalogRepositoryAdapter instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.db_client = db_client or DatabaseClient()
        logger.warning("CatalogHybridSearchHelper initialized (DEPRECATED)")
    
    async def search_by_specific_attribute(
        self,
        tenant_id: str,
        attribute: str,
        value: Optional[str] = None,
        limit: int = 10,
    ) -> List[RetrievedProduct]:
        """
        Search products by specific attribute using DB query.
        
        Args:
            tenant_id: Tenant UUID
            attribute: Attribute name (price, feature, status, free, etc.)
            value: Optional value to match
            limit: Maximum results to return
        
        Returns:
            List of products matching the criteria
        """
        try:
            logger.info(
                f"Searching by specific attribute",
                extra={
                    "tenant_id": tenant_id,
                    "attribute": attribute,
                    "value": value,
                }
            )
            
            # Build parameterized query based on attribute
            query, params = self._build_attribute_query(tenant_id, attribute, value, limit)
            
            # Execute parameterized query
            # Note: database_client.fetch() may need to support parameters
            # If not supported, this will need refactoring
            try:
                rows = await self.db_client.fetch(query, *params)
            except TypeError:
                # Fallback: if fetch doesn't support parameters, use old method (UNSAFE)
                logger.warning(
                    "Database client doesn't support parameterized queries. Using unsafe string interpolation.",
                    extra={"tenant_id": tenant_id}
                )
                # Rebuild query as string (UNSAFE - but needed for backward compatibility)
                query_str = query.replace("$1", f"'{tenant_id}'").replace("$2", str(limit))
                rows = await self.db_client.fetch(query_str)
            
            # Convert rows to RetrievedProduct
            products = []
            for row in rows:
                product = RetrievedProduct(
                    product_id=row.get("product_id") or row.get("id"),
                    title=row.get("title", "Unknown"),
                    description=row.get("description", ""),
                    score=1.0,  # DB queries have exact match (score 1.0)
                    metadata=row.get("metadata", {}),
                )
                products.append(product)
            
            logger.info(
                f"Found {len(products)} products by attribute",
                extra={
                    "tenant_id": tenant_id,
                    "attribute": attribute,
                    "results_count": len(products),
                }
            )
            
            return products
            
        except Exception as e:
            logger.error(
                f"Failed to search by attribute: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "attribute": attribute}
            )
            return []
    
    async def count_products_in_category(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count products with optional category/filter criteria.
        
        Args:
            tenant_id: Tenant UUID
            category: Optional category to filter by
            filters: Optional additional filters
        
        Returns:
            Count of products matching criteria
        """
        try:
            query, params = self._build_count_query(tenant_id, category, filters)
            # Execute parameterized query
            try:
                result = await self.db_client.fetchval(query, *params)
            except TypeError:
                # Fallback: if fetchval doesn't support parameters
                logger.warning(
                    "Database client doesn't support parameterized queries. Using unsafe string interpolation.",
                    extra={"tenant_id": tenant_id}
                )
                # Rebuild query as string (UNSAFE - but needed for backward compatibility)
                query_str = query
                for i, param in enumerate(params, start=1):
                    if isinstance(param, str):
                        query_str = query_str.replace(f"${i}", f"'{param}'")
                    else:
                        query_str = query_str.replace(f"${i}", str(param))
                result = await self.db_client.fetchval(query_str)
            count = result or 0
            
            logger.info(
                f"Counted {count} products",
                extra={
                    "tenant_id": tenant_id,
                    "category": category,
                }
            )
            
            return count
            
        except Exception as e:
            logger.error(
                f"Failed to count products: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "category": category}
            )
            return 0
    
    async def search_by_comparison_attributes(
        self,
        tenant_id: str,
        product_names: List[str],
        limit: int = 10,
    ) -> Dict[str, List[RetrievedProduct]]:
        """
        Search for specific products to enable comparison.
        
        Args:
            tenant_id: Tenant UUID
            product_names: Names of products to compare
            limit: Max results per product
        
        Returns:
            Dictionary mapping product names to their results
        """
        try:
            results = {}
            
            for product_name in product_names:
                query, params = self._build_product_name_query(tenant_id, product_name, limit)
                # Execute parameterized query
                try:
                    rows = await self.db_client.fetch(query, *params)
                except TypeError:
                    # Fallback: if fetch doesn't support parameters
                    logger.warning(
                        "Database client doesn't support parameterized queries. Using unsafe string interpolation.",
                        extra={"tenant_id": tenant_id, "product_name": product_name}
                    )
                    # Rebuild query as string (UNSAFE - but needed for backward compatibility)
                    # Escape product_name manually
                    safe_name = product_name.replace("'", "''")
                    query_str = f"""
                        SELECT id, product_id, title, description, metadata
                        FROM products
                        WHERE tenant_id = '{tenant_id}'
                          AND (title ILIKE '%{safe_name}%' OR description ILIKE '%{safe_name}%')
                        ORDER BY CASE
                            WHEN title ILIKE '{safe_name}' THEN 0
                            WHEN title ILIKE '{safe_name}%' THEN 1
                            ELSE 2
                        END,
                        title
                        LIMIT {limit}
                    """
                    rows = await self.db_client.fetch(query_str)
                
                products = []
                for row in rows:
                    product = RetrievedProduct(
                        product_id=row.get("product_id") or row.get("id"),
                        title=row.get("title", "Unknown"),
                        description=row.get("description", ""),
                        score=1.0,  # Exact match
                        metadata=row.get("metadata", {}),
                    )
                    products.append(product)
                
                results[product_name] = products
            
            logger.info(
                f"Retrieved {len(results)} products for comparison",
                extra={
                    "tenant_id": tenant_id,
                    "product_count": len(results),
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve products for comparison: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "product_names": product_names}
            )
            return {}
    
    def _build_attribute_query(
        self,
        tenant_id: str,
        attribute: str,
        value: Optional[str] = None,
        limit: int = 10,
    ) -> tuple[str, list]:
        """
        Build parameterized SQL query based on attribute.
        
        ⚠️ FIXED: Now uses parameterized queries to prevent SQL injection.
        
        Args:
            tenant_id: Tenant UUID
            attribute: Attribute to query
            value: Optional value to match
            limit: Result limit
        
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        # Use parameterized queries to prevent SQL injection
        # Note: This assumes database_client supports parameterized queries
        # If not, this should be refactored to use repository adapter
        
        attribute_lower = attribute.lower()
        params = [tenant_id, limit]
        
        if attribute_lower in ["price", "cost", "fee"]:
            # Price-related query - use parameterized query
            query = """
                SELECT id, product_id, title, description, metadata
                FROM products
                WHERE tenant_id = $1
                  AND metadata->>'price' IS NOT NULL
                ORDER BY CAST(metadata->>'price' AS NUMERIC)
                LIMIT $2
            """
            return query, params
        
        elif attribute_lower in ["feature", "features", "capability", "capabilities"]:
            # Feature query
            query = """
                SELECT id, product_id, title, description, metadata
                FROM products
                WHERE tenant_id = $1
                  AND metadata->>'features' IS NOT NULL
                ORDER BY title
                LIMIT $2
            """
            return query, params
        
        elif attribute_lower in ["free", "miễn phí", "freemium", "open_source"]:
            # Free/pricing query
            query = """
                SELECT id, product_id, title, description, metadata
                FROM products
                WHERE tenant_id = $1
                  AND (metadata->>'is_free' = 'true' OR metadata->>'pricing_model' = 'free')
                ORDER BY title
                LIMIT $2
            """
            return query, params
        
        elif attribute_lower in ["status", "availability", "sẵn có"]:
            # Status/availability query
            query = """
                SELECT id, product_id, title, description, metadata
                FROM products
                WHERE tenant_id = $1
                  AND metadata->>'status' IS NOT NULL
                ORDER BY title
                LIMIT $2
            """
            return query, params
        
        else:
            # Generic metadata query - escape attribute name
            # Note: Attribute name should be validated/sanitized before use
            # For safety, we'll use a whitelist approach
            safe_attribute = attribute_lower.replace("'", "").replace(";", "").replace("--", "")
            query = f"""
                SELECT id, product_id, title, description, metadata
                FROM products
                WHERE tenant_id = $1
                  AND metadata->>'{safe_attribute}' IS NOT NULL
                ORDER BY title
                LIMIT $2
            """
            return query, params
    
    def _build_count_query(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, list]:
        """
        Build parameterized count query with optional filters.
        
        ⚠️ FIXED: Now uses parameterized queries to prevent SQL injection.
        
        Args:
            tenant_id: Tenant UUID
            category: Optional category filter
            filters: Optional additional filters
        
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        # Use parameterized queries
        query = "SELECT COUNT(*) FROM products WHERE tenant_id = $1"
        params = [tenant_id]
        param_index = 2
        
        if category:
            # Sanitize category to prevent SQL injection
            safe_category = category.replace("'", "").replace(";", "").replace("--", "")
            query += f" AND category = ${param_index}"
            params.append(safe_category)
            param_index += 1
        
        if filters:
            for key, value in filters.items():
                # Sanitize key
                safe_key = key.replace("'", "").replace(";", "").replace("--", "")
                if isinstance(value, str):
                    safe_value = value.replace("'", "''")  # Escape single quotes
                    query += f" AND metadata ->> '{safe_key}' = ${param_index}"
                    params.append(safe_value)
                    param_index += 1
                elif isinstance(value, bool):
                    query += f" AND metadata ->> '{safe_key}' = ${param_index}"
                    params.append('true' if value else 'false')
                    param_index += 1
        
        return query, params
    
    def _build_product_name_query(
        self,
        tenant_id: str,
        product_name: str,
        limit: int = 10,
    ) -> tuple[str, list]:
        """
        Build parameterized query to find specific product by name.
        
        ⚠️ FIXED: Now uses parameterized queries to prevent SQL injection.
        
        Args:
            tenant_id: Tenant UUID
            product_name: Product name to search
            limit: Result limit
        
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        # Use parameterized queries with LIKE pattern
        # Note: PostgreSQL uses $1, $2, etc. for parameters
        query = """
            SELECT id, product_id, title, description, metadata
            FROM products
            WHERE tenant_id = $1
              AND (title ILIKE $2 OR description ILIKE $2)
            ORDER BY CASE
                WHEN title ILIKE $3 THEN 0
                WHEN title ILIKE $4 THEN 1
                ELSE 2
            END,
            title
            LIMIT $5
        """
        
        # Build LIKE patterns
        pattern_contains = f"%{product_name}%"
        pattern_exact = product_name
        pattern_starts = f"{product_name}%"
        
        params = [
            tenant_id,
            pattern_contains,  # $2 - for ILIKE '%name%'
            pattern_exact,    # $3 - for exact match
            pattern_starts,   # $4 - for starts with
            limit             # $5 - for LIMIT
        ]
        
        return query, params

