"""
Database Connection Repository - Load connections from dba_connections table
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import asyncpg
import json
from datetime import datetime

from ...infrastructure.database_client import database_client
from ...shared.logger import logger


@dataclass
class DBConnectionRecord:
    """Database connection record from dba_connections table"""
    id: str
    connection_id: str
    name: str
    db_type: str
    connection_string: str  # Encrypted
    description: Optional[str]
    environment: Optional[str]
    tags: Optional[List[str]]
    status: str
    last_tested_at: Optional[datetime]
    last_error: Optional[str]
    created_by: Optional[str]
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class DBConnectionRepository:
    """Repository for DBA connections from database"""

    async def get_all_connections(
        self,
        environment: Optional[str] = None,
        status: str = "active",
        tenant_id: Optional[str] = None,
    ) -> List[DBConnectionRecord]:
        """
        Get all connections from database
        
        Args:
            environment: Filter by environment (dev, prod, etc.)
            status: Filter by status (default: active)
            tenant_id: Filter by tenant (optional)
            
        Returns:
            List of database connection records
        """
        try:
            pool = database_client._pool
            if not pool:
                logger.warning("🔴 Database pool not initialized")
                return []

            # Build query
            query = "SELECT * FROM dba_connections WHERE status = $1"
            params = [status]

            if environment:
                query += f" AND environment = ${len(params) + 1}"
                params.append(environment)

            if tenant_id:
                query += f" AND tenant_id = ${len(params) + 1}"
                params.append(tenant_id)

            query += " ORDER BY created_at DESC"

            logger.debug(f"Querying dba_connections: status={status}, environment={environment}")
            
            # Execute query
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            # Convert to records
            records = []
            for row in rows:
                record = self._map_row_to_record(dict(row))
                records.append(record)

            logger.debug(f"🔵 Loaded {len(records)} connections from database")
            
            if len(records) == 0:
                logger.info("ℹ️  No connections found in dba_connections table with status='active'")
                # List all connections for debugging
                debug_query = "SELECT id, name, db_type, status FROM dba_connections LIMIT 10"
                async with pool.acquire() as conn:
                    debug_rows = await conn.fetch(debug_query)
                if debug_rows:
                    logger.info(f"Available in table (debug): {len(debug_rows)} total records")
                    for r in debug_rows:
                        logger.debug(f"  - {r['name']} ({r['db_type']}) - status: {r['status']}")
                else:
                    logger.info("⚠️  dba_connections table is completely empty")
            
            return records

        except Exception as e:
            logger.error(f"🔴 Error loading connections from database: {e}", exc_info=True)
            return []

    async def get_connection_by_id(self, connection_id: str) -> Optional[DBConnectionRecord]:
        """Get specific connection by connection_id"""
        try:
            pool = database_client._pool
            if not pool:
                return None

            query = "SELECT * FROM dba_connections WHERE connection_id = $1 AND status = 'active' LIMIT 1"

            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, connection_id)

            if not row:
                return None

            return self._map_row_to_record(dict(row))

        except Exception as e:
            logger.error(f"Error loading connection {connection_id}: {e}", exc_info=True)
            return None

    async def get_connection_by_name(
        self,
        name: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[DBConnectionRecord]:
        """Get connection by name (and optional tenant)"""
        try:
            pool = database_client._pool
            if not pool:
                return None

            if tenant_id:
                query = "SELECT * FROM dba_connections WHERE name = $1 AND tenant_id = $2 AND status = 'active' LIMIT 1"
                params = [name, tenant_id]
            else:
                query = "SELECT * FROM dba_connections WHERE name = $1 AND status = 'active' LIMIT 1"
                params = [name]

            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)

            if not row:
                return None

            return self._map_row_to_record(dict(row))

        except Exception as e:
            logger.error(f"Error loading connection {name}: {e}", exc_info=True)
            return None

    async def update_connection_status(
        self,
        connection_id: str,
        is_healthy: bool,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update connection health status after validation
        
        Args:
            connection_id: Connection ID to update
            is_healthy: Is connection working?
            error_message: Error message if not healthy
        """
        try:
            pool = database_client._pool
            if not pool:
                return False

            if is_healthy:
                query = """
                UPDATE dba_connections 
                SET status = 'active', last_tested_at = NOW(), last_error = NULL
                WHERE connection_id = $1
                """
                async with pool.acquire() as conn:
                    await conn.execute(query, connection_id)
            else:
                query = """
                UPDATE dba_connections 
                SET status = 'error', last_tested_at = NOW(), last_error = $2
                WHERE connection_id = $1
                """
                async with pool.acquire() as conn:
                    await conn.execute(query, connection_id, error_message)

            logger.debug(f"Updated connection {connection_id} status: healthy={is_healthy}")
            return True

        except Exception as e:
            logger.error(f"Error updating connection status: {e}", exc_info=True)
            return False

    def _map_row_to_record(self, row: Dict[str, Any]) -> DBConnectionRecord:
        """Convert database row to DBConnectionRecord"""
        tags = row.get("tags", [])
        if isinstance(tags, str):
            tags = json.loads(tags)

        return DBConnectionRecord(
            id=str(row["id"]),
            connection_id=row["connection_id"],
            name=row["name"],
            db_type=row["db_type"],
            connection_string=row["connection_string"],
            description=row.get("description"),
            environment=row.get("environment"),
            tags=tags,
            status=row["status"],
            last_tested_at=row.get("last_tested_at"),
            last_error=row.get("last_error"),
            created_by=row.get("created_by"),
            tenant_id=row.get("tenant_id"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# Global repository instance
_repository: Optional[DBConnectionRepository] = None


def get_db_connection_repository() -> DBConnectionRepository:
    """Get global database connection repository (singleton)"""
    global _repository

    if _repository is None:
        _repository = DBConnectionRepository()

    return _repository
