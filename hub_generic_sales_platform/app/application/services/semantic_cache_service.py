from typing import Any, Dict, Optional, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories.cache_repo import SemanticCacheRepository
from app.infrastructure.llm.factory import get_llm_provider
from app.infrastructure.cache import get_redis_semantic_cache
from app.core import domain

logger = logging.getLogger(__name__)


class _RedisCacheEntry:
    """Wrapper để trả về từ Redis cache (tương thích TenantSemanticCache)."""
    def __init__(self, response_text: str, cache_id: Optional[str] = None):
        self.response_text = response_text
        self.id = cache_id or ""
        self.tenant_id = ""
        self.query_text = ""
        self.hit_count = 0
        self.last_hit_at = None
        self.created_at = None
        self.updated_at = None


class SemanticCacheService:
    """
    Semantic Cache Service (Tier 2 optimization)

    L1: Redis (exact match, ~1ms) → L2: DB keyword + vector search
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_repo = SemanticCacheRepository(db)
        self.llm_provider = get_llm_provider()
        self.redis_cache = get_redis_semantic_cache()

    async def find_match(
        self,
        tenant_id: str,
        message: str,
        query_vector: Optional[List[float]] = None,
        threshold: float = 0.95
    ) -> Optional[domain.TenantSemanticCache]:
        """
        L1 Redis (exact) → L2 DB (keyword + vector).
        """
        msg_lower = (message or "").lower().strip()

        # L1: Redis exact match (nhanh nhất)
        redis_entry = await self.redis_cache.get(tenant_id, message)
        if redis_entry:
            return _RedisCacheEntry(
                response_text=redis_entry.get("response_text", ""),
                cache_id=redis_entry.get("cache_id"),
            )

        # L2: DB - cần vector nếu dùng semantic search
        if not query_vector:
            logger.debug("SemanticCacheService: Generating embedding for DB lookup")
            query_vector = await self.llm_provider.get_embedding(message)

        cache_entry = await self.cache_repo.get_by_message(
            tenant_id=tenant_id,
            message=msg_lower,
            query_vector=query_vector,
            threshold=threshold
        )

        # Populate Redis cho lần sau (exact match)
        if cache_entry and hasattr(cache_entry, "query_text"):
            await self.redis_cache.set(
                tenant_id,
                cache_entry.query_text,
                cache_entry.response_text,
                cache_id=getattr(cache_entry, "id", None),
            )

        return cache_entry

    async def track_hit(self, cache_id: str):
        """Chỉ track khi hit từ DB (Redis hit không cần)."""
        if not cache_id:
            return
        await self.cache_repo.track_hit(cache_id)

    async def create_entry(
        self,
        tenant_id: str,
        query_text: str,
        response_text: str,
        embedding: Optional[List[float]] = None
    ) -> Optional[domain.TenantSemanticCache]:
        """Tạo cache trong DB và Redis."""
        try:
            data = {
                "tenant_id": tenant_id,
                "query_text": query_text.lower().strip()[:500],
                "response_text": response_text[:2000],
            }
            if embedding:
                data["embedding"] = embedding
            obj = await self.cache_repo.create(data, tenant_id=tenant_id)
            if obj:
                await self.redis_cache.set(
                    tenant_id,
                    obj.query_text,
                    obj.response_text,
                    cache_id=getattr(obj, "id", None),
                )
            return obj
        except Exception as e:
            logger.warning(f"SemanticCacheService.create_entry failed: {e}")
            return None
