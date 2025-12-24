"""
Notification Service Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class INotificationService(ABC):
    """Interface for notification service"""
    
    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Send notification"""
        pass

