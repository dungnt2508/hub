"""
Channel Configuration API (BotChannelConfig CRUD)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import ChannelConfigurationRepository, BotVersionRepository
from app.infrastructure.database.models.bot import BotChannelConfig as BotChannelConfigModel, BotVersion, Bot
from app.interfaces.api.dependencies import get_current_tenant_id

channel_config_router = APIRouter(tags=["channel-config"])


class ChannelConfigCreate(BaseModel):
    bot_version_id: str
    channel_code: str
    config: Optional[dict] = None
    is_active: bool = True


class ChannelConfigUpdate(BaseModel):
    config: Optional[dict] = None
    is_active: Optional[bool] = None


async def _verify_bot_version_tenant(db: AsyncSession, bot_version_id: str, tenant_id: str) -> bool:
    """Verify bot_version belongs to tenant via bot"""
    stmt = select(BotVersion).join(Bot).where(
        BotVersion.id == bot_version_id,
        Bot.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _verify_config_tenant(db: AsyncSession, config_id: str, tenant_id: str) -> bool:
    """Verify channel config belongs to tenant via bot_version -> bot"""
    stmt = select(BotChannelConfigModel).join(BotVersion).join(Bot).where(
        BotChannelConfigModel.id == config_id,
        Bot.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


@channel_config_router.get("/channel-configs")
async def list_channel_configs(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    bot_id: Optional[str] = None,
    bot_version_id: Optional[str] = None
):
    """List channel configs. Filter by bot_id (uses active version) or bot_version_id."""
    repo = ChannelConfigurationRepository(db)
    if bot_version_id:
        if not await _verify_bot_version_tenant(db, bot_version_id, tenant_id):
            raise HTTPException(status_code=404, detail="Bot version not found")
        configs = await repo.get_by_bot_version(bot_version_id)
    elif bot_id:
        # Get active version for bot
        bot_version_repo = BotVersionRepository(db)
        version = await bot_version_repo.get_active_version(bot_id, tenant_id=tenant_id)
        if not version:
            return []
        configs = await repo.get_by_bot_version(version.id)
    else:
        raise HTTPException(status_code=400, detail="bot_id or bot_version_id required")
    return [
        {
            "id": c.id,
            "bot_version_id": c.bot_version_id,
            "channel_code": c.channel_code,
            "config": c.config,
            "is_active": c.is_active,
        }
        for c in configs
    ]


@channel_config_router.post("/channel-configs")
async def create_channel_config(
    data: ChannelConfigCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Create or upsert channel config. Tenant isolation via bot_version."""
    if not await _verify_bot_version_tenant(db, data.bot_version_id, tenant_id):
        raise HTTPException(status_code=404, detail="Bot version not found")
    repo = ChannelConfigurationRepository(db)
    existing = await repo.get_by_bot_version_and_channel(data.bot_version_id, data.channel_code)
    if existing:
        updated = await repo.update(existing, {"config": data.config, "is_active": data.is_active})
        return {
            "id": updated.id,
            "bot_version_id": updated.bot_version_id,
            "channel_code": updated.channel_code,
            "config": updated.config,
            "is_active": updated.is_active,
        }
    obj = await repo.create({
        "bot_version_id": data.bot_version_id,
        "channel_code": data.channel_code.upper(),
        "config": data.config,
        "is_active": data.is_active,
    })
    return {
        "id": obj.id,
        "bot_version_id": obj.bot_version_id,
        "channel_code": obj.channel_code,
        "config": obj.config,
        "is_active": obj.is_active,
    }


@channel_config_router.get("/channel-configs/{config_id}")
async def get_channel_config(
    config_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Get channel config by ID. Tenant isolation enforced."""
    if not await _verify_config_tenant(db, config_id, tenant_id):
        raise HTTPException(status_code=404, detail="Channel config not found")
    repo = ChannelConfigurationRepository(db)
    config = await repo.get(config_id, tenant_id=None)  # We verified via join
    if not config:
        raise HTTPException(status_code=404, detail="Channel config not found")
    return {
        "id": config.id,
        "bot_version_id": config.bot_version_id,
        "channel_code": config.channel_code,
        "config": config.config,
        "is_active": config.is_active,
    }


@channel_config_router.put("/channel-configs/{config_id}")
async def update_channel_config(
    config_id: str,
    data: ChannelConfigUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Update channel config. Tenant isolation enforced."""
    if not await _verify_config_tenant(db, config_id, tenant_id):
        raise HTTPException(status_code=404, detail="Channel config not found")
    repo = ChannelConfigurationRepository(db)
    config = await repo.get(config_id, tenant_id=None)
    if not config:
        raise HTTPException(status_code=404, detail="Channel config not found")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return {"id": config.id, "bot_version_id": config.bot_version_id, "channel_code": config.channel_code, "config": config.config, "is_active": config.is_active}
    updated = await repo.update(config, update_data)
    return {
        "id": updated.id,
        "bot_version_id": updated.bot_version_id,
        "channel_code": updated.channel_code,
        "config": updated.config,
        "is_active": updated.is_active,
    }


@channel_config_router.delete("/channel-configs/{config_id}")
async def delete_channel_config(
    config_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Delete channel config. Tenant isolation enforced."""
    if not await _verify_config_tenant(db, config_id, tenant_id):
        raise HTTPException(status_code=404, detail="Channel config not found")
    repo = ChannelConfigurationRepository(db)
    await repo.delete(config_id)
    return {"message": "Deleted"}
