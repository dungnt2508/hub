from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Import Infrastructure Models
from app.infrastructure.database.models.bot import Bot as BotModel
from app.infrastructure.database.models.bot import BotVersion as BotVersionModel
from app.infrastructure.database.models.bot import SystemCapability as SystemCapabilityModel
from app.infrastructure.database.models.bot import BotChannelConfig as BotChannelConfigModel

# Import Domain Entities
from app.core import domain
from app.core.interfaces.bot_repo import IBotRepository, IBotVersionRepository


class BotRepository(BaseRepository[BotModel], IBotRepository):
    """Bot repository (Async Implementation) with Domain Mapping"""
    domain_container = domain.Bot
    
    def __init__(self, db: AsyncSession):
        super().__init__(BotModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.Bot]:
        """Get bot and map to domain entity with mandatory tenant isolation"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(BotModel).where(
            and_(BotModel.id == id, BotModel.tenant_id == tenant_id)
        ).options(
            selectinload(BotModel.versions).selectinload(BotVersionModel.capabilities_rel),
            joinedload(BotModel.domain_rel)
        )
        
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        return self._to_domain(db_obj)

    async def get_multi(self, tenant_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[domain.Bot]:
        """Get multiple bots and map to domain entities with mandatory tenant isolation"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(BotModel).where(BotModel.tenant_id == tenant_id).options(
            selectinload(BotModel.versions).selectinload(BotVersionModel.capabilities_rel),
            joinedload(BotModel.domain_rel)
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        
        return [self._to_domain(obj) for obj in result.scalars().all()]
# ... (rest of the file)

    async def get_by_code(self, code: str, tenant_id: str) -> Optional[domain.Bot]:
        """Lấy bot theo code và tenant với mapping domain"""
        stmt = select(BotModel).where(BotModel.code == code, BotModel.tenant_id == tenant_id).options(
            selectinload(BotModel.versions).selectinload(BotVersionModel.capabilities_rel),
            joinedload(BotModel.domain_rel)
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        return domain.Bot.model_validate(db_obj) if db_obj else None
    
    async def get_active_bots(self, tenant_id: str) -> List[domain.Bot]:
        """Lấy tất cả bot đang hoạt động với mapping domain (giống get_multi)"""
        stmt = select(BotModel).where(BotModel.tenant_id == tenant_id, BotModel.status == "active").options(
            selectinload(BotModel.versions).selectinload(BotVersionModel.capabilities_rel),
            joinedload(BotModel.domain_rel)
        )
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.unique().scalars().all()]

    async def get_active_bot_by_offering(self, offering_id: str, tenant_id: str) -> Optional[domain.Bot]:
        """Tìm Bot đang quản lý offering này."""
        from app.infrastructure.database.models.offering import TenantOffering as OfferingModel
        stmt = select(BotModel).join(OfferingModel, BotModel.id == OfferingModel.bot_id).where(
            OfferingModel.id == offering_id,
            OfferingModel.tenant_id == tenant_id,
            BotModel.status == "active"
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        return domain.Bot.model_validate(db_obj) if db_obj else None


class BotVersionRepository(BaseRepository[BotVersionModel], IBotVersionRepository):
    """Bot version repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BotVersionModel, db)
    
    async def get_by_bot_and_version(self, bot_id: str, version: int) -> Optional[domain.BotVersion]:
        stmt = select(BotVersionModel).where(BotVersionModel.bot_id == bot_id, BotVersionModel.version == version)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        return domain.BotVersion.model_validate(db_obj) if db_obj else None
    
    async def get_active_version(self, bot_id: str, tenant_id: Optional[str] = None) -> Optional[domain.BotVersion]:
        stmt = select(BotVersionModel).join(BotModel).where(
            BotVersionModel.bot_id == bot_id, 
            BotVersionModel.is_active == True
        )
        
        if tenant_id:
            stmt = stmt.where(BotModel.tenant_id == tenant_id)
            
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        return domain.BotVersion.model_validate(db_obj) if db_obj else None
    
    async def get_by_bot(self, bot_id: str, tenant_id: Optional[str] = None) -> List[domain.BotVersion]:
        stmt = select(BotVersionModel).join(BotModel).where(
            BotVersionModel.bot_id == bot_id
        )
        
        if tenant_id:
            stmt = stmt.where(BotModel.tenant_id == tenant_id)
            
        stmt = stmt.options(
            selectinload(BotVersionModel.capabilities_rel)
        ).order_by(BotVersionModel.version.desc())
        
        result = await self.db.execute(stmt)
        
        return [domain.BotVersion.model_validate(obj) for obj in result.scalars().all()]


class CapabilityRepository(BaseRepository[SystemCapabilityModel]):
    """Capability repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(SystemCapabilityModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.SystemCapability]:
        db_obj = await super().get(id, tenant_id)
        return domain.SystemCapability.model_validate(db_obj) if db_obj else None

    async def get_by_code(self, code: str) -> Optional[domain.SystemCapability]:
        """Get capability by code"""
        stmt = select(SystemCapabilityModel).where(SystemCapabilityModel.code == code)
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        return domain.SystemCapability.model_validate(db_obj) if db_obj else None


class ChannelConfigurationRepository(BaseRepository[BotChannelConfigModel]):
    """Channel configuration repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BotChannelConfigModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.BotChannelConfig]:
        db_obj = await super().get(id, tenant_id)
        return domain.BotChannelConfig.model_validate(db_obj) if db_obj else None

    async def get_by_bot_version_and_channel(
        self,
        bot_version_id: str,
        channel_code: str
    ) -> Optional[domain.BotChannelConfig]:
        """Get channel config by bot version and channel code"""
        stmt = select(BotChannelConfigModel).where(
            BotChannelConfigModel.bot_version_id == bot_version_id,
            BotChannelConfigModel.channel_code == channel_code
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        return domain.BotChannelConfig.model_validate(db_obj) if db_obj else None
    
    async def get_by_bot_version(self, bot_version_id: str, active_only: bool = False) -> List[domain.BotChannelConfig]:
        """Get all channel configs for a bot version"""
        stmt = select(BotChannelConfigModel).where(
            BotChannelConfigModel.bot_version_id == bot_version_id
        )
        if active_only:
            stmt = stmt.where(BotChannelConfigModel.is_active == True)
        result = await self.db.execute(stmt)
        return [domain.BotChannelConfig.model_validate(obj) for obj in result.scalars().all()]
