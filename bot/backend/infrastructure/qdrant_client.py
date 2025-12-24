"""
Qdrant Client - Wrapper for Qdrant Python client
Provides tenant-isolated vector storage operations
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid

from qdrant_client import QdrantClient as QdrantSDKClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)

try:
    from qdrant_client.http.exceptions import ResponseHandlingException
except ImportError:
    # Fallback if exception path changes
    ResponseHandlingException = Exception

from ..shared.config import config
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


@dataclass
class VectorPoint:
    """Vector point with metadata"""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Search result with similarity score"""
    id: str
    score: float
    metadata: Dict[str, Any]


class QdrantClient:
    """
    Qdrant client wrapper with tenant isolation.
    
    Each tenant has a separate collection: `tenant_{tenant_id}_products`
    """
    
    def __init__(self):
        """Initialize Qdrant client"""
        self.url = config.QDRANT_URL
        self.api_key = config.QDRANT_API_KEY
        self.vector_dimension = config.VECTOR_DIMENSION
        
        try:
            self.client = QdrantSDKClient(
                url=self.url,
                api_key=self.api_key if self.api_key else None,
                timeout=10.0,
            )
            logger.info(f"Qdrant client initialized: {self.url}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}", exc_info=True)
            raise ExternalServiceError(f"Qdrant initialization failed: {e}") from e
    
    def _get_collection_name(self, tenant_id: str) -> str:
        """Get collection name for tenant"""
        return f"tenant_{tenant_id}_products"
    
    async def create_collection(
        self,
        tenant_id: str,
        vector_dimension: Optional[int] = None,
    ) -> bool:
        """
        Create collection for tenant if not exists.
        
        Args:
            tenant_id: Tenant UUID
            vector_dimension: Vector dimension (defaults to config)
        
        Returns:
            True if created, False if already exists
        """
        collection_name = self._get_collection_name(tenant_id)
        dimension = vector_dimension or self.vector_dimension
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]
            
            if collection_name in existing_names:
                logger.info(f"Collection already exists: {collection_name}")
                return False
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
            
            logger.info(f"Created collection: {collection_name} (dim={dimension})")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to create collection {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Failed to create collection: {e}") from e
    
    async def collection_exists(self, tenant_id: str) -> bool:
        """Check if collection exists for tenant"""
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]
            return collection_name in existing_names
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}", exc_info=True)
            return False
    
    async def upsert_vectors(
        self,
        tenant_id: str,
        vectors: List[VectorPoint],
    ) -> bool:
        """
        Upsert vectors into tenant collection.
        
        Args:
            tenant_id: Tenant UUID
            vectors: List of vector points to upsert
        
        Returns:
            True if successful
        """
        if not vectors:
            logger.warning("No vectors to upsert")
            return True
        
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            # Ensure collection exists
            if not await self.collection_exists(tenant_id):
                await self.create_collection(tenant_id)
            
            # Convert to Qdrant points
            points = []
            for vec_point in vectors:
                # Use UUID as point ID if provided, otherwise generate
                point_id = vec_point.id
                if not point_id:
                    point_id = str(uuid.uuid4())
                
                # Ensure metadata includes tenant_id for filtering
                metadata = vec_point.metadata.copy()
                metadata["tenant_id"] = tenant_id
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vec_point.vector,
                        payload=metadata,
                    )
                )
            
            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            
            logger.info(
                f"Upserted {len(points)} vectors to {collection_name}",
                extra={"tenant_id": tenant_id, "count": len(points)}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to upsert vectors to {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Failed to upsert vectors: {e}") from e
    
    async def search(
        self,
        tenant_id: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search vectors in tenant collection.
        
        Args:
            tenant_id: Tenant UUID
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            metadata_filter: Additional metadata filters
        
        Returns:
            List of search results with scores
        """
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            # Check collection exists
            if not await self.collection_exists(tenant_id):
                logger.warning(f"Collection does not exist: {collection_name}")
                return []
            
            # Build filter: always filter by tenant_id
            filter_conditions = [
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id)
                )
            ]
            
            # Add additional metadata filters
            if metadata_filter:
                for key, value in metadata_filter.items():
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            query_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search
            search_results: List[ScoredPoint] = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
            
            # Convert to SearchResult
            results = []
            for result in search_results:
                results.append(
                    SearchResult(
                        id=str(result.id),
                        score=result.score,
                        metadata=result.payload or {},
                    )
                )
            
            logger.debug(
                f"Search returned {len(results)} results from {collection_name}",
                extra={
                    "tenant_id": tenant_id,
                    "top_k": top_k,
                    "results_count": len(results)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Failed to search in {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Search failed: {e}") from e
    
    async def delete_collection(self, tenant_id: str) -> bool:
        """
        Delete collection for tenant.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            True if successful
        """
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            if not await self.collection_exists(tenant_id):
                logger.warning(f"Collection does not exist: {collection_name}")
                return False
            
            self.client.delete_collection(collection_name=collection_name)
            
            logger.info(f"Deleted collection: {collection_name}", extra={"tenant_id": tenant_id})
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to delete collection {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Failed to delete collection: {e}") from e
    
    async def delete_points(
        self,
        tenant_id: str,
        point_ids: List[str],
    ) -> bool:
        """
        Delete specific points from collection.
        
        Args:
            tenant_id: Tenant UUID
            point_ids: List of point IDs to delete
        
        Returns:
            True if successful
        """
        if not point_ids:
            return True
        
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            if not await self.collection_exists(tenant_id):
                logger.warning(f"Collection does not exist: {collection_name}")
                return False
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids,
            )
            
            logger.info(
                f"Deleted {len(point_ids)} points from {collection_name}",
                extra={"tenant_id": tenant_id, "count": len(point_ids)}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to delete points from {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Failed to delete points: {e}") from e
    
    async def get_collection_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection information (points count, etc.).
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            Collection info dict or None
        """
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            if not await self.collection_exists(tenant_id):
                return None
            
            collection_info = self.client.get_collection(collection_name=collection_name)
            
            return {
                "name": collection_info.name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "config": {
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.value,
                },
            }
            
        except Exception as e:
            logger.error(
                f"Failed to get collection info for {collection_name}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            return None
    
    async def health_check(self) -> bool:
        """
        Check Qdrant service health.
        
        Returns:
            True if Qdrant is available and responding, False otherwise
        """
        try:
            # Check if client is initialized
            if not hasattr(self, 'client') or self.client is None:
                logger.warning("Qdrant client not initialized")
                return False
            
            # Simple health check: try to list collections
            # This will fail if Qdrant is not available
            self.client.get_collections()
            return True
        except ResponseHandlingException as e:
            # Qdrant HTTP client exception (connection refused, etc.)
            logger.warning(f"Qdrant health check failed (connection error): {e}")
            return False
        except (ConnectionError, OSError) as e:
            # Connection refused, connection reset, etc.
            logger.warning(f"Qdrant health check failed (connection error): {e}")
            return False
        except Exception as e:
            # Other exceptions (timeout, API errors, etc.)
            error_type = type(e).__name__
            logger.warning(f"Qdrant health check failed ({error_type}): {e}")
            return False

