"""
Admin Router
Handles tenant management and knowledge base administration
"""
from fastapi import APIRouter, Request, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
from backend.infrastructure.database_client import database_client
from backend.shared.logger import logger
from backend.schemas.multi_tenant_types import PlanType
from backend.interface.middleware.multi_tenant_auth import require_api_key

router = APIRouter(prefix="/admin", tags=["Admin"])


# ========================================================================
# REQUEST/RESPONSE MODELS
# ========================================================================

class CreateTenantRequest(BaseModel):
    """Request model for creating a new tenant"""
    name: str = Field(..., description="Tenant name (e.g., 'GSNAKE Catalog')", example="GSNAKE Catalog")
    site_id: str = Field(..., description="Site identifier (e.g., 'catalog-001')", example="catalog-001")
    web_embed_origins: List[str] = Field(
        ..., 
        description="List of allowed origins for web embed",
        example=["https://gsnake.com", "https://www.gsnake.com"]
    )
    plan: Optional[str] = Field(
        default="basic",
        description="Service plan: basic, professional, or enterprise",
        example="professional"
    )
    telegram_enabled: Optional[bool] = Field(
        default=False,
        description="Enable Telegram bot integration"
    )
    teams_enabled: Optional[bool] = Field(
        default=False,
        description="Enable Microsoft Teams bot integration"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "GSNAKE Catalog",
                "site_id": "catalog-001",
                "web_embed_origins": ["https://gsnake.com"],
                "plan": "professional",
                "telegram_enabled": False,
                "teams_enabled": False
            }
        }


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
# TENANT MANAGEMENT
# ========================================================================

@router.post("/tenants", response_model=dict)
@require_api_key
async def admin_create_tenant(request: Request, request_body: CreateTenantRequest):
    """
    POST /admin/tenants
    
    Create new tenant (requires API key).
    
    **Request Body:**
    - `name`: Tenant name (required)
    - `site_id`: Site identifier (required, must be unique)
    - `web_embed_origins`: List of allowed origins for web embed (required)
    - `plan`: Service plan - basic, professional, or enterprise (optional, default: basic)
    - `telegram_enabled`: Enable Telegram bot (optional, default: false)
    - `teams_enabled`: Enable Teams bot (optional, default: false)
    
    **Returns:**
    - `success`: true
    - `data`: Tenant information including tenant_id, site_id, api_key, jwt_secret
    """
    # Use the actual request object (with API key verified by decorator)
    multi_tenant_api = get_multi_tenant_api()
    result = await multi_tenant_api.admin_create_tenant(request)
    
    # Handle error responses
    if result.get("error"):
        status_code = result.get("status_code", 500)
        return JSONResponse(
            content={"error": True, "message": result.get("message", "Internal server error")},
            status_code=status_code
        )
    
    return JSONResponse(content=result)


# ========================================================================
# KNOWLEDGE BASE MANAGEMENT
# ========================================================================

@router.post("/tenants/{tenant_id}/knowledge/sync", response_model=dict)
@require_api_key
async def admin_knowledge_sync(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID", example="123e4567-e89b-12d3-a456-426614174000"),
    batch_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Batch size for syncing (1-100)",
        example=10
    )
):
    """
    POST /admin/tenants/{tenant_id}/knowledge/sync
    
    Trigger manual sync of knowledge base for tenant.
    Requires API key authentication.
    
    **Path Parameters:**
    - `tenant_id`: Tenant UUID (required)
    
    **Query Parameters:**
    - `batch_size`: Number of items to sync per batch (optional, default: 10, range: 1-100)
    
    **Returns:**
    - `success`: true
    - `data`: Sync results including synced_count, failed_count, status
    """
    try:
        # Task 2.3: Verify tenant_id from path matches API key tenant_id
        context = request.state.user_context
        verified_tenant_id = context.tenant_id
        
        if tenant_id != verified_tenant_id:
            logger.warning(
                f"Tenant ID mismatch: path={tenant_id}, API key={verified_tenant_id}"
            )
            return JSONResponse(
                content={
                    "error": True,
                    "message": "Tenant ID mismatch",
                },
                status_code=403
            )
        
        # Get database connection
        db = database_client.pool
        
        multi_tenant_api = get_multi_tenant_api()
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


@router.get("/tenants/{tenant_id}/knowledge/status", response_model=dict)
@require_api_key
async def admin_knowledge_status(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID", example="123e4567-e89b-12d3-a456-426614174000")
):
    """
    GET /admin/tenants/{tenant_id}/knowledge/status
    
    Get current sync status for tenant.
    Requires API key authentication.
    
    Returns:
    {
        "success": true,
        "data": {
            "last_sync_at": "2025-01-20T10:30:00",
            "product_count": 100,
            "sync_status": "completed"
        }
    }
    """
    try:
        # Task 2.3: Verify tenant_id from path matches API key tenant_id
        context = request.state.user_context
        verified_tenant_id = context.tenant_id
        
        if tenant_id != verified_tenant_id:
            logger.warning(
                f"Tenant ID mismatch: path={tenant_id}, API key={verified_tenant_id}"
            )
            return JSONResponse(
                content={
                    "error": True,
                    "message": "Tenant ID mismatch",
                },
                status_code=403
            )
        
        # Get database connection
        db = database_client.pool
        
        multi_tenant_api = get_multi_tenant_api()
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


@router.delete("/tenants/{tenant_id}/knowledge", response_model=dict)
@require_api_key
async def admin_knowledge_delete(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID", example="123e4567-e89b-12d3-a456-426614174000")
):
    """
    DELETE /admin/tenants/{tenant_id}/knowledge
    
    Delete all knowledge base data for tenant.
    Requires API key authentication.
    
    Returns:
    {
        "success": true,
        "data": {
            "deleted_count": 100
        }
    }
    """
    try:
        # Task 2.3: Verify tenant_id from path matches API key tenant_id
        context = request.state.user_context
        verified_tenant_id = context.tenant_id
        
        if tenant_id != verified_tenant_id:
            logger.warning(
                f"Tenant ID mismatch: path={tenant_id}, API key={verified_tenant_id}"
            )
            return JSONResponse(
                content={
                    "error": True,
                    "message": "Tenant ID mismatch",
                },
                status_code=403
            )
        
        # Get database connection
        db = database_client.pool
        
        multi_tenant_api = get_multi_tenant_api()
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

