"""Session Repository Interface - Uses domain entities (Clean Architecture)"""

from typing import Optional, List
from abc import abstractmethod
from app.core.interfaces.repository import IRepository
from app.core.domain.runtime import RuntimeSession, RuntimeTurn, RuntimeContextSlot


class ISessionRepository(IRepository[RuntimeSession]):
    """Interface cho Session Repository"""
    
    @abstractmethod
    async def get_by_bot_and_channel(
        self,
        bot_id: str,
        channel_code: str,
        tenant_id: str
    ) -> List[RuntimeSession]:
        """Lấy session theo bot và channel"""
        pass


class IConversationTurnRepository(IRepository[RuntimeTurn]):
    """Interface cho Conversation Turn Repository"""
    
    @abstractmethod
    async def get_by_session(self, session_id: str, tenant_id: str) -> List[RuntimeTurn]:
        """Lấy lịch sử chat của một session"""
        pass


class IContextSlotRepository(IRepository[RuntimeContextSlot]):
    """Interface cho Context Slot Repository"""
    
    @abstractmethod
    async def get_by_session(self, session_id: str, tenant_id: str) -> List[RuntimeContextSlot]:
        """Lấy các slots của một session"""
        pass

