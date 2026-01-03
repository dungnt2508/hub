"""
Database Client - Singleton connection pool for PostgreSQL
"""
import asyncpg
from typing import Optional
import os

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
                db_url = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_pw@localhost:5432/bot_db")
                
                # Parse DATABASE_URL
                # Format: postgresql+asyncpg://user:password@host:port/database
                if db_url.startswith("postgresql+asyncpg://"):
                    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                
                # Create connection pool
                self._pool = await asyncpg.create_pool(
                    db_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                )
                
                # Test connection
                async with self._pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                
                logger.info("Database connection pool established")
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

