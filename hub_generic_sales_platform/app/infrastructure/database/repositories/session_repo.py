from typing import Optional, List, Any
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository
from app.core.shared.exceptions import ConcurrentUpdateError

# Infrastructure Models
from app.infrastructure.database.models.runtime import RuntimeSession as SessionModel
from app.infrastructure.database.models.runtime import RuntimeTurn as TurnModel
from app.infrastructure.database.models.runtime import RuntimeContextSlot as SlotModel

# Domain Entities
from app.core import domain
from app.core.interfaces.session_repo import ISessionRepository, IConversationTurnRepository, IContextSlotRepository


class SessionRepository(BaseRepository[SessionModel], ISessionRepository):
    """Conversation session repository (Async Implementation) with Domain Mapping"""
    domain_container = domain.RuntimeSession

    def __init__(self, db: AsyncSession):
        super().__init__(SessionModel, db)
    
    async def get_by_bot_and_channel(
        self,
        bot_id: str,
        channel_code: str,
        tenant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[domain.RuntimeSession]:
        """Get recent sessions by bot and channel with mandatory tenant isolation"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(SessionModel).where(
            SessionModel.bot_id == bot_id,
            SessionModel.channel_code == channel_code,
            SessionModel.tenant_id == tenant_id,
        ).order_by(SessionModel.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def update(
        self,
        db_obj: Any,
        obj_in: dict,
        tenant_id: Optional[str] = None
    ) -> domain.RuntimeSession:
        """Update session with optimistic locking"""
        # Get current version and ID
        current_version = getattr(db_obj, "version", 0)
        id_val = getattr(db_obj, "id")

        # Increment version
        obj_in["version"] = current_version + 1

        # Atomic update with version check
        stmt = sa_update(SessionModel).where(
            SessionModel.id == id_val,
            SessionModel.version == current_version
        ).values(**obj_in)

        if tenant_id:
            stmt = stmt.where(SessionModel.tenant_id == tenant_id)

        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise ConcurrentUpdateError("RuntimeSession", id_val)

        # Refresh and return
        res = await self.db.execute(select(SessionModel).where(SessionModel.id == id_val))
        updated_db_obj = res.scalar_one()
        await self.db.refresh(updated_db_obj)
        return self._to_domain(updated_db_obj)
    
    async def get_active_sessions(
        self,
        tenant_id: str,
        bot_id: Optional[str] = None
    ) -> List[domain.RuntimeSession]:
        """Get active (not closed) sessions"""
        stmt = select(SessionModel).where(
            SessionModel.tenant_id == tenant_id,
            SessionModel.lifecycle_state != "closed"
        )
        
        if bot_id:
            stmt = stmt.where(SessionModel.bot_id == bot_id)
        
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def list_for_logs(
        self,
        tenant_id: str,
        bot_id: Optional[str] = None,
        channel_code: Optional[str] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[domain.RuntimeSession]:
        """List sessions for logs/monitor. active_only=True => flow_step != CLOSED."""
        stmt = select(SessionModel).where(
            SessionModel.tenant_id == tenant_id
        )
        if bot_id:
            stmt = stmt.where(SessionModel.bot_id == bot_id)
        if channel_code:
            stmt = stmt.where(SessionModel.channel_code == channel_code)
        if active_only:
            stmt = stmt.where(SessionModel.lifecycle_state != "closed")
        stmt = stmt.order_by(SessionModel.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]


class ConversationTurnRepository(BaseRepository[TurnModel], IConversationTurnRepository):
    """Conversation turn repository (Async Implementation) with Domain Mapping"""
    domain_container = domain.RuntimeTurn

    def __init__(self, db: AsyncSession):
        super().__init__(TurnModel, db)
    
    async def get_by_session(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50
    ) -> List[domain.RuntimeTurn]:
        """Get all turns for a session with tenant isolation check"""
        stmt = select(TurnModel).join(SessionModel).where(
            TurnModel.session_id == session_id,
            SessionModel.tenant_id == tenant_id
        ).order_by(TurnModel.created_at.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]


class ContextSlotRepository(BaseRepository[SlotModel], IContextSlotRepository):
    """Context slot repository (Async Implementation) with Domain Mapping"""
    domain_container = domain.RuntimeContextSlot

    def __init__(self, db: AsyncSession):
        super().__init__(SlotModel, db)
    
    async def get_by_session(self, session_id: str, tenant_id: str) -> List[domain.RuntimeContextSlot]:
        """Get all active context slots for a session with tenant isolation check"""
        stmt = select(SlotModel).join(SessionModel).where(
            SlotModel.session_id == session_id,
            SlotModel.status == "active",
            SessionModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def get_by_key(
        self, session_id: str, key: str, tenant_id: str
    ) -> Optional[domain.RuntimeContextSlot]:
        """Get context slot by session and key with tenant isolation"""
        stmt = (
            select(SlotModel)
            .join(SessionModel, SlotModel.session_id == SessionModel.id)
            .where(
                SlotModel.session_id == session_id,
                SlotModel.key == key,
                SlotModel.status == "active",
                SessionModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return self._to_domain(db_obj)

    async def deactivate_by_keys(
        self, session_id: str, keys: List[str], tenant_id: str
    ) -> int:
        """Deactivate slots với keys chỉ định (để overwrite khi search mới). Tenant isolation enforced."""
        if not keys:
            return 0
        # Subquery: only update when session exists and belongs to tenant
        subq = select(SessionModel.id).where(
            SessionModel.id == session_id,
            SessionModel.tenant_id == tenant_id
        ).scalar_subquery()
        stmt = (
            sa_update(SlotModel)
            .where(SlotModel.session_id == session_id)
            .where(SlotModel.key.in_(keys))
            .where(SlotModel.session_id == subq)
            .values(status="overridden")
        )
        result = await self.db.execute(stmt)
        return result.rowcount
