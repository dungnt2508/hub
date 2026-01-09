"""
Database Client - Singleton connection pool for PostgreSQL
Uses asyncpg with proper Windows networking handling
"""
import asyncpg
from typing import Optional
import os
import asyncio

from ..shared.config import config
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


class DatabaseClient:
    """Singleton database client with connection pool"""
    
    _instance: Optional['DatabaseClient'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Initialize database connection pool"""
        if self._pool is None:
            try:
                # Get DATABASE_URL from environment
                db_url = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_pw@127.0.0.1:5432/bot_db")
                
                # Parse DATABASE_URL
                # Format: postgresql+asyncpg://user:password@host:port/database or postgresql://...
                if db_url.startswith("postgresql+asyncpg://"):
                    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                
                # Windows Docker Desktop fix: if localhost fails, try host.docker.internal
                connection_attempts = [db_url]
                
                # If using localhost/127.0.0.1, also try host.docker.internal
                if "localhost" in db_url or "127.0.0.1" in db_url:
                    docker_db_url = db_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
                    connection_attempts.append(docker_db_url)
                
                last_error = None
                for attempt_url in connection_attempts:
                    try:
                        logger.debug(f"Attempting connection to: {attempt_url.split('@')[1] if '@' in attempt_url else 'unknown'}")
                        
                        # Windows fix: use TCP instead of Unix sockets
                        # Add ssl=False for local connections
                        self._pool = await asyncpg.create_pool(
                            attempt_url,
                            min_size=2,
                            max_size=10,
                            command_timeout=120,
                            ssl=False,  # Disable SSL for local Docker connections
                        )
                        
                        # Test connection
                        async with self._pool.acquire() as conn:
                            await conn.execute("SELECT 1")
                        
                        logger.info(f"Database connection pool established with asyncpg ({attempt_url.split('@')[1] if '@' in attempt_url else 'unknown'})")
                        return
                    except Exception as e:
                        last_error = e
                        if self._pool:
                            await self._pool.close()
                            self._pool = None
                        logger.debug(f"Connection attempt failed: {e}")
                        continue
                
                # All attempts failed
                if last_error:
                    raise last_error
                else:
                    raise ExternalServiceError("No database connection attempts made")
                    
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}", exc_info=True)
                raise ExternalServiceError(f"Database connection failed: {e}") from e
    
    async def disconnect(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get database connection pool"""
        if self._pool is None:
            raise ExternalServiceError("Database not connected. Call connect() first.")
        return self._pool
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if self._pool:
                async with self._pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                return True
            return False
        except Exception:
            return False


# Global database client instance
database_client = DatabaseClient()
