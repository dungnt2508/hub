"""
Database Adapters for MCP Server
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import asyncio
import asyncpg
import aiomysql
import pymssql
from urllib.parse import urlparse, parse_qs


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class DatabaseAdapter(ABC):
    """Base class for database adapters"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    @abstractmethod
    async def connect(self):
        """Connect to database"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from database"""
        pass
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        pass
    
    @abstractmethod
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL adapter using asyncpg"""
    
    async def connect(self):
        """Connect to PostgreSQL"""
        if self._connection is None:
            self._connection = await asyncpg.connect(self.connection_string)
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on PostgreSQL"""
        await self.connect()
        
        # Replace named parameters with positional parameters for asyncpg
        if params:
            # Simple parameter substitution (for production, use proper parameterization)
            formatted_query = query
            for key, value in params.items():
                placeholder = f"%({key})s"
                if placeholder in formatted_query:
                    formatted_query = formatted_query.replace(placeholder, str(value))
            query = formatted_query
        
        rows = await self._connection.fetch(query)
        return [dict(row) for row in rows]
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get PostgreSQL connection info"""
        await self.connect()
        version = await self._connection.fetchval("SELECT version()")
        return {
            "database_type": "postgresql",
            "version": version,
            "database": await self._connection.fetchval("SELECT current_database()"),
            "user": await self._connection.fetchval("SELECT current_user"),
        }


class MySQLAdapter(DatabaseAdapter):
    """MySQL adapter using aiomysql"""
    
    async def connect(self):
        """Connect to MySQL"""
        if self._connection is None:
            # Parse connection string
            parsed = urlparse(self.connection_string.replace("mysql://", "http://"))
            self._connection = await aiomysql.connect(
                host=parsed.hostname or "localhost",
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                db=parsed.path.lstrip("/") if parsed.path else None,
            )
    
    async def disconnect(self):
        """Disconnect from MySQL"""
        if self._connection:
            self._connection.close()
            await self._connection.ensure_closed()
            self._connection = None
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on MySQL"""
        await self.connect()
        cursor = await self._connection.cursor(aiomysql.DictCursor)
        
        # Replace named parameters
        if params:
            formatted_query = query
            for key, value in params.items():
                placeholder = f"%({key})s"
                if placeholder in formatted_query:
                    formatted_query = formatted_query.replace(placeholder, str(value))
            query = formatted_query
        
        await cursor.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get MySQL connection info"""
        await self.connect()
        cursor = await self._connection.cursor(aiomysql.DictCursor)
        await cursor.execute("SELECT VERSION() as version, DATABASE() as database, USER() as user")
        row = await cursor.fetchone()
        await cursor.close()
        return {
            "database_type": "mysql",
            "version": row.get("version"),
            "database": row.get("database"),
            "user": row.get("user"),
        }


class SQLServerAdapter(DatabaseAdapter):
    """SQL Server adapter using pymssql (sync, wrapped with async)"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._parsed = None
    
    def _parse_connection_string(self):
        """Parse SQL Server connection string"""
        if self._parsed:
            return self._parsed
        
        # Support formats:
        # sqlserver://user:pass@host:port?database=db
        # mssql+pyodbc://user:pass@host:port/database
        # mssql+pymssql://user:pass@host:port/database
        
        conn_str = self.connection_string
        
        # Remove driver prefix if present
        if conn_str.startswith("mssql+pyodbc://") or conn_str.startswith("mssql+pymssql://"):
            conn_str = conn_str.replace("mssql+pyodbc://", "sqlserver://").replace("mssql+pymssql://", "sqlserver://")
        
        if not conn_str.startswith("sqlserver://"):
            # Try to parse as direct connection string
            raise ValueError("SQL Server connection string must start with 'sqlserver://'")
        
        # Parse URL
        parsed = urlparse(conn_str.replace("sqlserver://", "http://"))
        
        # Parse query parameters
        query_params = parse_qs(parsed.query)
        
        self._parsed = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 1433,
            "user": parsed.username,
            "password": parsed.password,
            "database": query_params.get("database", [None])[0] or (parsed.path.lstrip("/") if parsed.path else "master"),
        }
        
        return self._parsed
    
    def _connect_sync(self):
        """Synchronous connection to SQL Server"""
        parsed = self._parse_connection_string()
        # pymssql requires server in format "host:port" or just "host" (default port 1433)
        server = parsed["host"]
        if parsed["port"] and parsed["port"] != 1433:
            server = f"{parsed['host']}:{parsed['port']}"
        
        return pymssql.connect(
            server=server,
            user=parsed["user"],
            password=parsed["password"],
            database=parsed["database"],
            timeout=10,
        )
    
    async def connect(self):
        """Connect to SQL Server (async wrapper)"""
        # Always create fresh connection for each request to avoid stale connections
        # Close existing connection if any
        if self._connection is not None:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._executor,
                    self._connection.close
                )
            except:
                pass
            self._connection = None
        
        # Create new connection
        loop = asyncio.get_event_loop()
        self._connection = await loop.run_in_executor(
            self._executor,
            self._connect_sync
        )
    
    async def disconnect(self):
        """Disconnect from SQL Server"""
        if self._connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._connection.close
            )
            self._connection = None
    
    def _execute_query_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query synchronously"""
        cursor = self._connection.cursor(as_dict=True)
        
        # Simple parameter substitution (for production, use proper parameterization)
        if params:
            formatted_query = query
            for key, value in params.items():
                placeholder = f"%({key})s"
                if placeholder in formatted_query:
                    formatted_query = formatted_query.replace(placeholder, str(value))
            query = formatted_query
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on SQL Server"""
        await self.connect()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._execute_query_sync,
            query,
            params
        )
    
    def _get_connection_info_sync(self) -> Dict[str, Any]:
        """Get SQL Server connection info synchronously"""
        # Connection should already be established by connect()
        if self._connection is None:
            self._connection = self._connect_sync()
        
        cursor = self._connection.cursor(as_dict=True)
        
        try:
            # Get version
            cursor.execute("SELECT @@VERSION as version")
            version_row = cursor.fetchone()
            
            # Get database name
            cursor.execute("SELECT DB_NAME() as database_name, SYSTEM_USER as user_name")
            info_row = cursor.fetchone()
            
            parsed = self._parse_connection_string()
            
            return {
                "database_type": "sqlserver",
                "version": version_row.get("version") if version_row else None,
                "database": info_row.get("database_name") if info_row else parsed["database"],
                "user": info_row.get("user_name") if info_row else parsed["user"],
                "server": f"{parsed['host']}:{parsed['port']}",
            }
        finally:
            cursor.close()
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get SQL Server connection info"""
        await self.connect()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._get_connection_info_sync
        )


# Adapter factory
_adapters: Dict[DatabaseType, type] = {
    DatabaseType.POSTGRESQL: PostgreSQLAdapter,
    DatabaseType.MYSQL: MySQLAdapter,
    DatabaseType.SQLSERVER: SQLServerAdapter,
}


def get_adapter(db_type: DatabaseType, connection_string: str) -> DatabaseAdapter:
    """
    Get database adapter for specified type.
    
    Args:
        db_type: Database type
        connection_string: Database connection string
        
    Returns:
        Database adapter instance
        
    Raises:
        ValueError: If database type is not supported
    """
    adapter_class = _adapters.get(db_type)
    if not adapter_class:
        raise ValueError(f"Unsupported database type: {db_type.value}")
    
    return adapter_class(connection_string)

