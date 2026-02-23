"""
Bot Management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository, CapabilityRepository
from app.infrastructure.database.models.bot import BotVersion
from app.interfaces.api.dependencies import get_current_tenant_id

bot_router = APIRouter(tags=["bots"])

# ========== Schemas ==========

class BotCreate(BaseModel):
    name: str
    code: str
    domain_id: Optional[str] = None

class BotUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None
    domain_id: Optional[str] = None

class CapabilityResponse(BaseModel):
    id: str
    code: str
    domain_id: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CapabilityUpdate(BaseModel):
    codes: List[str]

class KnowledgeDomainResponse(BaseModel):
    id: str
    code: str
    name: str

    class Config:
        from_attributes = True

class BotVersionResponse(BaseModel):
    id: str
    bot_id: str
    version: int
    is_active: bool
    capabilities: List[CapabilityResponse] = []

    class Config:
        from_attributes = True

class BotResponse(BaseModel):
    id: str
    tenant_id: str
    domain_id: Optional[str] = None
    code: str
    name: str
    status: str
    versions_count: int = 0
    capabilities: List[str] = []
    domain: Optional[KnowledgeDomainResponse] = None

    class Config:
        from_attributes = True

# ========== Endpoints ==========

@bot_router.get("/bots", response_model=List[BotResponse])
async def list_bots(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    status: Optional[str] = Query(None, description="Filter by status, e.g. 'active'"),
):
    """List bots for current authenticated user's tenant. Use status=active for selectors."""
    repo = BotRepository(db)
    if status == "active":
        return await repo.get_active_bots(tenant_id=tenant_id)
    return await repo.get_multi(tenant_id=tenant_id)

@bot_router.post("/bots", response_model=BotResponse)
async def create_bot(
    bot: BotCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Create bot for current authenticated user's tenant"""
    repo = BotRepository(db)
    
    # Check if bot with same code exists for this tenant
    existing_bot = await repo.get_by_code(bot.code, tenant_id=tenant_id)
    if existing_bot:
        raise HTTPException(status_code=400, detail=f"Bot with code '{bot.code}' already exists")
    
    bot_obj = await repo.create(bot.model_dump(), tenant_id=tenant_id)
    return await repo.get(bot_obj.id, tenant_id=tenant_id)

@bot_router.put("/bots/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_in: BotUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BotRepository(db)
    db_obj = await repo.get(bot_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Check if bot code is being changed and if new code already exists
    if bot_in.code and bot_in.code != db_obj.code:
        existing_bot = await repo.get_by_code(bot_in.code, tenant_id=tenant_id)
        if existing_bot:
            raise HTTPException(status_code=400, detail=f"Bot with code '{bot_in.code}' already exists")
    
    await repo.update(db_obj, bot_in.model_dump(exclude_unset=True), tenant_id=tenant_id)
    return await repo.get(bot_id, tenant_id=tenant_id)

@bot_router.delete("/bots/{bot_id}")
async def delete_bot(
    bot_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BotRepository(db)
    db_obj = await repo.delete(bot_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": "Bot deleted successfully"}

@bot_router.patch("/bots/{bot_id}/status")
async def update_bot_status(
    bot_id: str,
    status_in: Dict[str, str],
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    new_status = status_in.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    repo = BotRepository(db)
    db_obj = await repo.get(bot_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return await repo.update(db_obj, {"status": new_status}, tenant_id=tenant_id)

# ========== Bot Versions ==========

@bot_router.get("/bots/{bot_id}/versions", response_model=List[BotVersionResponse])
async def list_bot_versions(
    bot_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    # Check if bot exists and belongs to tenant
    bot_repo = BotRepository(db)
    bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    repo = BotVersionRepository(db)
    return await repo.get_by_bot(bot_id, tenant_id=tenant_id)

@bot_router.post("/bots/{bot_id}/versions", response_model=BotVersionResponse)
async def create_bot_version(
    bot_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    bot_repo = BotRepository(db)
    bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    repo = BotVersionRepository(db)
    versions = await repo.get_by_bot(bot_id, tenant_id=tenant_id)
    next_version = 1
    if versions:
        next_version = max(v.version for v in versions) + 1
        
    new_v = await repo.create({
        "bot_id": bot_id,
        "version": next_version,
        "is_active": False
    }, tenant_id=tenant_id)
    
    # Reload with capabilities to avoid lazy loading error
    stmt = select(BotVersion).where(BotVersion.id == new_v.id).options(selectinload(BotVersion.capabilities_rel))
    res = await db.execute(stmt)
    return res.scalar_one()

@bot_router.patch("/bots/{bot_id}/versions/{version_id}/activate", response_model=BotVersionResponse)
async def activate_bot_version(
    bot_id: str,
    version_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    bot_repo = BotRepository(db)
    bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    repo = BotVersionRepository(db)
    # Deactivate all versions for this bot
    versions = await repo.get_by_bot(bot_id, tenant_id=tenant_id)
    for v in versions:
        if v.is_active:
            await repo.update(v, {"is_active": False})
            
    # Activate selected version
    version = await repo.get(version_id, tenant_id=tenant_id)
    if not version or version.bot_id != bot_id:
        raise HTTPException(status_code=404, detail="Version not found")
        
    await repo.update(version, {"is_active": True})
    
    # Reload with capabilities to avoid lazy loading error
    stmt = select(BotVersion).where(BotVersion.id == version_id).options(selectinload(BotVersion.capabilities_rel))
    res = await db.execute(stmt)
    return res.scalar_one()

# ========== Capabilities ==========

@bot_router.get("/capabilities", response_model=List[CapabilityResponse])
async def list_capabilities(db: AsyncSession = Depends(get_session)):
    """List all available system capabilities"""
    repo = CapabilityRepository(db)
    return await repo.get_multi()

@bot_router.patch("/bots/{bot_id}/versions/{version_id}/capabilities", response_model=BotVersionResponse)
async def update_bot_version_capabilities(
    bot_id: str,
    version_id: str,
    data: CapabilityUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Update capabilities for a specific bot version"""
    capability_codes = data.codes
    bot_repo = BotRepository(db)
    bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    version_repo = BotVersionRepository(db)
    # Re-fetch version with capabilities loaded
    stmt = select(BotVersion).where(BotVersion.id == version_id).options(selectinload(BotVersion.capabilities_rel))
    res = await db.execute(stmt)
    version = res.scalar_one_or_none()
    
    if not version or version.bot_id != bot_id:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Multi-fetch capabilities
    cap_repo = CapabilityRepository(db)
    all_caps = await cap_repo.get_multi()
    selected_caps = [c for c in all_caps if c.code in capability_codes]
    
    version.capabilities_rel = selected_caps
    await db.commit()
    
    # Reload with capabilities to avoid lazy loading error after commit
    stmt = select(BotVersion).where(BotVersion.id == version_id).options(selectinload(BotVersion.capabilities_rel))
    res = await db.execute(stmt)
    return res.scalar_one()
