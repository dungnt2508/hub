"""
Redis L1 Cache cho Semantic Cache (Tier 2 - Knowledge Path)

Tối ưu: Exact match được cache trong Redis (~1ms) thay vì query DB (~10-50ms).
Vector search vẫn qua DB (pgvector) vì Redis không lưu vector similarity.
"""
import hashlib
import json
import logging
from typing import Optional, Any

from app.core.config.settings import get_settings

logger = logging.getLogger(__name__)

PREFIX = "semantic_cache"
DEFAULT_TTL = 3600  # 1 hour


def _normalize(message: str) -> str:
    return (message or "").lower().strip()[:500]


def _cache_key(tenant_id: str, message: str) -> str:
    norm = _normalize(message)
    h = hashlib.sha256(f"{tenant_id}:{norm}".encode()).hexdigest()
    return f"{PREFIX}:{tenant_id}:{h[:16]}"


class RedisSemanticCache:
    """
    L1 cache for semantic responses. Key = hash(tenant_id + normalized_message).
    Fallback to in-memory khi Redis không có.
    """

    def __init__(self):
        self._memory: dict = {}
        self.redis = None
        settings = get_settings()
        if settings.redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(settings.redis_url)
                logger.info("RedisSemanticCache: Connected to Redis")
            except Exception as e:
                logger.warning(f"RedisSemanticCache: Redis unavailable: {e}")

    async def get(self, tenant_id: str, message: str) -> Optional[dict]:
        """
        Lấy cache entry nếu có. Return dict {response_text, cache_id} hoặc None.
        """
        key = _cache_key(tenant_id, message)
        if self.redis:
            try:
                raw = await self.redis.get(key)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

        return self._memory.get(key)

    async def set(
        self,
        tenant_id: str,
        message: str,
        response_text: str,
        cache_id: Optional[str] = None,
        ttl: int = DEFAULT_TTL,
    ) -> None:
        """Lưu vào Redis (và memory fallback)."""
        key = _cache_key(tenant_id, message)
        payload = {"response_text": response_text, "cache_id": cache_id}

        if self.redis:
            try:
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(payload, ensure_ascii=False),
                )
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

        self._memory[key] = payload

    async def delete(self, tenant_id: str, message: str) -> None:
        """Xóa entry (khi invalidate)."""
        key = _cache_key(tenant_id, message)
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
        self._memory.pop(key, None)


_redis_cache: Optional[RedisSemanticCache] = None


def get_redis_semantic_cache() -> RedisSemanticCache:
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisSemanticCache()
    return _redis_cache
