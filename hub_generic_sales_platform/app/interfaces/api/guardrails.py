"""
Guardrail API – CRUD tenant_guardrail (Quy tắc An toàn)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import GuardrailRepository
from app.interfaces.api.dependencies import get_current_tenant_id

guardrails_router = APIRouter(tags=["guardrails"])


class GuardrailCreate(BaseModel):
    code: str
    name: str
    condition_expression: str
    violation_action: str = "block"
    fallback_message: Optional[str] = None
    priority: int = 0
    is_active: bool = True


class GuardrailUpdate(BaseModel):
    name: Optional[str] = None
    condition_expression: Optional[str] = None
    violation_action: Optional[str] = None
    fallback_message: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


@guardrails_router.get("/guardrails")
async def list_guardrails(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    active_only: bool = False
):
    """List guardrails. active_only=true → only active."""
    repo = GuardrailRepository(db)
    if active_only:
        items = await repo.get_active_for_tenant(tenant_id)
    else:
        items = await repo.get_multi(tenant_id=tenant_id, limit=100)
    return [
        {"id": g.id, "code": g.code, "name": g.name, "condition_expression": g.condition_expression,
         "violation_action": g.violation_action, "fallback_message": g.fallback_message,
         "priority": g.priority, "is_active": g.is_active}
        for g in items
    ]


@guardrails_router.post("/guardrails")
async def create_guardrail(
    data: GuardrailCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Create guardrail."""
    repo = GuardrailRepository(db)
    obj = await repo.create({
        "code": data.code,
        "name": data.name,
        "condition_expression": data.condition_expression,
        "violation_action": data.violation_action,
        "fallback_message": data.fallback_message,
        "priority": data.priority,
        "is_active": data.is_active,
    }, tenant_id=tenant_id)
    return {"id": obj.id, "code": obj.code, "name": obj.name, "condition_expression": obj.condition_expression,
            "violation_action": obj.violation_action, "fallback_message": obj.fallback_message,
            "priority": obj.priority, "is_active": obj.is_active}


@guardrails_router.put("/guardrails/{guardrail_id}")
async def update_guardrail(
    guardrail_id: str,
    data: GuardrailUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Update guardrail."""
    repo = GuardrailRepository(db)
    existing = await repo.get(guardrail_id, tenant_id=tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    updated = await repo.update(existing, data.model_dump(exclude_unset=True), tenant_id=tenant_id)
    return {"id": updated.id, "code": updated.code, "name": updated.name, "condition_expression": updated.condition_expression,
            "violation_action": updated.violation_action, "fallback_message": updated.fallback_message,
            "priority": updated.priority, "is_active": updated.is_active}


@guardrails_router.delete("/guardrails/{guardrail_id}")
async def delete_guardrail(
    guardrail_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Delete guardrail."""
    repo = GuardrailRepository(db)
    result = await repo.delete(guardrail_id, tenant_id=tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return {"message": "Deleted"}
