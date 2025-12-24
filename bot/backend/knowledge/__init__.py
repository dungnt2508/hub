"""
Knowledge Layer - RAG pipelines for different domains
"""

from .catalog_knowledge_engine import CatalogKnowledgeEngine
from .catalog_retriever import CatalogRetriever, RetrievedProduct
from .catalog_knowledge_sync import CatalogKnowledgeSyncService, SyncResult, SyncStatus
from .product_text_builder import build_product_text, build_product_metadata
from .optimizations import (
    BatchEmbeddingGenerator,
    QueryCache,
    PerformanceMonitor,
    get_batch_embedding_generator,
    get_query_cache,
    get_performance_monitor,
)

__all__ = [
    "CatalogKnowledgeEngine",
    "CatalogRetriever",
    "RetrievedProduct",
    "CatalogKnowledgeSyncService",
    "SyncResult",
    "SyncStatus",
    "build_product_text",
    "build_product_metadata",
    "BatchEmbeddingGenerator",
    "QueryCache",
    "PerformanceMonitor",
    "get_batch_embedding_generator",
    "get_query_cache",
    "get_performance_monitor",
]
