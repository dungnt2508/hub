"""
Connection Validator - Validates database connections for safety
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time

from .database_client import DatabaseClientFactory, DatabaseClient

@dataclass
class ConnectionInfo:
    """Database connection information"""
    id: str
    name: str
    db_type: str
    host: str
    port: int
    is_production: bool
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ConnectionValidator:
    """Validates database connections for DBA sandbox"""

    def __init__(self):
        """Initialize connection validator"""
        self.timeout_ms = 5000  # 5 second timeout
        self.max_retries = 2

    async def validate(self, connection: ConnectionInfo) -> Dict[str, Any]:
        """
        Validate database connection with real connection
        
        Tests:
        - Connection is alive
        - User has permissions
        - DB type is correct
        - Can execute queries
        
        Returns:
        {
            'connection_id': str,
            'is_alive': bool,
            'db_type': str,
            'is_production': bool,
            'user_permissions': List[str],
            'server_version': Optional[str],
            'database_name': str,
            'table_stats': List[TableStats],
            'warning': Optional[str],
            'error': Optional[str],
            'duration_ms': int,
        }
        """
        start_time = time.time()
        result = {
            'connection_id': connection.id,
            'is_alive': False,
            'db_type': connection.db_type,
            'is_production': connection.is_production,
            'user_permissions': [],
            'server_version': None,
            'database_name': connection.database or 'unknown',
            'table_stats': [],
            'warning': None,
            'error': None,
            'duration_ms': 0,
        }

        db_client = None
        try:
            # Check if production
            if connection.is_production:
                result['warning'] = "This is a PRODUCTION database - be careful!"

            # Create database client
            db_client = DatabaseClientFactory.create(
                connection.db_type,
                connection.host,
                connection.port,
                connection.database,
                connection.username or "sa",
                connection.password or ""
            )

            # Test connection
            is_alive, error_msg = await db_client.test_connection()
            result['is_alive'] = is_alive

            if not is_alive:
                result['error'] = f"Cannot connect to {connection.name}: {error_msg}"
                result['duration_ms'] = int((time.time() - start_time) * 1000)
                return result

            # Get server version
            version = await db_client.get_server_version()
            result['server_version'] = version

            # Get user permissions
            permissions = await db_client.get_user_permissions()
            result['user_permissions'] = permissions

            # Get table statistics
            table_stats = await db_client.get_table_stats()
            result['table_stats'] = [
                {
                    'name': ts.name,
                    'row_count': ts.row_count,
                    'size_mb': ts.size_mb,
                    'schema': ts.schema
                }
                for ts in table_stats
            ]

            # Check for permission warnings
            required_perms = ['SELECT']
            missing_perms = [p for p in required_perms if p not in permissions]
            if missing_perms:
                result['error'] = f"User lacks permissions: {', '.join(missing_perms)}"

        except ImportError as e:
            result['error'] = f"Database driver not installed: {str(e)}"
        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"

        finally:
            # Cleanup
            if db_client:
                try:
                    await db_client.disconnect()
                except Exception:
                    pass

            result['duration_ms'] = int((time.time() - start_time) * 1000)

        return result


    async def validate_multiple(
        self, connections: List[ConnectionInfo]
    ) -> Dict[str, Dict[str, Any]]:
        """Validate multiple connections in parallel"""
        tasks = [self.validate(conn) for conn in connections]
        results = await asyncio.gather(*tasks)

        return {conn.id: result for conn, result in zip(connections, results)}

    def get_connection_status_summary(self, result: Dict[str, Any]) -> str:
        """Get human-readable connection status"""
        if result['is_alive']:
            if result['user_permissions']:
                perms = ', '.join(result['user_permissions'])
                return f"✓ Connected ({perms})"
            else:
                return "✓ Connected (no permissions)"
        else:
            return "✗ Connection failed"

    def get_connection_risk(self, result: Dict[str, Any]) -> str:
        """Get connection risk level"""
        if not result['is_alive']:
            return 'CRITICAL'  # Can't even connect

        if result['is_production']:
            if 'SELECT' not in result['user_permissions']:
                return 'CRITICAL'  # No SELECT on production
            return 'HIGH'  # Any production access is risky

        # Development connections are lower risk
        return 'LOW'
