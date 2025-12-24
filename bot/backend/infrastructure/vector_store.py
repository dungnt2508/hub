"""
Vector Store - Abstraction layer for vector database operations
Provides high-level interface for knowledge base storage
"""
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from .qdrant_client import QdrantClient, VectorPoint, SearchResult
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


class VectorStore(ABC):
    """Abstract vector store interface"""
    
    @abstractmethod
    async def create_collection(self, tenant_id: str) -> bool:
        """Create collection for tenant"""
        pass
    
    @abstractmethod
    async def upsert_vectors(
        self,
        tenant_id: str,
        vectors: List[VectorPoint],
    ) -> bool:
        """Upsert vectors"""
        pass
    
    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """Search vectors"""
        pass
    
    @abstractmethod
    async def delete_collection(self, tenant_id: str) -> bool:
        """Delete collection"""
        pass


class QdrantVectorStore(VectorStore):
    """
    Qdrant implementation of VectorStore.
    
    This class provides a high-level interface while delegating
    to QdrantClient for actual operations.
    """
    
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        """
        Initialize vector store.
        
        Args:
            qdrant_client: Optional QdrantClient instance (creates new if None)
        """
        self.qdrant_client = qdrant_client or QdrantClient()
        logger.info("QdrantVectorStore initialized")
    
    async def create_collection(self, tenant_id: str) -> bool:
        """Create collection for tenant"""
        try:
            return await self.qdrant_client.create_collection(tenant_id)
        except Exception as e:
            logger.error(
                f"Failed to create collection for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            raise ExternalServiceError(f"Failed to create collection: {e}") from e
    
    async def upsert_vectors(
        self,
        tenant_id: str,
        vectors: List[VectorPoint],
    ) -> bool:
        """Upsert vectors into tenant collection"""
        try:
            return await self.qdrant_client.upsert_vectors(tenant_id, vectors)
        except Exception as e:
            logger.error(
                f"Failed to upsert vectors for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "vector_count": len(vectors)}
            )
            raise ExternalServiceError(f"Failed to upsert vectors: {e}") from e
    
    async def search(
        self,
        tenant_id: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """Search vectors in tenant collection"""
        try:
            return await self.qdrant_client.search(
                tenant_id=tenant_id,
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=score_threshold,
            )
        except Exception as e:
            logger.error(
                f"Failed to search for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "top_k": top_k}
            )
            raise ExternalServiceError(f"Search failed: {e}") from e
    
    async def delete_collection(self, tenant_id: str) -> bool:
        """Delete collection for tenant"""
        try:
            return await self.qdrant_client.delete_collection(tenant_id)
        except Exception as e:
            logger.error(
                f"Failed to delete collection for tenant {tenant_id}: {e}",
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
        try:
            return await self.qdrant_client.delete_points(tenant_id, point_ids)
        except Exception as e:
            logger.error(
                f"Failed to delete points for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "point_count": len(point_ids)}
            )
            raise ExternalServiceError(f"Failed to delete points: {e}") from e
    
    async def collection_exists(self, tenant_id: str) -> bool:
        """Check if collection exists"""
        return await self.qdrant_client.collection_exists(tenant_id)
    
    async def get_collection_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        return await self.qdrant_client.get_collection_info(tenant_id)
    
    async def health_check(self) -> bool:
        """Check vector store health"""
        return await self.qdrant_client.health_check()


# Global instance (lazy initialization)
_vector_store_instance: Optional[QdrantVectorStore] = None


def get_vector_store() -> QdrantVectorStore:
    """Get or create global vector store instance"""
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = QdrantVectorStore()
    
    return _vector_store_instance

