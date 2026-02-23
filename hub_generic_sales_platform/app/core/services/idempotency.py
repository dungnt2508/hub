import json
import logging
from typing import Any, Optional
from app.core.config.settings import get_settings

logger = logging.getLogger(__name__)

class IdempotencyService:
    """
    Service to ensure tool calls are idempotent.
    Uses Redis as primary store, falls back to in-memory for dev.
    """
    _memory_cache = {}

    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.redis_url
        self.redis = None
        
        if self.redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(self.redis_url)
                logger.info("IdempotencyService: Connected to Redis")
            except Exception as e:
                logger.error(f"IdempotencyService: Failed to connect to Redis: {e}")

    async def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached tool result by idempotency key"""
        if not key:
            return None
            
        if self.redis:
            try:
                cached = await self.redis.get(f"idempotency:{key}")
                return json.loads(cached) if cached else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return self._memory_cache.get(key)

    async def cache_result(self, key: str, result: Any, ttl: int = 3600):
        """Cache tool result"""
        if not key:
            return
            
        if self.redis:
            try:
                await self.redis.setex(
                    f"idempotency:{key}",
                    ttl,
                    json.dumps(result, ensure_ascii=False)
                )
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        self._memory_cache[key] = result

    async def clear_cache(self):
        """Clear memory cache (for tests)"""
        self._memory_cache.clear()
        if self.redis:
            try:
                keys = await self.redis.keys("idempotency:*")
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

# Singleton instance
_idempotency_service: Optional[IdempotencyService] = None

def get_idempotency_service() -> IdempotencyService:
    global _idempotency_service
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService()
    return _idempotency_service
