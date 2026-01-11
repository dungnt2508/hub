"""
MCP DB Client Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class IMCPDBClient(ABC):
    """Interface for MCP DB Client"""
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        connection_id: Optional[str] = None,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        db_type: Optional[str] = None,
        timeout_seconds: int = 300,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query on specified database.
        
        Args:
            query: SQL query to execute
            connection_id: Connection ID from registry (optional)
            connection_string: Database connection string (optional, may use default)
            connection_name: Connection name from registry (optional)
            db_type: Database type (optional, inferred from connection)
            timeout_seconds: Query timeout in seconds (default: 300)
            params: Query parameters (optional)
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            ExternalServiceError: If query execution fails
        """
        pass
    
    @abstractmethod
    async def get_slow_queries(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 10,
        min_duration_ms: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get slow queries from database.
        
        Args:
            db_type: Database type
            connection_string: Database connection string (optional, can use connection_name/id instead)
            connection_name: Connection name from registry (optional)
            connection_id: Connection ID from registry (optional)
            tenant_id: Tenant ID for connection lookup (optional)
            limit: Maximum number of queries to return
            min_duration_ms: Minimum duration in milliseconds to consider as slow
            
        Returns:
            List of slow query dictionaries
        """
        pass
    
    @abstractmethod
    async def get_wait_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get wait statistics from database.
        
        Args:
            db_type: Database type
            connection_string: Database connection string
            
        Returns:
            Dictionary with wait statistics
        """
        pass
    
    @abstractmethod
    async def get_index_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get index statistics from database.
        
        Args:
            db_type: Database type
            connection_string: Database connection string (optional)
            connection_name: Connection name from registry (optional)
            connection_id: Connection ID from registry (optional)
            tenant_id: Tenant ID for connection lookup (optional)
            schema: Schema name (optional)
            
        Returns:
            List of index statistics dictionaries
        """
        pass
    
    @abstractmethod
    async def detect_blocking(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect blocking sessions in database.
        
        Args:
            db_type: Database type
            connection_string: Database connection string (optional)
            connection_name: Connection name from registry (optional)
            connection_id: Connection ID from registry (optional)
            tenant_id: Tenant ID for connection lookup (optional)
            
        Returns:
            List of blocking session dictionaries
        """
        pass
    
    @abstractmethod
    async def get_connection_info(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get database connection information.
        
        Args:
            db_type: Database type
            connection_string: Database connection string
            
        Returns:
            Dictionary with connection information
        """
        pass

