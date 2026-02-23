from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import and_, select, update, delete, Column, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr
from app.core.interfaces.repository import IRepository


class TimestampMixin:
    """Mixin for created_at and updated_at columns"""
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, default=func.now(), onupdate=func.now())


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass


ModelType = TypeVar("ModelType", bound=Base)
DomainType = TypeVar("DomainType")


class BaseRepository(Generic[ModelType], IRepository[ModelType]):
    """Base repository with tenant isolation and Domain Mapping support"""
    
    # Subclasses should set this to the Pydantic domain model class
    domain_container: Optional[Type[Any]] = None

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    def _to_domain(self, db_obj: Any) -> Any:
        """Helper to map DB model to domain entity if domain_container is set"""
        if db_obj is None:
            return None
        if self.domain_container:
            return self.domain_container.model_validate(db_obj)
        return db_obj

    async def get(self, id: str, tenant_id: Optional[str] = None) -> Any:
        """Get by ID with mandatory tenant isolation for multi-tenant models"""
        if hasattr(self.model, 'tenant_id'):
            if not tenant_id:
                raise ValueError(f"tenant_id is required for {self.model.__name__}")
            stmt = select(self.model).where(
                and_(self.model.id == id, self.model.tenant_id == tenant_id)
            )
        else:
            stmt = select(self.model).where(self.model.id == id)
        
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return self._to_domain(db_obj)
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        **filters
    ) -> List[Any]:
        """Get multiple records with mandatory tenant isolation for multi-tenant models"""
        stmt = select(self.model).offset(skip).limit(limit)
        
        if hasattr(self.model, 'tenant_id'):
            if not tenant_id:
                raise ValueError(f"tenant_id is required for {self.model.__name__}")
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def create(self, obj_in: dict, tenant_id: Optional[str] = None) -> Any:
        """
        Create new record.
        WARNING: This no longer commits automatically. Caller must manage transaction.
        """
        if hasattr(self.model, 'tenant_id'):
            if not tenant_id:
                raise ValueError(f"tenant_id is required for {self.model.__name__}")
            obj_in['tenant_id'] = tenant_id
        
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return self._to_domain(db_obj)
    
    async def update(
        self,
        db_obj: Any,
        obj_in: dict,
        tenant_id: Optional[str] = None
    ) -> Any:
        """Update record. Handles both SQLAlchemy model and Domain entity as input."""
        # Check if db_obj is a domain entity (not a SQLAlchemy model)
        if hasattr(db_obj, "id") and not isinstance(db_obj, Base):
            # It's likely a Pydantic model, we need the actual DB object
            actual_db_obj = await self.db.get(self.model, db_obj.id)
            if not actual_db_obj:
                raise ValueError(f"Object with id {db_obj.id} not found for update")
            db_obj = actual_db_obj

        if tenant_id and hasattr(self.model, 'tenant_id'):
            if db_obj.tenant_id != tenant_id:
                raise ValueError("Tenant ID mismatch")
        
        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        await self.db.flush()
        await self.db.refresh(db_obj)
        return self._to_domain(db_obj)
    
    async def delete(
        self,
        id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Any]:
        """Delete record with mandatory tenant isolation for multi-tenant models"""
        stmt = select(self.model).where(self.model.id == id)
        
        if hasattr(self.model, 'tenant_id'):
            if not tenant_id:
                raise ValueError(f"tenant_id is required for {self.model.__name__}")
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if not db_obj:
            return None
        
        # Keep a copy of domain version for return
        domain_obj = self._to_domain(db_obj)

        await self.db.delete(db_obj)
        await self.db.commit()
        return domain_obj
