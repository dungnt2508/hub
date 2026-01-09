"""
Database Connection Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.database_connection import DatabaseConnection


class IConnectionRepository(ABC):
    """Interface for database connection repository"""
    
    @abstractmethod
    async def create_connection(self, connection: DatabaseConnection) -> DatabaseConnection:
        """Create new database connection"""
        pass
    
    @abstractmethod
    async def get_connection(
        self,
        connection_id: str,
        include_encrypted: bool = False
    ) -> Optional[DatabaseConnection]:
        """Get connection by ID"""
        pass
    
    @abstractmethod
    async def get_connection_by_name(
        self,
        name: str,
        tenant_id: Optional[str] = None
    ) -> Optional[DatabaseConnection]:
        """Get connection by name"""
        pass
    
    @abstractmethod
    async def list_connections(
        self,
        db_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        include_encrypted: bool = False
    ) -> List[DatabaseConnection]:
        """List connections with filters"""
        pass
    
    @abstractmethod
    async def update_connection(
        self,
        connection_id: str,
        updates: dict
    ) -> Optional[DatabaseConnection]:
        """Update connection"""
        pass
    
    @abstractmethod
    async def delete_connection(self, connection_id: str) -> bool:
        """Delete connection"""
        pass
    
    @abstractmethod
    async def test_connection(self, connection_id: str) -> bool:
        """Test connection"""
        pass

