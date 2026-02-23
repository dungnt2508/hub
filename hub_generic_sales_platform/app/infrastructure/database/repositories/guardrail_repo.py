from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.policy import TenantGuardrail as GuardrailModel

# Domain Entities
from app.core import domain

class GuardrailRepository(BaseRepository[GuardrailModel]):
    """Guardrail repository (Async) with Domain Mapping"""
    domain_container = domain.TenantGuardrail

    def __init__(self, db: AsyncSession):
        super().__init__(GuardrailModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantGuardrail]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantGuardrail.model_validate(db_obj) if db_obj else None

    async def get_active_for_tenant(self, tenant_id: str) -> List[domain.TenantGuardrail]:
        """Get all active guardrails for a tenant, ordered by priority"""
        stmt = select(GuardrailModel).where(
            GuardrailModel.tenant_id == tenant_id,
            GuardrailModel.is_active == True
        ).order_by(GuardrailModel.priority.desc())
        result = await self.db.execute(stmt)
        return [domain.TenantGuardrail.model_validate(obj) for obj in result.scalars().all()]
