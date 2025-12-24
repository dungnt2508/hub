"""
Catalog Retriever - Retrieve relevant products from vector store
"""
from typing import List, Optional
from dataclasses import dataclass

from ..infrastructure.vector_store import get_vector_store, SearchResult
from ..infrastructure.ai_provider import AIProvider
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


@dataclass
class RetrievedProduct:
    """Retrieved product with relevance score"""
    product_id: str
    title: str
    description: str
    score: float
    metadata: dict


class CatalogRetriever:
    """
    Retrieve relevant products from vector store using semantic search.
    
    Responsibilities:
    - Generate query embedding
    - Vector search in tenant collection
    - Filter by similarity threshold
    - Return products with scores
    """
    
    def __init__(
        self,
        ai_provider: Optional[AIProvider] = None,
        similarity_threshold: float = 0.7,
    ):
        """
        Initialize catalog retriever.
        
        Args:
            ai_provider: Optional AIProvider instance
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.ai_provider = ai_provider or AIProvider()
        self.vector_store = get_vector_store()
        self.similarity_threshold = similarity_threshold
        logger.info(
            f"CatalogRetriever initialized (threshold={similarity_threshold})"
        )
    
    async def retrieve(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[RetrievedProduct]:
        """
        Retrieve relevant products for a query.
        
        Args:
            tenant_id: Tenant UUID
            query: User query text
            top_k: Number of results to return
            score_threshold: Optional custom threshold (overrides default)
        
        Returns:
            List of RetrievedProduct with relevance scores
        
        Raises:
            ExternalServiceError: If retrieval fails
        """
        try:
            logger.debug(
                f"Retrieving products for query: {query[:100]}",
                extra={"tenant_id": tenant_id, "top_k": top_k}
            )
            
            # Generate query embedding
            query_embedding = await self.ai_provider.embed(query)
            
            # Use custom threshold if provided, otherwise use default
            threshold = score_threshold if score_threshold is not None else self.similarity_threshold
            
            # Vector search
            search_results = await self.vector_store.search(
                tenant_id=tenant_id,
                query_vector=query_embedding,
                top_k=top_k,
                score_threshold=threshold,
            )
            
            # Convert to RetrievedProduct
            retrieved_products = []
            for result in search_results:
                try:
                    product = RetrievedProduct(
                        product_id=result.metadata.get("product_id", result.id),
                        title=result.metadata.get("title", "Unknown"),
                        description=result.metadata.get("description", ""),
                        score=result.score,
                        metadata=result.metadata,
                    )
                    retrieved_products.append(product)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse search result: {e}",
                        extra={"result_id": result.id}
                    )
                    continue
            
            logger.info(
                f"Retrieved {len(retrieved_products)} products",
                extra={
                    "tenant_id": tenant_id,
                    "query_length": len(query),
                    "results_count": len(retrieved_products),
                }
            )
            
            return retrieved_products
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve products: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id, "query": query[:100]}
            )
            raise ExternalServiceError(f"Product retrieval failed: {e}") from e
    
    async def retrieve_with_context(
        self,
        tenant_id: str,
        query: str,
        conversation_context: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[RetrievedProduct]:
        """
        Retrieve products with conversation context.
        
        Args:
            tenant_id: Tenant UUID
            query: Current user query
            conversation_context: Previous messages for context
            top_k: Number of results to return
        
        Returns:
            List of RetrievedProduct
        """
        # Build enriched query with context
        if conversation_context:
            # Combine last few messages with current query
            context_text = "\n".join(conversation_context[-3:])  # Last 3 messages
            enriched_query = f"{context_text}\n\nUser question: {query}"
        else:
            enriched_query = query
        
        return await self.retrieve(tenant_id, enriched_query, top_k=top_k)

