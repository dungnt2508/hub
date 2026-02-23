from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import BotUseCase as UseCaseModel

# Domain Entities
from app.core import domain


class UseCaseRepository(BaseRepository[UseCaseModel]):
    """Use case repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UseCaseModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.BotUseCase]:
        db_obj = await super().get(id, tenant_id)
        return domain.BotUseCase.model_validate(db_obj) if db_obj else None

    async def get_by_offering(self, offering_id: str, tenant_id: str) -> List[domain.BotUseCase]:
        """Get all use cases for an offering"""
        stmt = select(UseCaseModel).where(
            UseCaseModel.offering_id == offering_id,
            UseCaseModel.tenant_id == tenant_id,
            UseCaseModel.is_active == True
        ).order_by(UseCaseModel.priority.desc())
        result = await self.db.execute(stmt)
        return [domain.BotUseCase.model_validate(obj) for obj in result.scalars().all()]
    
    async def get_active(self, tenant_id: str, bot_id: Optional[str] = None) -> List[domain.BotUseCase]:
        """Get all active use cases for a tenant/bot"""
        stmt = select(UseCaseModel).where(
            UseCaseModel.tenant_id == tenant_id,
            UseCaseModel.is_active == True
        )
        if bot_id:
            stmt = stmt.where(UseCaseModel.bot_id == bot_id)
        stmt = stmt.order_by(UseCaseModel.priority.desc())
        result = await self.db.execute(stmt)
        return [domain.BotUseCase.model_validate(obj) for obj in result.scalars().all()]
