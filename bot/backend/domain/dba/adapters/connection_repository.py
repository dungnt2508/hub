"""
Database Connection Repository Implementation
"""
from typing import Optional, List
from datetime import datetime
import uuid

from ....infrastructure.database_client import database_client
from ....shared.logger import logger
from ....shared.exceptions import DomainError
from ..ports.connection_repository import IConnectionRepository
from ..entities.database_connection import DatabaseConnection


class PostgreSQLConnectionRepository(IConnectionRepository):
    """PostgreSQL implementation of connection repository"""
    
    async def create_connection(self, connection: DatabaseConnection) -> DatabaseConnection:
        """Create new database connection"""
        pool = database_client.pool
        
        # Generate connection_id if not provided
        if not connection.connection_id:
            connection.connection_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO dba_connections (
                connection_id, name, db_type, connection_string,
                description, environment, tags, status,
                created_by, tenant_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING connection_id, created_at, updated_at
        """
        
        try:
            async with pool.acquire() as conn:
                # Handle db_type - could be enum or string due to use_enum_values=True
                db_type_value = connection.db_type.value if hasattr(connection.db_type, 'value') else connection.db_type
                status_value = connection.status.value if hasattr(connection.status, 'value') else connection.status
                
                row = await conn.fetchrow(
                    query,
                    connection.connection_id,
                    connection.name,
                    db_type_value,
                    connection.connection_string,  # Already encrypted
                    connection.description,
                    connection.environment,
                    connection.tags,
                    status_value,
                    connection.created_by,
                    connection.tenant_id,
                    connection.created_at,
                    connection.updated_at
                )
                
                if row:
                    connection.created_at = row["created_at"]
                    connection.updated_at = row["updated_at"]
                    
                logger.info(
                    f"Created database connection: {connection.name}",
                    extra={"connection_id": connection.connection_id}
                )
                
                return connection
        except Exception as e:
            logger.error(f"Error creating connection: {e}", exc_info=True)
            raise DomainError(f"Failed to create connection: {e}") from e
    
    async def get_connection(
        self,
        connection_id: str,
        include_encrypted: bool = False
    ) -> Optional[DatabaseConnection]:
        """Get connection by ID"""
        pool = database_client.pool
        
        query = """
            SELECT 
                connection_id, name, db_type, connection_string,
                description, environment, tags, status,
                last_tested_at, last_error,
                created_by, tenant_id, created_at, updated_at
            FROM dba_connections
            WHERE connection_id = $1
        """
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, connection_id)
                
                if not row:
                    return None
                
                data = dict(row)
                if not include_encrypted:
                    data.pop("connection_string", None)
                
                return DatabaseConnection.from_dict(data, encrypted=True)
        except Exception as e:
            logger.error(f"Error getting connection: {e}", exc_info=True)
            raise DomainError(f"Failed to get connection: {e}") from e
    
    async def get_connection_by_name(
        self,
        name: str,
        tenant_id: Optional[str] = None
    ) -> Optional[DatabaseConnection]:
        """Get connection by name"""
        pool = database_client.pool
        
        query = """
            SELECT 
                connection_id, name, db_type, connection_string,
                description, environment, tags, status,
                last_tested_at, last_error,
                created_by, tenant_id, created_at, updated_at
            FROM dba_connections
            WHERE name = $1
        """
        params = [name]
        
        if tenant_id:
            query += " AND (tenant_id = $2 OR tenant_id IS NULL)"
            params.append(tenant_id)
        
        query += " ORDER BY tenant_id NULLS LAST LIMIT 1"
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                
                if not row:
                    return None
                
                data = dict(row)
                data.pop("connection_string", None)  # Don't expose encrypted string
                
                return DatabaseConnection.from_dict(data, encrypted=True)
        except Exception as e:
            logger.error(f"Error getting connection by name: {e}", exc_info=True)
            raise DomainError(f"Failed to get connection: {e}") from e
    
    async def list_connections(
        self,
        db_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        include_encrypted: bool = False
    ) -> List[DatabaseConnection]:
        """List connections with filters"""
        pool = database_client.pool
        
        query = """
            SELECT 
                connection_id, name, db_type, connection_string,
                description, environment, tags, status,
                last_tested_at, last_error,
                created_by, tenant_id, created_at, updated_at
            FROM dba_connections
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if db_type:
            query += f" AND db_type = ${param_idx}"
            params.append(db_type)
            param_idx += 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if environment:
            query += f" AND environment = ${param_idx}"
            params.append(environment)
            param_idx += 1
        
        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1
        
        query += " ORDER BY name ASC"
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                connections = []
                for row in rows:
                    data = dict(row)
                    if not include_encrypted:
                        data.pop("connection_string", None)
                    connections.append(DatabaseConnection.from_dict(data, encrypted=True))
                
                return connections
        except Exception as e:
            logger.error(f"Error listing connections: {e}", exc_info=True)
            raise DomainError(f"Failed to list connections: {e}") from e
    
    async def update_connection(
        self,
        connection_id: str,
        updates: dict
    ) -> Optional[DatabaseConnection]:
        """Update connection"""
        pool = database_client.pool
        
        # Build update query dynamically
        set_clauses = []
        params = []
        param_idx = 1
        
        allowed_fields = [
            "name", "db_type", "connection_string", "description",
            "environment", "tags", "status", "last_tested_at", "last_error"
        ]
        
        for field in allowed_fields:
            if field in updates:
                value = updates[field]
                
                # Handle enum to string conversion for db_type and status
                if field == "db_type" and hasattr(value, 'value'):
                    value = value.value
                elif field == "status" and hasattr(value, 'value'):
                    value = value.value
                elif field == "connection_string" and value:
                    # Encrypt connection string if provided
                    value = DatabaseConnection.encrypt_connection_string(value)
                
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1
        
        if not set_clauses:
            # No updates
            return await self.get_connection(connection_id)
        
        set_clauses.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        params.append(connection_id)  # WHERE clause
        
        query = f"""
            UPDATE dba_connections
            SET {', '.join(set_clauses)}
            WHERE connection_id = ${param_idx}
            RETURNING connection_id
        """
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                
                if row:
                    return await self.get_connection(connection_id)
                return None
        except Exception as e:
            logger.error(f"Error updating connection: {e}", exc_info=True)
            raise DomainError(f"Failed to update connection: {e}") from e
    
    async def delete_connection(self, connection_id: str) -> bool:
        """Delete connection"""
        pool = database_client.pool
        
        query = "DELETE FROM dba_connections WHERE connection_id = $1 RETURNING connection_id"
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, connection_id)
                return row is not None
        except Exception as e:
            logger.error(f"Error deleting connection: {e}", exc_info=True)
            raise DomainError(f"Failed to delete connection: {e}") from e
    
    async def test_connection(self, connection_id: str) -> bool:
        """Test connection (placeholder - would need actual connection test)"""
        # This would test the actual database connection
        # For now, just update last_tested_at
        connection = await self.get_connection(connection_id, include_encrypted=True)
        if not connection:
            return False
        
        # TODO: Implement actual connection test
        # For now, just mark as tested
        await self.update_connection(connection_id, {
            "last_tested_at": datetime.utcnow(),
            "status": "active"
        })
        
        return True

