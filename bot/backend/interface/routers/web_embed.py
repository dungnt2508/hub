"""
Web Embed Router
Handles web embed initialization, bot messages, and embed.js serving
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os

from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
from backend.shared.logger import logger

router = APIRouter(prefix="", tags=["Web Embed"])


# Global instance - will be set by main app
_multi_tenant_api: MultiTenantBotAPI = None

def set_multi_tenant_api(api: MultiTenantBotAPI):
    """Set multi-tenant API instance (called from main app)"""
    global _multi_tenant_api
    _multi_tenant_api = api

def get_multi_tenant_api() -> MultiTenantBotAPI:
    """Get multi-tenant API instance"""
    if _multi_tenant_api is None:
        raise RuntimeError("MultiTenantBotAPI not initialized. Call set_multi_tenant_api() first.")
    return _multi_tenant_api


@router.post("/embed/init")
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
    
    Returns:
    {
        "success": true,
        "data": {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "expiresIn": 300,
            "botConfig": {...}
        }
    }
    """
    multi_tenant_api = get_multi_tenant_api()
    result = await multi_tenant_api.embed_init(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


@router.post("/bot/message")
async def bot_message(request: Request):
    """
    POST /bot/message
    
    Send message to bot (requires JWT authentication).
    
    Headers:
    - Authorization: Bearer <jwt_token>
    - Origin: Required (validated against token)
    
    Body:
    {
        "message": "Tôi còn bao nhiêu ngày phép?",
        "sessionId": "session-abc123",  # optional
        "attachments": []  # optional
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "messageId": "...",
            "response": "...",
            "intent": "...",
            "confidence": 0.95
        }
    }
    """
    multi_tenant_api = get_multi_tenant_api()
    result = await multi_tenant_api.bot_message(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


@router.get("/embed.js")
async def serve_embed_js():
    """
    GET /embed.js
    
    Serve the bot embed JavaScript file.
    
    This endpoint serves the client-side JavaScript that creates
    the chat widget on customer websites.
    """
    # Get path to embed.js file (in bot root directory)
    # api.py is at: bot/backend/interface/api.py
    # embed.js is at: bot/embed.js
    # So we need to go up 3 levels from routers/web_embed.py
    bot_root = Path(__file__).parent.parent.parent.parent
    embed_js_path = bot_root / "embed.js"
    
    if not embed_js_path.exists():
        logger.error(f"embed.js not found at {embed_js_path}")
        raise HTTPException(status_code=404, detail="embed.js not found")
    
    # In development, disable cache for easier testing
    # In production, enable cache with max-age
    env = os.getenv("ENVIRONMENT", "dev")
    cache_control = (
        "no-cache, no-store, must-revalidate" 
        if env in ["dev", "development"] 
        else "public, max-age=3600"
    )
    
    return FileResponse(
        path=embed_js_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": cache_control,
        }
    )

