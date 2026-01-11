"""
Connection Registry - Manages database connections from dba_connections table
Loads connections from database first, falls back to environment variable
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import json
from enum import Enum
import asyncio

from .db_connection_repository import get_db_connection_repository
from ...shared.logger import logger


class ConnectionScope(str, Enum):
    """Connection visibility scope"""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"


@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    id: str
    connection_id: str
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str  # Should be from vault
    is_production: bool = False
    scope: ConnectionScope = ConnectionScope.GLOBAL
    tenant_id: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None


class ConnectionRegistry:
    """
    Central registry for database connections
    
    Priority:
    1. Load from dba_connections table (database)
    2. Fall back to DBA_CONNECTIONS_JSON environment variable
    3. Use default development connections
    """

    def __init__(self):
        """Initialize connection registry"""
        self.connections: Dict[str, ConnectionConfig] = {}
        self.db_repo = get_db_connection_repository()
        self._loaded_from_db = False
        self._loaded_from_env = False

    async def initialize(self) -> bool:
        """
        Initialize and load connections from database or environment
        Should be called during app startup
        """
        try:
            logger.info("🔧 Initializing DBA Sandbox Connection Registry...")
            
            # Try to load from database first
            logger.debug("Attempting to load connections from dba_connections table...")
            db_records = await self.db_repo.get_all_connections(status="active")

            if db_records:
                logger.info(f"✅ Loaded {len(db_records)} connections from database")
                for record in db_records:
                    # Parse connection string (format: db_type://user:password@host:port/database)
                    conn_config = self._parse_connection_string(
                        record.connection_string,
                        record.db_type,
                        record.name,
                        record.connection_id,
                        record.environment,
                        record.tenant_id,
                        record.description,
                    )
                    if conn_config:
                        self.connections[conn_config.connection_id] = conn_config
                        logger.debug(f"  → {record.name} ({record.db_type}) - {record.environment}")

                self._loaded_from_db = True
                logger.info(f"🎉 Registry ready with {len(self.connections)} connections from database")
                return True

            else:
                # Fall back to environment variable
                logger.info("❌ No connections found in database, trying DBA_CONNECTIONS_JSON...")
                self._load_connections_from_env()
                
                if self.connections:
                    logger.info(f"✅ Loaded {len(self.connections)} connections from environment")
                    return True
                else:
                    # Load defaults as last resort
                    logger.warning("❌ No connections in environment, loading defaults")
                    self._load_default_connections()
                    if self.connections:
                        logger.info(f"⚠️  Loaded {len(self.connections)} default connections")
                        return True
                    else:
                        logger.error("❌ No connections available at all!")
                        return False

        except Exception as e:
            logger.warning(f"⚠️  Error loading from database: {e}, falling back to environment")
            self._load_connections_from_env()
            
            if self.connections:
                logger.info(f"✅ Loaded {len(self.connections)} connections from environment")
                return True
            else:
                logger.warning("❌ No connections found, loading defaults")
                self._load_default_connections()
                if self.connections:
                    logger.info(f"⚠️  Loaded {len(self.connections)} default connections")
                    return True
                else:
                    logger.error("❌ CRITICAL: No connections available!")
                    return False

    def _load_connections_from_env(self):
        """Load connections from environment variables"""
        # Format:
        # DBA_CONNECTIONS_JSON='[{"id":"dev-1","name":"DEV_DB",...}]'

        connections_json = os.getenv("DBA_CONNECTIONS_JSON", "[]")

        try:
            connections_list = json.loads(connections_json)

            for conn_config in connections_list:
                # Parse connection from environment format
                conn = ConnectionConfig(
                    id=conn_config.get("id", conn_config.get("connection_id")),
                    connection_id=conn_config.get("connection_id", conn_config.get("id")),
                    name=conn_config.get("name"),
                    db_type=conn_config.get("db_type"),
                    host=conn_config.get("host"),
                    port=conn_config.get("port"),
                    database=conn_config.get("database"),
                    username=conn_config.get("username"),
                    password=conn_config.get("password"),
                    is_production=conn_config.get("is_production", False),
                    environment=conn_config.get("environment"),
                    description=conn_config.get("description"),
                )
                self.connections[conn.connection_id] = conn

            if self.connections:
                logger.info(f"Loaded {len(self.connections)} connections from environment")
                self._loaded_from_env = True

        except Exception as e:
            logger.error(f"Error parsing DBA_CONNECTIONS_JSON: {e}")
            # Fall back to defaults if parsing fails
            self._load_default_connections()

    def _parse_connection_string(
        self,
        conn_string: str,
        db_type: str,
        name: str,
        connection_id: str,
        environment: Optional[str],
        tenant_id: Optional[str],
        description: Optional[str],
    ) -> Optional[ConnectionConfig]:
        """
        Parse connection string into ConnectionConfig
        Format: db_type://user:password@host:port/database
        Example: sql_server://sa:password@localhost:1433/development
        """
        try:
            # Remove scheme if present
            if "://" in conn_string:
                conn_string = conn_string.split("://", 1)[1]

            # Parse user:password@host:port/database
            # user:password
            if "@" in conn_string:
                auth, rest = conn_string.split("@", 1)
                username, password = auth.split(":", 1)
            else:
                username = "sa"
                password = ""
                rest = conn_string

            # host:port/database
            if "/" in rest:
                host_port, database = rest.split("/", 1)
            else:
                host_port = rest
                database = "master"

            # host:port
            if ":" in host_port:
                host, port_str = host_port.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 1433 if db_type == "sql_server" else 5432

            else:
                host = host_port
                port = 1433 if db_type == "sql_server" else 5432

            is_production = environment and environment.lower() == "production"

            return ConnectionConfig(
                id=connection_id,
                connection_id=connection_id,
                name=name,
                db_type=db_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
                is_production=is_production,
                environment=environment,
                description=description,
                tenant_id=tenant_id,
            )

        except Exception as e:
            logger.error(f"Error parsing connection string for {name}: {e}")
            return None

    def _load_default_connections(self):
        """Load default development connections"""
        defaults = [
            ConnectionConfig(
                id="dev-1",
                connection_id="dev-1",
                name="DEV_DB",
                db_type="sql_server",
                host="localhost",
                port=1433,
                database="development",
                username="sa",
                password="YourStrongPassword123",
                is_production=False,
                description="Local development database",
                environment="development",
            ),
            ConnectionConfig(
                id="dev-2",
                connection_id="dev-2",
                name="DEV_POSTGRES",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database="development",
                username="postgres",
                password="postgres",
                is_production=False,
                description="Local PostgreSQL for testing",
                environment="development",
            ),
        ]

        for conn in defaults:
            self.connections[conn.connection_id] = conn

        logger.info(f"Loaded {len(defaults)} default development connections")

    def get_connection(self, connection_id: str) -> Optional[ConnectionConfig]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_connection_by_name(self, name: str) -> Optional[ConnectionConfig]:
        """Get connection by name"""
        for conn in self.connections.values():
            if conn.name.lower() == name.lower():
                return conn
        return None

    def list_connections(
        self,
        is_production: Optional[bool] = None,
        db_type: Optional[str] = None,
        environment: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[ConnectionConfig]:
        """List connections with optional filters"""
        result = []

        for conn in self.connections.values():
            # Apply filters
            if is_production is not None and conn.is_production != is_production:
                continue
            if db_type is not None and conn.db_type != db_type:
                continue
            if environment is not None and conn.environment != environment:
                continue
            if tenant_id is not None and conn.tenant_id != tenant_id:
                continue

            result.append(conn)

        return result

    def add_connection(self, config: ConnectionConfig) -> bool:
        """Add new connection to registry"""
        if config.connection_id in self.connections:
            return False  # Already exists

        self.connections[config.connection_id] = config
        return True

    def update_connection(self, config: ConnectionConfig) -> bool:
        """Update existing connection"""
        if config.connection_id not in self.connections:
            return False

        self.connections[config.connection_id] = config
        return True

    def delete_connection(self, connection_id: str) -> bool:
        """Delete connection from registry"""
        if connection_id not in self.connections:
            return False

        del self.connections[connection_id]
        return True

    def get_status(self) -> Dict[str, any]:
        """Get registry status"""
        return {
            "total_connections": len(self.connections),
            "loaded_from_database": self._loaded_from_db,
            "loaded_from_environment": self._loaded_from_env,
            "connection_ids": list(self.connections.keys()),
        }


# Global registry instance
_registry: Optional[ConnectionRegistry] = None


def get_registry() -> ConnectionRegistry:
    """Get global connection registry (singleton)"""
    global _registry

    if _registry is None:
        _registry = ConnectionRegistry()

    return _registry


async def initialize_registry() -> bool:
    """Initialize registry during app startup"""
    registry = get_registry()
    return await registry.initialize()
