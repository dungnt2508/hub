"""
Knowledge Base Optimizations
Performance optimization utilities for catalog knowledge operations
"""
from typing import List, Optional
from functools import lru_cache
import asyncio

from ..infrastructure.ai_provider import AIProvider
from ..infrastructure.catalog_client import CatalogProduct
from ..shared.logger import logger


class BatchEmbeddingGenerator:
    """
    Batch embedding generator for better performance.
    
    Groups multiple texts together to reduce API calls.
    """
    
    def __init__(self, ai_provider: Optional[AIProvider] = None, batch_size: int = 10):
        """
        Initialize batch embedding generator.
        
        Args:
            ai_provider: AIProvider instance
            batch_size: Number of texts to process in parallel
        """
        self.ai_provider = ai_provider or AIProvider()
        self.batch_size = batch_size
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in parallel batches.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Process in batches
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Generate embeddings in parallel
            tasks = [self.ai_provider.embed(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle errors
            for idx, emb in enumerate(batch_embeddings):
                if isinstance(emb, Exception):
                    logger.warning(
                        f"Failed to generate embedding for text {i + idx}: {emb}",
                        exc_info=True
                    )
                    # Use zero vector as fallback
                    all_embeddings.append([0.0] * 1536)
                else:
                    all_embeddings.append(emb)
        
        return all_embeddings


class QueryCache:
    """
    Simple in-memory cache for query embeddings.
    
    Reduces redundant embedding generation for repeated queries.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of cached queries
        """
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, query: str) -> Optional[List[float]]:
        """Get cached embedding for query"""
        if query in self.cache:
            # Update access order (LRU)
            if query in self.access_order:
                self.access_order.remove(query)
            self.access_order.append(query)
            return self.cache[query]
        return None
    
    def set(self, query: str, embedding: List[float]):
        """Cache embedding for query"""
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size and self.access_order:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[query] = embedding
        self.access_order.append(query)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_order.clear()


class PerformanceMonitor:
    """
    Monitor performance metrics for knowledge operations.
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {
            "sync_durations": [],
            "query_latencies": [],
            "embedding_times": [],
            "vector_search_times": [],
        }
    
    def record_sync_duration(self, duration: float):
        """Record sync operation duration"""
        self.metrics["sync_durations"].append(duration)
        # Keep only last 100
        if len(self.metrics["sync_durations"]) > 100:
            self.metrics["sync_durations"] = self.metrics["sync_durations"][-100:]
    
    def record_query_latency(self, latency: float):
        """Record query operation latency"""
        self.metrics["query_latencies"].append(latency)
        if len(self.metrics["query_latencies"]) > 100:
            self.metrics["query_latencies"] = self.metrics["query_latencies"][-100:]
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        stats = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                stats[metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
            else:
                stats[metric_name] = {
                    "count": 0,
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                }
        
        return stats


# Global instances
_batch_embedding_generator: Optional[BatchEmbeddingGenerator] = None
_query_cache: Optional[QueryCache] = None
_performance_monitor: Optional[PerformanceMonitor] = None


def get_batch_embedding_generator() -> BatchEmbeddingGenerator:
    """Get or create global batch embedding generator"""
    global _batch_embedding_generator
    if _batch_embedding_generator is None:
        _batch_embedding_generator = BatchEmbeddingGenerator()
    return _batch_embedding_generator


def get_query_cache() -> QueryCache:
    """Get or create global query cache"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

