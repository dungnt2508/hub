"""
HR Domain Ports (Interfaces)
"""

from .repository import IHRRepository
from .notification import INotificationService

__all__ = ["IHRRepository", "INotificationService"]

