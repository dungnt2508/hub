from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import SessionRepository
from app.core import domain
from app.core.domain.state_machine import StateMachine
from datetime import datetime, timezone


class SessionStateHandler:
    """Handler for session state operations (Bước 2, 8) - 100% Async"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
    
    async def read_session_state(self, session_id: str, tenant_id: str) -> Optional[domain.RuntimeSession]:
        """
        Đọc trạng thái session hiện tại (Bước 2)
        """
        return await self.session_repo.get(session_id, tenant_id=tenant_id)
    
    async def update_flow_step(self, *args, **kwargs):
        """Compatibility alias for tests"""
        return await self.update_lifecycle_state(*args, **kwargs)

    async def update_lifecycle_state(
        self,
        session_id: str,
        new_state: Any,
        tenant_id: str
    ) -> Optional[domain.RuntimeSession]:
        """
        Cập nhật trạng thái flow (Bước 8)
        """
        session = await self.session_repo.get(session_id, tenant_id=tenant_id)
        if not session:
            return None
            
        current_state = session.lifecycle_state
        target_state = new_state.value if hasattr(new_state, 'value') else str(new_state)
        
        # Validate Transition
        if current_state != target_state and current_state:
            # Only validate if state is changing and current state exists
            if not StateMachine.is_transition_valid(current_state, target_state):
                 raise ValueError(f"Invalid state transition from {current_state} to {target_state}")
        
        updated_data = {
            "lifecycle_state": target_state,
            "state_updated_at": datetime.now(timezone.utc)
        }
        
        return await self.session_repo.update(session, updated_data, tenant_id=tenant_id)
