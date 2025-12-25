"""
Health & Config Router
"""
from fastapi import APIRouter, Response
from backend.shared.logger import logger
from backend.shared.config import config
from backend.shared.metrics import metrics_collector
from backend.infrastructure.redis_client import redis_client
from backend.infrastructure.database_client import database_client

router = APIRouter(prefix="", tags=["Health & Config"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns status of all infrastructure services:
    - Redis
    - Database
    - Qdrant (vector store)
    """
    redis_healthy = await redis_client.health_check()
    db_healthy = await database_client.health_check()
    
    # Check Qdrant with exception handling
    qdrant_healthy = False
    try:
        from backend.infrastructure.vector_store import get_vector_store
        vector_store = get_vector_store()
        qdrant_healthy = await vector_store.health_check()
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}", exc_info=True)
        qdrant_healthy = False
    
    # Overall status: degraded if any service is down
    all_healthy = redis_healthy and db_healthy and qdrant_healthy
    status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": status,
        "service": "hub-bot-service",
        "version": "1.0.0",
        "redis": "healthy" if redis_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "qdrant": "healthy" if qdrant_healthy else "unhealthy",
    }


@router.get("/api/v1/config")
async def get_config():
    """
    Get router configuration (non-sensitive)
    
    Public endpoint - no authentication required.
    Returns configuration values for client-side use.
    """
    return {
        "embedding_threshold": config.EMBEDDING_THRESHOLD,
        "llm_threshold": config.LLM_THRESHOLD,
        "max_message_length": config.MAX_MESSAGE_LENGTH,
        "enable_llm_fallback": config.ENABLE_LLM_FALLBACK,
        "authenticated": False,  # Always false for public endpoint
    }


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Task 9: Export metrics in Prometheus format for scraping.
    
    Returns:
        Prometheus text format metrics
    """
    prometheus_metrics = metrics_collector.export_prometheus()
    return Response(
        content=prometheus_metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

