"""
Webhooks Router
Handles incoming webhooks from external services (Telegram, Teams, Catalog)
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
from backend.infrastructure.database_client import database_client
from backend.shared.logger import logger

router = APIRouter(prefix="", tags=["Webhooks"])


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


# ========================================================================
# TELEGRAM WEBHOOK
# ========================================================================

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    POST /webhook/telegram?token=<bot-token>
    
    Receive webhook from Telegram.
    
    Task 3.3: Tenant ID is resolved from bot token (database lookup), NOT from header.
    
    Query Params:
    - token: Telegram bot token (used to resolve tenant_id from database)
    
    Body: Telegram webhook payload
    
    Returns:
    {
        "ok": true
    }
    """
    multi_tenant_api = get_multi_tenant_api()
    result = await multi_tenant_api.telegram_webhook(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


# ========================================================================
# TEAMS WEBHOOK
# ========================================================================

@router.post("/webhook/teams")
async def teams_webhook(request: Request):
    """
    POST /webhook/teams
    
    Receive webhook from Microsoft Teams.
    
    Task 1.3: Tenant ID is extracted from JWT payload, NOT from query param.
    
    Headers:
    - Authorization: Bearer <teams_jwt> (contains tenant_id in payload)
    
    Body: Teams webhook payload
    
    Returns:
    {
        "type": "message",
        "text": "..."
    }
    """
    multi_tenant_api = get_multi_tenant_api()
    result = await multi_tenant_api.teams_webhook(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


# ========================================================================
# CATALOG WEBHOOK
# ========================================================================

@router.post("/webhooks/catalog/product-updated")
async def catalog_webhook(request: Request):
    """
    POST /webhooks/catalog/product-updated
    
    Receive webhook from catalog service for product updates.
    Task 6: Webhook secret verification (HMAC-SHA256).
    
    Headers:
    - X-Webhook-Signature: HMAC-SHA256(request_body, webhook_secret)
    
    Body:
    {
        "tenant_id": "...",
        "event": "created|updated|deleted",
        "product_id": "..."
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "processed": true
        }
    }
    """
    try:
        # Task 6.1: Get raw body for signature verification
        raw_body = await request.body()
        
        # Parse JSON body
        import json
        body = json.loads(raw_body)
        
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
        
        # Task 6.2: Verify webhook secret
        from backend.interface.middleware.multi_tenant_auth import verify_webhook_secret
        from backend.shared.auth_config import get_tenant_config
        
        tenant_config = await get_tenant_config(tenant_id)
        if not tenant_config:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "TENANT_NOT_FOUND",
                    "message": f"Tenant not found: {tenant_id}",
                },
                status_code=404
            )
        
        signature_header = request.headers.get("X-Webhook-Signature")
        webhook_secret = tenant_config.webhook_secret
        
        # Verify signature (if webhook_secret is configured)
        if webhook_secret:
            if not verify_webhook_secret(raw_body, signature_header, webhook_secret):
                logger.warning(
                    f"Invalid webhook signature for tenant {tenant_id}",
                    extra={"tenant_id": tenant_id}
                )
                return JSONResponse(
                    content={
                        "success": False,
                        "error": "INVALID_WEBHOOK_SIGNATURE",
                        "message": "Invalid webhook signature",
                    },
                    status_code=401
                )
        
        # Get database connection
        db = database_client.pool
        
        multi_tenant_api = get_multi_tenant_api()
        result = await multi_tenant_api.catalog_webhook(
            tenant_id=tenant_id,
            event_data=body,
            db_connection=db,
        )
        
        status_code = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status_code)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog_webhook: {e}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "INVALID_JSON",
                "message": "Invalid JSON payload",
            },
            status_code=400
        )
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

