"""FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio

# Khắc phục lỗi NotImplementedError của Playwright trên Windows (asyncio subprocess)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.core.config.settings import get_settings
from app.interfaces.middleware.auth import AuthMiddleware
from app.interfaces.middleware.metrics_middleware import MetricsMiddleware

from app.interfaces.api.auth import auth_router
from app.interfaces.api.admin import admin_router
from app.interfaces.api.chat import chat_router
from app.interfaces.api.bot import bot_router
from app.interfaces.api.knowledge import knowledge_router
from app.interfaces.api.migration import migration_router
from app.interfaces.api.analytics import analytics_router
from app.interfaces.api.logs import logs_router
from app.interfaces.api.channel_config import channel_config_router
from app.interfaces.api.ws import ws_router
from app.interfaces.api.guardrails import guardrails_router
from app.interfaces.api.contacts import contacts_router
from app.interfaces.api.catalog import catalog_router
from app.interfaces.api.ontology import ontology_router
from app.interfaces.webhooks.zalo import zalo_router
from app.interfaces.webhooks.facebook import fb_router

settings = get_settings()
# print(settings.database_url)
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.app_version,
    debug=settings.debug,
)

# CORS middleware - MUST be added first to handle preflight requests
cors_origins = settings.cors_origins.split(",") if "," in settings.cors_origins else (
    [settings.cors_origins] if settings.cors_origins != "*" else ["*"]
)
print(cors_origins)

# Ensure localhost:3000 is always allowed for development
if "*" not in cors_origins and "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")

# Authentication middleware (JWT-based) - NEW
app.add_middleware(AuthMiddleware, require_auth=True)
# Prometheus metrics (request count, latency)
app.add_middleware(MetricsMiddleware)

# CORS middleware - MUST be added LAST to ensure it wraps all responses (including errors from other middlewares)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(bot_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(migration_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")
app.include_router(channel_config_router, prefix="/api/v1")
app.include_router(guardrails_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")
app.include_router(ontology_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(zalo_router)
app.include_router(fb_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.title,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (request count, latency, tier distribution)."""
    from app.infrastructure.metrics import get_prometheus_output
    body, content_type = get_prometheus_output()
    from starlette.responses import Response
    return Response(content=body, media_type=content_type)
