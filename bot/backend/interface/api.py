"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import uvicorn
import os

from .api_handler import APIHandler
from .multi_tenant_bot_api import MultiTenantBotAPI
from .admin_api import router as admin_router
from .handlers.embed_init_handler import setup_test_data
from ..shared.logger import logger
from ..shared.config import config
from ..infrastructure.redis_client import redis_client
from ..infrastructure.database_client import database_client
from ..infrastructure.ai_provider import AIProvider


# Create FastAPI app
app = FastAPI(
    title="Hub Bot - Global Router System",
    description="Intelligent routing system with 3-layer architecture",
    version="1.0.0",
)

# CORS middleware
# Allow catalog frontend and other origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
# Also allow any origin for web embed (will be validated per-tenant)
cors_origins.append("*")  # For web embed - origin validation happens in handler
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API handler
api_handler = APIHandler()

# Initialize multi-tenant bot API
multi_tenant_api = MultiTenantBotAPI()

# Register admin API router
app.include_router(admin_router)

# Global AI provider instance (will be closed on shutdown)
_ai_provider: AIProvider = None


@app.on_event("startup")
async def startup_event():
    """Initialize infrastructure on startup"""
    global _ai_provider
    
    try:
        # Connect Redis
        await redis_client.connect()
        logger.info("Infrastructure initialized: Redis connected")
        
        # Connect Database
        await database_client.connect()
        logger.info("Infrastructure initialized: Database connected")
        
        # Setup test data for multi-tenant (development only)
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["dev", "development"]:
            try:
                setup_test_data()
                logger.info("Test tenant data setup completed in startup")
            except Exception as e:
                logger.warning(f"Failed to setup test data in startup: {e}", exc_info=True)
        
        # Initialize multi-tenant bot API
        logger.info("Multi-tenant bot API initialized")
        
        # Initialize AI provider (lazy initialization, no connection needed)
        # We'll create it on first use or here for clarity
        from ..router.steps.embedding_step import EmbeddingClassifierStep
        from ..router.steps.llm_step import LLMClassifierStep
        # AI provider will be initialized when steps are created
        
    except Exception as e:
        logger.error(f"Failed to initialize infrastructure: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up infrastructure on shutdown"""
    global _ai_provider
    
    try:
        # Disconnect Redis
        await redis_client.disconnect()
        logger.info("Infrastructure cleaned up: Redis disconnected")
        
        # Disconnect Database
        await database_client.disconnect()
        logger.info("Infrastructure cleaned up: Database disconnected")
        
        # Close AI provider if exists
        if _ai_provider:
            await _ai_provider.close()
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = await redis_client.health_check()
    db_healthy = await database_client.health_check()
    
    # Check Qdrant with exception handling
    qdrant_healthy = False
    try:
        from ..infrastructure.vector_store import get_vector_store
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
        "service": "hub-bot-router",
        "version": "1.0.0",
        "redis": "healthy" if redis_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "qdrant": "healthy" if qdrant_healthy else "unhealthy",
    }


@app.get("/api/v1/config")
async def get_config():
    """
    Get router configuration (non-sensitive)
    
    Public endpoint - no authentication required.
    """
    return {
        "embedding_threshold": config.EMBEDDING_THRESHOLD,
        "llm_threshold": config.LLM_THRESHOLD,
        "max_message_length": config.MAX_MESSAGE_LENGTH,
        "enable_llm_fallback": config.ENABLE_LLM_FALLBACK,
        "authenticated": False,  # Always false for public endpoint
    }


# ========================================================================
# MULTI-TENANT BOT API ENDPOINTS
# ========================================================================

@app.post("/embed/init")
async def embed_init(request: Request):
    """
    POST /embed/init
    
    Initialize web embed session and issue JWT token.
    
    Headers:
    - Origin: Required (validated against tenant whitelist)
    
    Body:
    {
        "site_id": "catalog-001",
        "platform": "web",
        "user_data": {}  # optional
    }
    """
    result = await multi_tenant_api.embed_init(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


@app.post("/bot/message")
async def bot_message(request: Request):
    """
    POST /bot/message
    
    Send message to bot (requires JWT authentication).
    
    Headers:
    - Authorization: Bearer <jwt_token>
    - Origin: Required (validated against token)
    
    Query Params:
    - tenant_id: Tenant ID (required for now)
    
    Body:
    {
        "message": "Tôi còn bao nhiêu ngày phép?",
        "sessionId": "session-abc123",  # optional
        "attachments": []  # optional
    }
    """
    result = await multi_tenant_api.bot_message(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


# ========================================================================
# ADMIN API ENDPOINTS
# ========================================================================

@app.post("/admin/tenants/{tenant_id}/knowledge/sync")
async def admin_knowledge_sync(tenant_id: str, request: Request):
    """
    POST /admin/tenants/{tenant_id}/knowledge/sync
    
    Trigger manual sync of knowledge base for tenant.
    Requires API key authentication.
    
    Query params:
    - batch_size: Optional batch size (default: 10)
    """
    try:
        # Get batch_size from query params
        batch_size = int(request.query_params.get("batch_size", 10))
        
        # Get database connection
        db = database_client.pool
        
        result = await multi_tenant_api.admin_knowledge_sync(
            tenant_id=tenant_id,
            batch_size=batch_size,
            db_connection=db,
        )
        
        status_code = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error in admin_knowledge_sync endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": str(e),
            },
            status_code=500
        )


@app.get("/admin/tenants/{tenant_id}/knowledge/status")
async def admin_knowledge_status(tenant_id: str):
    """
    GET /admin/tenants/{tenant_id}/knowledge/status
    
    Get current sync status for tenant.
    Requires API key authentication.
    """
    try:
        # Get database connection
        db = database_client.pool
        
        result = await multi_tenant_api.admin_knowledge_status(
            tenant_id=tenant_id,
            db_connection=db,
        )
        
        status_code = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error in admin_knowledge_status endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": str(e),
            },
            status_code=500
        )


@app.delete("/admin/tenants/{tenant_id}/knowledge")
async def admin_knowledge_delete(tenant_id: str):
    """
    DELETE /admin/tenants/{tenant_id}/knowledge
    
    Delete all knowledge base data for tenant.
    Requires API key authentication.
    """
    try:
        # Get database connection
        db = database_client.pool
        
        result = await multi_tenant_api.admin_knowledge_delete(
            tenant_id=tenant_id,
            db_connection=db,
        )
        
        status_code = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error in admin_knowledge_delete endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": str(e),
            },
            status_code=500
        )


@app.post("/webhooks/catalog/product-updated")
async def catalog_webhook(request: Request):
    """
    POST /webhooks/catalog/product-updated
    
    Receive webhook from catalog service for product updates.
    Optional webhook secret verification.
    
    Body:
    {
        "tenant_id": "...",
        "event": "created|updated|deleted",
        "product_id": "..."
    }
    """
    try:
        body = await request.json()
        
        tenant_id = body.get("tenant_id")
        if not tenant_id:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "MISSING_TENANT_ID",
                    "message": "tenant_id is required",
                },
                status_code=400
            )
        
        # Get database connection
        db = database_client.pool
        
        result = await multi_tenant_api.catalog_webhook(
            tenant_id=tenant_id,
            event_data=body,
            db_connection=db,
        )
        
        status_code = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error in catalog_webhook endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": str(e),
            },
            status_code=500
        )


@app.get("/embed.js")
async def serve_embed_js():
    """
    GET /embed.js
    
    Serve the bot embed JavaScript file.
    """
    # Get path to embed.js file (in bot root directory)
    bot_root = Path(__file__).parent.parent.parent
    embed_js_path = bot_root / "embed.js"
    
    if not embed_js_path.exists():
        logger.error(f"embed.js not found at {embed_js_path}")
        raise HTTPException(status_code=404, detail="embed.js not found")
    
    # In development, disable cache for easier testing
    # In production, enable cache with max-age
    cache_control = "no-cache, no-store, must-revalidate" if os.getenv("ENVIRONMENT", "dev") in ["dev", "development"] else "public, max-age=3600"
    
    return FileResponse(
        path=embed_js_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": cache_control,
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "backend.interface.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8386)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )

