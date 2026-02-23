from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.decision import RuntimeDecisionEvent as DecisionModel
from app.infrastructure.database.models.decision import RuntimeGuardrailCheck as GuardrailCheckModel

# Domain Entities
from app.core import domain

class DecisionRepository(BaseRepository[DecisionModel]):
    """Decision event repository (Async Implementation) with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(DecisionModel, db)
        self.logger = logging.getLogger(__name__)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.RuntimeDecisionEvent]:
        db_obj = await super().get(id, tenant_id)
        return domain.RuntimeDecisionEvent.model_validate(db_obj) if db_obj else None

    async def get_by_session(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50
    ) -> List[domain.RuntimeDecisionEvent]:
        """Get all decisions for a session with tenant isolation check"""
        from app.infrastructure.database.models.runtime import RuntimeSession
        stmt = select(DecisionModel).join(RuntimeSession).where(
            DecisionModel.session_id == session_id,
            RuntimeSession.tenant_id == tenant_id
        ).order_by(DecisionModel.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        objs = result.scalars().all()
        
        domain_objs = []
        for obj in objs:
            try:
                domain_objs.append(domain.RuntimeDecisionEvent.model_validate(obj))
            except Exception as e:
                self.logger.error(f"Validation error for DecisionEvent {obj.id}: {str(e)}")
                # Continue and return what we can
                
        return domain_objs


class DecisionGuardrailCheckedRepository(BaseRepository[GuardrailCheckModel]):
    """Decision guardrail check repository (Async Implementation) with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(GuardrailCheckModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.RuntimeGuardrailCheck]:
        db_obj = await super().get(id, tenant_id)
        return domain.RuntimeGuardrailCheck.model_validate(db_obj) if db_obj else None
