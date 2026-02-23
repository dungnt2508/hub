from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import BotComparison as ComparisonModel

# Domain Entities
from app.core import domain


class ComparisonRepository(BaseRepository[ComparisonModel]):
    """Comparison repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ComparisonModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.BotComparison]:
        db_obj = await super().get(id, tenant_id)
        return domain.BotComparison.model_validate(db_obj) if db_obj else None

    async def get_active(self, tenant_id: str, bot_id: Optional[str] = None) -> List[domain.BotComparison]:
        """Get all active comparisons for a tenant/bot"""
        stmt = select(ComparisonModel).where(
            ComparisonModel.tenant_id == tenant_id,
            ComparisonModel.is_active == True
        )
        if bot_id:
            stmt = stmt.where(ComparisonModel.bot_id == bot_id)
        result = await self.db.execute(stmt)
        return [domain.BotComparison.model_validate(obj) for obj in result.scalars().all()]
    
    async def get_by_offerings(
        self,
        tenant_id: str,
        offering_ids: List[str]
    ) -> List[domain.BotComparison]:
        """Get comparisons containing specific offerings"""
        stmt = select(ComparisonModel).where(
            ComparisonModel.tenant_id == tenant_id,
            ComparisonModel.is_active == True,
            ComparisonModel.offering_ids.contains(offering_ids)
        )
        result = await self.db.execute(stmt)
        return [domain.BotComparison.model_validate(obj) for obj in result.scalars().all()]
