"""
FastAPI Application Entry Point

Cấu trúc:
- api.py: Main FastAPI app, register routers
- routers/: Organized by functionality
  - health.py: Health check & config
  - web_embed.py: Web embed endpoints
  - admin.py: Admin endpoints (tenant, knowledge)
  - webhooks.py: Webhook endpoints
- multi_tenant_bot_api.py: Business logic classes
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from .api_handler import APIHandler
from .multi_tenant_bot_api import MultiTenantBotAPI
# Priority 2 Fix: Removed setup_test_data import - test data should not be in production code
from .routers import (
    health_router,
    web_embed_router,
    admin_router,
    webhooks_router,
)
from ..shared.logger import logger
from ..shared.auth_config import set_db_connection
from ..shared.metrics import metrics_collector
from ..infrastructure.redis_client import redis_client
from ..infrastructure.database_client import database_client
from ..infrastructure.ai_provider import AIProvider


# Create FastAPI app
app = FastAPI(
    title="Hub - Global Router System",
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

# Initialize multi-tenant bot API (shared instance for routers)
multi_tenant_api = MultiTenantBotAPI()

# Global AI provider instance (will be closed on shutdown)
_ai_provider: AIProvider = None

# Inject multi_tenant_api into routers (dependency injection)
from .routers.web_embed import set_multi_tenant_api as set_web_embed_api
from .routers.admin import set_multi_tenant_api as set_admin_api
from .routers.webhooks import set_multi_tenant_api as set_webhooks_api

set_web_embed_api(multi_tenant_api)
set_admin_api(multi_tenant_api)
set_webhooks_api(multi_tenant_api)

# Register routers
app.include_router(health_router)
app.include_router(web_embed_router)
app.include_router(admin_router)
app.include_router(webhooks_router)


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
        
        # Set database connection pool for auth_config module
        set_db_connection(database_client.pool)
        logger.info("Database connection set for auth_config")
        
        # Priority 2 Fix: Remove test data from production
        # Test data should only be created via scripts or tests, not in application startup
        # Use scripts/create_tenant.py or POST /admin/tenants to create real tenants
        
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


# All endpoints are now registered via routers above
# See routers/ directory for endpoint implementations


if __name__ == "__main__":
    uvicorn.run(
        "backend.interface.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8386)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )

