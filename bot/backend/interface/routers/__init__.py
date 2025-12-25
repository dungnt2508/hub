"""
API Routers - Organized by functionality
"""

from .health import router as health_router
from .web_embed import router as web_embed_router
from .admin import router as admin_router
from .webhooks import router as webhooks_router

__all__ = [
    "health_router",
    "web_embed_router",
    "admin_router",
    "webhooks_router",
]

