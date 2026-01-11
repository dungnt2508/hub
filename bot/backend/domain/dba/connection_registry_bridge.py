"""
DBA Connection Registry Bridge

Gets actual connection details from DBA connections registry.
Used by risk assessment service to fetch real connection info.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from ...shared.logger import logger
from ...shared.exceptions import DomainError
from .services.connection_registry import connection_registry


class ConnectionInfo:
    """Connection details"""

    def __init__(
        self,
        connection_id: str,
        name: str,
        db_type: str,
        host: str,
        port: int,
        is_production: bool = False,
        status: str = "active",
    ):
        self.connection_id = connection_id
        self.name = name
        self.db_type = db_type
        self.host = host
        self.port = port
        self.is_production = is_production
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "is_production": self.is_production,
            "status": self.status,
        }

    @staticmethod
    def from_database_connection(db_conn: Any) -> 'ConnectionInfo':
        """Create from DatabaseConnection entity"""
        # Extract host and port from connection string if needed
        host = getattr(db_conn, 'host', 'unknown')
        port = int(getattr(db_conn, 'port', 5432))
        
        # Detect production from environment ONLY (strict)
        # Use environment field as source of truth
        environment = getattr(db_conn, 'environment', 'dev').lower()
        is_prod = environment == 'production' or environment == 'prod'
        
        return ConnectionInfo(
            connection_id=str(db_conn.connection_id),
            name=db_conn.name,
            db_type=db_conn.db_type.value if hasattr(db_conn.db_type, 'value') else str(db_conn.db_type),
            host=host,
            port=port,
            is_production=is_prod,
            status=getattr(db_conn, 'status', 'active'),
        )


class ConnectionRegistryBridge:
    """
    Bridge to connection registry.
    
    Queries the actual connection registry service to get real connections.
    Falls back to mock data for testing if connection not found.
    """

    # Mock connections for testing (fallback only)
    MOCK_CONNECTIONS = {
        "dev-1": ConnectionInfo(
            connection_id="dev-1",
            name="DEV_DB",
            db_type="postgresql",
            host="localhost",
            port=5432,
            is_production=False,
            status="active",
        ),
        "dev-mysql": ConnectionInfo(
            connection_id="dev-mysql",
            name="DEV_MYSQL",
            db_type="mysql",
            host="localhost",
            port=3306,
            is_production=False,
            status="active",
        ),
        "prod-01": ConnectionInfo(
            connection_id="prod-01",
            name="PROD_PRIMARY",
            db_type="postgresql",
            host="db.prod.internal",
            port=5432,
            is_production=True,
            status="active",
        ),
    }

    async def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection by ID from registry.
        
        Args:
            connection_id: Connection ID (UUID or string)
            
        Returns:
            ConnectionInfo if found, None otherwise
        """
        try:
            # Try to fetch from real registry first
            try:
                # Convert to UUID if needed
                if isinstance(connection_id, str):
                    try:
                        conn_uuid = UUID(connection_id)
                    except ValueError:
                        # Not a UUID, use as string
                        conn_uuid = connection_id
                else:
                    conn_uuid = connection_id
                
                # Query real registry
                db_conn = await connection_registry.repository.get_connection(
                    str(conn_uuid),
                    include_encrypted=False
                )
                
                if db_conn:
                    logger.info(
                        f"Connection loaded from registry: {db_conn.name}",
                        extra={"connection_id": str(conn_uuid)},
                    )
                    return ConnectionInfo.from_database_connection(db_conn)
                
            except Exception as e:
                logger.debug(
                    f"Could not load from registry: {e}, checking mock connections",
                    extra={"connection_id": connection_id},
                )
            
            # Fall back to mock connections for testing
            if connection_id in self.MOCK_CONNECTIONS:
                logger.info(
                    f"Using mock connection: {self.MOCK_CONNECTIONS[connection_id].name}",
                    extra={"connection_id": connection_id},
                )
                return self.MOCK_CONNECTIONS[connection_id]

            logger.warning(
                f"Connection not found: {connection_id}",
                extra={"connection_id": connection_id},
            )
            return None

        except Exception as e:
            logger.error(
                f"Error fetching connection: {e}",
                extra={"connection_id": connection_id},
                exc_info=True,
            )
            return None


# Singleton instance
connection_registry_bridge = ConnectionRegistryBridge()
