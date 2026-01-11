"""
Database Connection Registry Service
"""
from typing import Optional, List, Tuple, Dict, Any
from ..ports.connection_repository import IConnectionRepository
from ..adapters.connection_repository import PostgreSQLConnectionRepository
from ..entities.database_connection import DatabaseConnection, DatabaseType
from ....shared.logger import logger


class ConnectionRegistry:
    """Service for managing database connections"""
    
    def __init__(self, repository: Optional[IConnectionRepository] = None):
        """
        Initialize connection registry.
        
        Args:
            repository: Connection repository (defaults to PostgreSQLConnectionRepository)
        """
        self.repository = repository or PostgreSQLConnectionRepository()
    
    async def get_connection_string(
        self,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get decrypted connection string by name or ID.
        
        Args:
            connection_name: Connection name
            connection_id: Connection ID
            tenant_id: Tenant ID (optional)
            
        Returns:
            Decrypted connection string or None
        """
        try:
            if connection_id:
                connection = await self.repository.get_connection(
                    connection_id,
                    include_encrypted=True
                )
            elif connection_name:
                connection = await self.repository.get_connection_by_name(
                    connection_name,
                    tenant_id
                )
                if connection:
                    # Need to get with encrypted string
                    connection = await self.repository.get_connection(
                        connection.connection_id,
                        include_encrypted=True
                    )
            else:
                return None
            
            if connection:
                return connection.get_decrypted_connection_string()
            
            return None
        except Exception as e:
            logger.error(f"Error getting connection string: {e}", exc_info=True)
            return None
    
    async def list_connections(
        self,
        db_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DatabaseConnection]:
        """List connections with filters"""
        return await self.repository.list_connections(
            db_type=db_type,
            tenant_id=tenant_id,
            environment=environment,
            status=status,
            include_encrypted=False  # Don't expose encrypted strings
        )
    
    async def create_connection(
        self,
        name: str,
        db_type: str,
        connection_string: str,
        description: Optional[str] = None,
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> DatabaseConnection:
        """Create new connection"""
        # Encrypt connection string
        encrypted_string = DatabaseConnection.encrypt_connection_string(connection_string)
        
        # Convert db_type string to enum
        db_type_enum = DatabaseType(db_type.lower()) if isinstance(db_type, str) else db_type
        
        connection = DatabaseConnection(
            name=name,
            db_type=db_type_enum,
            connection_string=encrypted_string,
            description=description,
            environment=environment,
            tags=tags,
            created_by=created_by,
            tenant_id=tenant_id
        )
        
        return await self.repository.create_connection(connection)
    
    async def update_connection(
        self,
        connection_id: str,
        **updates
    ) -> Optional[DatabaseConnection]:
        """Update connection"""
        # If connection_string is provided, encrypt it
        if "connection_string" in updates:
            updates["connection_string"] = DatabaseConnection.encrypt_connection_string(
                updates["connection_string"]
            )
        
        # If db_type is provided as string, convert to enum
        if "db_type" in updates and isinstance(updates["db_type"], str):
            updates["db_type"] = DatabaseType(updates["db_type"].lower())
        
        return await self.repository.update_connection(connection_id, updates)
    
    async def delete_connection(self, connection_id: str) -> bool:
        """Delete connection"""
        return await self.repository.delete_connection(connection_id)
    
    async def test_connection(self, connection_id: str) -> bool:
        """Test connection"""
        return await self.repository.test_connection(connection_id)
    
    async def test_connection_string(
        self,
        db_type: str,
        connection_string: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Test connection string directly without saving to database.
        
        Returns:
            (success, error_message, connection_info)
        """
        try:
            from ..adapters.mcp_db_client import MCPDBClient
            from ..ports.mcp_client import DatabaseType
            
            mcp_client = MCPDBClient()
            db_type_enum = DatabaseType(db_type.lower())
            
            # Test connection
            try:
                connection_info = await mcp_client.get_connection_info(
                    db_type=db_type_enum,
                    connection_string=connection_string
                )
                
                # Check if connection_info contains error
                if isinstance(connection_info, dict) and "error" in connection_info:
                    error_msg = connection_info.get("error", {}).get("message", "Connection test failed")
                    return (False, error_msg, None)
                
                return (True, None, connection_info)
            except Exception as e:
                error_msg = str(e)
                # Extract more detailed error message if available
                if hasattr(e, 'args') and e.args:
                    error_msg = str(e.args[0]) if e.args else str(e)
                
                # Log as warning instead of error since connection test failures are expected
                logger.warning(f"Connection test failed: {error_msg}")
                return (False, error_msg, None)
        except Exception as e:
            error_msg = f"Failed to test connection: {str(e)}"
            logger.warning(f"Connection test error: {error_msg}")
            return (False, error_msg, None)


# Global registry instance
connection_registry = ConnectionRegistry()

