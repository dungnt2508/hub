"""Base repository with tenant isolation"""
from typing import TypeVar, Generic, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with tenant isolation"""
    
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class
    
    async def get_by_id(
        self, 
        id: UUID, 
        tenant_id: UUID,
        raise_if_not_found: bool = False
    ) -> Optional[T]:
        """Get entity by ID with tenant isolation"""
        stmt = select(self.model_class).where(
            and_(
                self.model_class.id == id,
                self.model_class.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if raise_if_not_found and entity is None:
            raise ValueError(f"{self.model_class.__name__} not found")
        
        return entity
    
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[T]:
        """List entities by tenant"""
        stmt = select(self.model_class).where(
            self.model_class.tenant_id == tenant_id
        )
        
        if limit:
            stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
