"""
Redis Client - Singleton connection pool
"""
import redis.asyncio as aioredis
from typing import Optional

from ..shared.config import config
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


class RedisClient:
    """Singleton Redis client with connection pool"""
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[aioredis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Initialize Redis connection"""
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    config.REDIS_URL,
                    max_connections=config.REDIS_MAX_CONNECTIONS,
                    decode_responses=True,
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
                raise ExternalServiceError(f"Redis connection failed: {e}") from e
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
    
    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client instance"""
        if self._redis is None:
            raise ExternalServiceError("Redis not connected. Call connect() first.")
        return self._redis
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if self._redis:
                await self._redis.ping()
                return True
            return False
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()

