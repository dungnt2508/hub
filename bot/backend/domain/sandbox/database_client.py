"""
Database Client Interface and Implementations for sandbox
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass


@dataclass
class TableStats:
    """Table statistics"""
    name: str
    row_count: int
    size_mb: float
    schema: str = "dbo"


class DatabaseClient(ABC):
    """Abstract base class for database clients"""

    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish database connection"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close database connection"""
        pass

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """Test if connection works"""
        pass

    @abstractmethod
    async def get_user_permissions(self) -> List[str]:
        """Get current user's permissions"""
        pass

    @abstractmethod
    async def get_table_stats(self) -> List[TableStats]:
        """Get table statistics for cost estimation"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """Execute query and return results/metadata"""
        pass

    @abstractmethod
    async def get_server_version(self) -> str:
        """Get database server version"""
        pass


class SQLServerClient(DatabaseClient):
    """Microsoft SQL Server client"""

    async def connect(self) -> bool:
        """Connect to SQL Server"""
        try:
            # Import here to avoid hard dependency
            import pyodbc
            
            connection_string = (
                f"Driver={{ODBC Driver 17 for SQL Server}};"
                f"Server={self.host},{self.port};"
                f"Database={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"Connection Timeout=5;"
            )
            
            self.connection = pyodbc.connect(connection_string)
            self.is_connected = True
            return True
        except ImportError:
            raise ImportError("pyodbc not installed. Install with: pip install pyodbc")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from SQL Server"""
        if self.is_connected and hasattr(self, 'connection'):
            try:
                self.connection.close()
                self.is_connected = False
                return True
            except Exception:
                return False
        return True

    async def test_connection(self) -> Tuple[bool, str]:
        """Test SQL Server connection"""
        try:
            await self.connect()
            
            # Try simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                await self.disconnect()
                return True, "Connection successful"
            else:
                return False, "Connection query failed"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def get_user_permissions(self) -> List[str]:
        """Get current user's permissions on database"""
        permissions = []
        
        try:
            cursor = self.connection.cursor()
            
            # Check for basic permissions
            permission_checks = {
                "SELECT": "SELECT COUNT(*) FROM sys.tables",
                "INSERT": "SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'INSERT')",
                "UPDATE": "SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'UPDATE')",
                "DELETE": "SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'DELETE')",
                "CREATE": "SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE')",
                "ALTER": "SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'ALTER')",
            }
            
            for perm_name, perm_query in permission_checks.items():
                try:
                    cursor.execute(perm_query)
                    result = cursor.fetchone()
                    if result and result[0]:
                        permissions.append(perm_name)
                except Exception:
                    # If query fails, assume permission denied
                    pass
            
            return permissions if permissions else ["SELECT"]
            
        except Exception as e:
            return ["SELECT"]  # Default to SELECT only

    async def get_table_stats(self) -> List[TableStats]:
        """Get table statistics from SQL Server"""
        tables = []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                SCHEMA_NAME(t.schema_id) as schema_name,
                t.name as table_name,
                SUM(p.rows) as row_count,
                CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(10,2)) as size_mb
            FROM sys.tables t
            INNER JOIN sys.indexes i ON t.object_id = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
            INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE t.is_ms_shipped = 0
            GROUP BY t.schema_id, t.name
            ORDER BY row_count DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                schema, table_name, row_count, size_mb = row
                tables.append(
                    TableStats(
                        name=table_name,
                        row_count=int(row_count or 0),
                        size_mb=float(size_mb or 0),
                        schema=schema or "dbo"
                    )
                )
            
            return tables
            
        except Exception as e:
            # Return empty list if query fails
            return []

    async def execute_query(self, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """Execute query on SQL Server"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Get first few rows
            rows = cursor.fetchmany(100)
            
            return {
                'success': True,
                'columns': columns,
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows),
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    async def get_server_version(self) -> str:
        """Get SQL Server version"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            return version.split('\n')[0]  # Get first line
        except Exception:
            return "SQL Server (unknown version)"


class PostgreSQLClient(DatabaseClient):
    """PostgreSQL client"""

    async def connect(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            import psycopg2
            
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                connect_timeout=5,
            )
            self.is_connected = True
            return True
        except ImportError:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL"""
        if self.is_connected and hasattr(self, 'connection'):
            try:
                self.connection.close()
                self.is_connected = False
                return True
            except Exception:
                return False
        return True

    async def test_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            await self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                await self.disconnect()
                return True, "Connection successful"
            else:
                return False, "Connection query failed"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def get_user_permissions(self) -> List[str]:
        """Get current user's permissions on database"""
        permissions = ["SELECT"]  # PostgreSQL allows SELECT by default
        
        try:
            cursor = self.connection.cursor()
            
            # Check for other permissions
            current_user_query = "SELECT current_user"
            cursor.execute(current_user_query)
            current_user = cursor.fetchone()[0]
            
            # Check for specific permissions
            # In PostgreSQL, we'd check table privileges
            # For simplicity, assume full permissions if connected
            permissions = ["SELECT", "INSERT", "UPDATE", "DELETE"]
            
            return permissions
            
        except Exception as e:
            return ["SELECT"]

    async def get_table_stats(self) -> List[TableStats]:
        """Get table statistics from PostgreSQL"""
        tables = []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                schemaname,
                tablename,
                CAST(pg_total_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0 AS DECIMAL(10,2)) as size_mb,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                schema, table_name, size_mb, row_count = row
                tables.append(
                    TableStats(
                        name=table_name,
                        row_count=int(row_count or 0),
                        size_mb=float(size_mb or 0),
                        schema=schema or "public"
                    )
                )
            
            return tables
            
        except Exception as e:
            return []

    async def execute_query(self, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """Execute query on PostgreSQL"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Get first few rows
            rows = cursor.fetchmany(100)
            
            return {
                'success': True,
                'columns': columns,
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows),
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    async def get_server_version(self) -> str:
        """Get PostgreSQL version"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            return version.split(',')[0]  # Get first part
        except Exception:
            return "PostgreSQL (unknown version)"


class MySQLClient(DatabaseClient):
    """MySQL/MariaDB client"""

    async def connect(self) -> bool:
        """Connect to MySQL"""
        try:
            import mysql.connector
            
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                connection_timeout=5,
            )
            self.is_connected = True
            return True
        except ImportError:
            raise ImportError("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from MySQL"""
        if self.is_connected and hasattr(self, 'connection'):
            try:
                self.connection.close()
                self.is_connected = False
                return True
            except Exception:
                return False
        return True

    async def test_connection(self) -> Tuple[bool, str]:
        """Test MySQL connection"""
        try:
            await self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                await self.disconnect()
                return True, "Connection successful"
            else:
                return False, "Connection query failed"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def get_user_permissions(self) -> List[str]:
        """Get current user's permissions"""
        permissions = ["SELECT"]
        
        try:
            cursor = self.connection.cursor()
            
            # Check grants
            cursor.execute("SHOW GRANTS FOR CURRENT_USER")
            grants = cursor.fetchall()
            
            grants_str = str(grants).upper()
            
            if "INSERT" in grants_str:
                permissions.append("INSERT")
            if "UPDATE" in grants_str:
                permissions.append("UPDATE")
            if "DELETE" in grants_str:
                permissions.append("DELETE")
            if "CREATE" in grants_str:
                permissions.append("CREATE")
            if "ALTER" in grants_str:
                permissions.append("ALTER")
            
            return permissions
            
        except Exception:
            return ["SELECT"]

    async def get_table_stats(self) -> List[TableStats]:
        """Get table statistics from MySQL"""
        tables = []
        
        try:
            cursor = self.connection.cursor()
            
            query = f"""
            SELECT 
                TABLE_NAME,
                TABLE_ROWS,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{self.database}'
            ORDER BY TABLE_ROWS DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                table_name, row_count, size_mb = row
                tables.append(
                    TableStats(
                        name=table_name,
                        row_count=int(row_count or 0),
                        size_mb=float(size_mb or 0),
                        schema=self.database
                    )
                )
            
            return tables
            
        except Exception:
            return []

    async def execute_query(self, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """Execute query on MySQL"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Get first few rows
            rows = cursor.fetchmany(100)
            
            return {
                'success': True,
                'columns': columns,
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows),
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    async def get_server_version(self) -> str:
        """Get MySQL version"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            return version
        except Exception:
            return "MySQL (unknown version)"


class DatabaseClientFactory:
    """Factory for creating database clients"""

    @staticmethod
    def create(
        db_type: str, host: str, port: int, database: str,
        username: str, password: str
    ) -> DatabaseClient:
        """Create appropriate database client"""
        
        db_type = db_type.lower()
        
        if db_type in ["sql_server", "mssql", "sqlserver"]:
            return SQLServerClient(host, port, database, username, password)
        elif db_type in ["postgresql", "postgres", "pg"]:
            return PostgreSQLClient(host, port, database, username, password)
        elif db_type in ["mysql", "mariadb"]:
            return MySQLClient(host, port, database, username, password)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
