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
from .document_chunker import DocumentChunker, DocumentChunk
from .knowledge_ingester import KnowledgeIngester
from .rag_orchestrator import RAGOrchestrator, RetrievedDocument
from .hr_knowledge_engine import HRKnowledgeEngine
from .knowledge_sync_scheduler import KnowledgeSyncScheduler, get_scheduler

__all__ = [
    # Catalog
    "CatalogKnowledgeEngine",
    "CatalogRetriever",
    "RetrievedProduct",
    "CatalogKnowledgeSyncService",
    "SyncResult",
    "SyncStatus",
    "build_product_text",
    "build_product_metadata",
    # Optimizations
    "BatchEmbeddingGenerator",
    "QueryCache",
    "PerformanceMonitor",
    "get_batch_embedding_generator",
    "get_query_cache",
    "get_performance_monitor",
    # RAG Pipeline
    "DocumentChunker",
    "DocumentChunk",
    "KnowledgeIngester",
    "RAGOrchestrator",
    "RetrievedDocument",
    "HRKnowledgeEngine",
    "KnowledgeSyncScheduler",
    "get_scheduler",
]
