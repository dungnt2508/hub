from typing import Optional, List
from abc import abstractmethod
from app.core.interfaces.repository import IRepository
from app.core.domain.bot import Bot, BotVersion


class IBotRepository(IRepository[Bot]):
    """Interface cho Bot Repository"""
    
    @abstractmethod
    async def get_by_code(self, code: str, tenant_id: str) -> Optional[Bot]:
        """Lấy bot theo code và tenant"""
        pass
    
    @abstractmethod
    async def get_active_bots(self, tenant_id: str) -> List[Bot]:
        """Lấy tất cả bot đang hoạt động của mỗi tenant"""
        pass


class IBotVersionRepository(IRepository[BotVersion]):
    """Interface cho Bot Version Repository"""
    
    @abstractmethod
    async def get_active_version(self, bot_id: str, tenant_id: Optional[str] = None) -> Optional[BotVersion]:
        """Lấy version đang hoạt động của bot"""
        pass
