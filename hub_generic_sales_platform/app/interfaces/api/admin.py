"""
Admin & Tenant Management API

Requires JWT authentication. User can only manage tenant they belong to.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import TenantRepository
from app.interfaces.api.dependencies import get_current_tenant_id

admin_router = APIRouter(tags=["admin"])

# ========== Schemas ==========

class TenantCreate(BaseModel):
    name: str

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None

# ========== Endpoints ==========

def _verify_tenant_access(path_tenant_id: str, current_tenant_id: str) -> None:
    """Verify user can only access their own tenant"""
    if path_tenant_id != current_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: can only manage your own tenant"
        )


@admin_router.get("/tenants")
async def list_tenants(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """List tenant(s) - returns only the tenant the user belongs to"""
    repo = TenantRepository(db)
    db_obj = await repo.get(tenant_id, tenant_id)
    if not db_obj:
        return []
    return [db_obj]

@admin_router.post("/tenants")
async def create_tenant(
    tenant: TenantCreate,
    _tenant_id: str = Depends(get_current_tenant_id),  # Auth required
    db: AsyncSession = Depends(get_session)
):
    """Create new tenant - requires auth (RBAC: owner only can be added later)"""
    repo = TenantRepository(db)
    return await repo.create(tenant.model_dump())

@admin_router.put("/tenants/{path_tenant_id}")
async def update_tenant(
    path_tenant_id: str,
    tenant_in: TenantUpdate,
    current_tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    _verify_tenant_access(path_tenant_id, current_tenant_id)
    repo = TenantRepository(db)
    db_obj = await repo.get(path_tenant_id, path_tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return await repo.update(db_obj, tenant_in.model_dump(exclude_unset=True))

@admin_router.delete("/tenants/{path_tenant_id}")
async def delete_tenant(
    path_tenant_id: str,
    current_tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    _verify_tenant_access(path_tenant_id, current_tenant_id)
    repo = TenantRepository(db)
    db_obj = await repo.delete(path_tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

@admin_router.patch("/tenants/{path_tenant_id}/status")
async def update_tenant_status(
    path_tenant_id: str,
    status_in: Dict[str, str],
    current_tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    _verify_tenant_access(path_tenant_id, current_tenant_id)
    new_status = status_in.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    repo = TenantRepository(db)
    db_obj = await repo.get(path_tenant_id, path_tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return await repo.update(db_obj, {"status": new_status})

@admin_router.get("/health")
async def health():
    return {"status": "healthy", "version": "2026.1"}
