from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.cache import TenantSemanticCache as CacheModel

# Domain Entities
from app.core import domain

class SemanticCacheRepository(BaseRepository[CacheModel]):
    """Semantic cache repository (Async Implementation) with Domain Mapping"""
    domain_container = domain.TenantSemanticCache
    
    def __init__(self, db: AsyncSession):
        super().__init__(CacheModel, db)
    
    async def get_by_message(
        self,
        tenant_id: str,
        message: str,
        query_vector: Optional[List[float]] = None,
        threshold: float = 0.9  # Threshold for semantic match
    ) -> Optional[domain.TenantSemanticCache]:
        """
        Tìm kiếm câu trả lời trong cache (Keyword Match + Vector Fallback)
        """
        # 1. Thử keyword match trước (Fastest)
        stmt = select(CacheModel).where(
            CacheModel.tenant_id == tenant_id,
            CacheModel.query_text.ilike(f"%{message}%")
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        if db_obj:
            return self._to_domain(db_obj)
            
        # 2. Thử vector match nếu có query_vector
        if query_vector:
            if self.db.bind.dialect.name == "postgresql":
                distance_limit = 1.0 - threshold
                stmt = select(CacheModel).where(
                    CacheModel.tenant_id == tenant_id,
                    CacheModel.embedding.cosine_distance(query_vector) <= distance_limit
                ).order_by(CacheModel.embedding.cosine_distance(query_vector)).limit(1)
                
                result = await self.db.execute(stmt)
                db_obj = result.scalars().first()
                return self._to_domain(db_obj)
            else:
                from app.core.shared.math_utils import cosine_similarity
                stmt = select(CacheModel).where(
                    CacheModel.tenant_id == tenant_id,
                    CacheModel.embedding != None
                )
                result = await self.db.execute(stmt)
                caches = result.scalars().all()
                
                best_match = None
                max_sim = -1.0
                
                for c in caches:
                    sim = cosine_similarity(query_vector, c.embedding)
                    if sim >= threshold and sim > max_sim:
                        max_sim = sim
                        best_match = c
                return self._to_domain(best_match)
            
        return None
    
    async def track_hit(self, cache_id: str):
        """Tăng số lần hit cho cache item"""
        from sqlalchemy import update, func
        stmt = update(CacheModel).where(CacheModel.id == cache_id).values(
            hit_count=CacheModel.hit_count + 1,
            last_hit_at=func.now()
        )
        await self.db.execute(stmt)
