from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.tenant import Tenant as TenantModel
from app.infrastructure.database.models.tenant import UserAccount as UserModel

# Domain Entities
from app.core import domain

class TenantRepository(BaseRepository[TenantModel]):
    """Tenant repository (Async) with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(TenantModel, db)
    
    async def get(self, id: str, tenant_id: str) -> Optional[domain.Tenant]:
        db_obj = await super().get(id, tenant_id)
        return domain.Tenant.model_validate(db_obj) if db_obj else None
    
    async def get_active_tenants(self) -> List[domain.Tenant]:
        """Get all active tenants"""
        stmt = select(TenantModel).where(TenantModel.status == "active")
        result = await self.db.execute(stmt)
        return [domain.Tenant.model_validate(obj) for obj in result.scalars().all()]


class UserAccountRepository(BaseRepository[UserModel]):
    """User account repository (Async) with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UserModel, db)
    
    async def get(self, id: str, tenant_id: str) -> Optional[domain.UserAccount]:
        """Get user by ID with mandatory tenant isolation"""
        stmt = select(UserModel).options(selectinload(UserModel.tenant)).where(
            UserModel.id == id,
            UserModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.UserAccount.model_validate(db_obj) if db_obj else None
    
    async def get_by_email(self, email: str, tenant_id: str) -> Optional[domain.UserAccount]:
        """Get user by email with mandatory tenant isolation"""
        stmt = select(UserModel).options(selectinload(UserModel.tenant)).where(
            UserModel.email == email,
            UserModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        return domain.UserAccount.model_validate(db_obj) if db_obj else None

    async def get_by_email_system(self, email: str) -> Optional[domain.UserAccount]:
        """SYSTEM-LEVEL: Get user by email across all tenants (specifically for login)"""
        stmt = select(UserModel).options(selectinload(UserModel.tenant)).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        return domain.UserAccount.model_validate(db_obj) if db_obj else None
    
    async def get_by_tenant(self, tenant_id: str) -> List[domain.UserAccount]:
        """Get all users for a tenant"""
        stmt = select(UserModel).where(UserModel.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return [domain.UserAccount.model_validate(obj) for obj in result.scalars().all()]
