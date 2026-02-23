from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import (
    DomainAttributeDefinition as AttributeDefModel,
    TenantAttributeConfig as AttributeConfigModel
)

# Domain Entities
from app.core import domain


class DomainAttributeDefinitionRepository(BaseRepository[AttributeDefModel]):
    """Domain Attribute Definition repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AttributeDefModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.DomainAttributeDefinition]:
        db_obj = await super().get(id, tenant_id)
        return domain.DomainAttributeDefinition.model_validate(db_obj) if db_obj else None

    async def get_by_domain(self, domain_id: str) -> List[domain.DomainAttributeDefinition]:
        stmt = select(AttributeDefModel).where(AttributeDefModel.domain_id == domain_id)
        result = await self.db.execute(stmt)
        return [domain.DomainAttributeDefinition.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_key(self, key: str, domain_id: Optional[str] = None) -> Optional[domain.DomainAttributeDefinition]:
        stmt = select(AttributeDefModel).where(AttributeDefModel.key == key)
        if domain_id:
            stmt = stmt.where(AttributeDefModel.domain_id == domain_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.DomainAttributeDefinition.model_validate(db_obj) if db_obj else None


class TenantAttributeConfigRepository(BaseRepository[AttributeConfigModel]):
    """Tenant Attribute Config repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AttributeConfigModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantAttributeConfig]:
        stmt = select(AttributeConfigModel).options(selectinload(AttributeConfigModel.definition)).where(AttributeConfigModel.id == id)
        if tenant_id:
            stmt = stmt.where(AttributeConfigModel.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantAttributeConfig.model_validate(db_obj) if db_obj else None

    async def get_config(self, tenant_id: str, attribute_def_id: str) -> Optional[domain.TenantAttributeConfig]:
        stmt = select(AttributeConfigModel).options(selectinload(AttributeConfigModel.definition)).where(
            AttributeConfigModel.tenant_id == tenant_id,
            AttributeConfigModel.attribute_def_id == attribute_def_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantAttributeConfig.model_validate(db_obj) if db_obj else None

    async def get_all_for_tenant(self, tenant_id: str, domain_id: Optional[str] = None) -> List[domain.TenantAttributeConfig]:
        stmt = select(AttributeConfigModel).options(selectinload(AttributeConfigModel.definition)).where(AttributeConfigModel.tenant_id == tenant_id)
        if domain_id:
            # Join with definition to filter by domain
            stmt = stmt.join(AttributeConfigModel.definition).where(AttributeDefModel.domain_id == domain_id)
        
        result = await self.db.execute(stmt)
        return [domain.TenantAttributeConfig.model_validate(obj) for obj in result.scalars().all()]
