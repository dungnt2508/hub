from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import KnowledgeDomain as DomainModel

# Domain Entities
from app.core import domain
from app.core.interfaces.knowledge_repo import IKnowledgeDomainRepository


class KnowledgeDomainRepository(BaseRepository[DomainModel]):
    """Knowledge Domain repository with mapping support"""
    domain_container = domain.KnowledgeDomain

    def __init__(self, db: AsyncSession):
        super().__init__(DomainModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.KnowledgeDomain]:
        db_obj = await super().get(id, tenant_id)
        return self._to_domain(db_obj)

    async def get_by_code(self, code: str) -> Optional[domain.KnowledgeDomain]:
        """Lấy domain theo code (Global scope)"""
        stmt = select(DomainModel).where(DomainModel.code == code)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.KnowledgeDomain.model_validate(db_obj) if db_obj else None
