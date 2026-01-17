"""API routers"""
from backend.routers.bot import router as bot_router
from backend.routers.admin import router as admin_router

__all__ = ["bot_router", "admin_router"]
