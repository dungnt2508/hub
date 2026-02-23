from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import BotFAQ as FAQModel

# Domain Entities
from app.core import domain
from app.core.interfaces.knowledge_repo import IFAQRepository


class FAQRepository(BaseRepository[FAQModel], IFAQRepository):
    """FAQ repository with Domain Mapping"""
    domain_container = domain.BotFAQ
    
    def __init__(self, db: AsyncSession):
        super().__init__(FAQModel, db)
    
    async def get_by_offering(self, offering_id: str, tenant_id: str) -> List[domain.BotFAQ]:
        """Get all FAQs for an offering"""
        stmt = select(FAQModel).where(
            FAQModel.offering_id == offering_id,
            FAQModel.tenant_id == tenant_id,
            FAQModel.is_active == True
        ).order_by(FAQModel.priority.desc())
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def get_by_category(
        self,
        tenant_id: str,
        category: str,
        bot_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> List[domain.BotFAQ]:
        """Get FAQs by category and bot/domain"""
        stmt = select(FAQModel).where(
            FAQModel.tenant_id == tenant_id,
            FAQModel.category == category,
            FAQModel.is_active == True
        )
        if bot_id:
            stmt = stmt.where(FAQModel.bot_id == bot_id)
        if domain_id:
            stmt = stmt.where(FAQModel.domain_id == domain_id)
        stmt = stmt.order_by(FAQModel.priority.desc())
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
    
    async def search(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10,
        bot_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> List[domain.BotFAQ]:
        """Search FAQs by question text and bot/domain"""
        stmt = select(FAQModel).where(
            FAQModel.tenant_id == tenant_id,
            FAQModel.is_active == True,
            FAQModel.question.ilike(f"%{query}%")
        )
        if bot_id:
            stmt = stmt.where(FAQModel.bot_id == bot_id)
        if domain_id:
            stmt = stmt.where(FAQModel.domain_id == domain_id)
        stmt = stmt.order_by(FAQModel.priority.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]

    async def semantic_search(
        self,
        tenant_id: str,
        query_vector: List[float],
        threshold: float = 0.8,
        limit: int = 5,
        bot_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> List[tuple[domain.BotFAQ, float]]:
        """
        Tìm kiếm FAQ bằng vector similarity
        """
        distance_limit = 1.0 - threshold
        
        if self.db.bind.dialect.name == "postgresql":
            stmt = select(
                FAQModel, 
                (1.0 - FAQModel.embedding.cosine_distance(query_vector)).label("similarity")
            ).where(
                FAQModel.tenant_id == tenant_id,
                FAQModel.is_active == True,
                FAQModel.embedding.cosine_distance(query_vector) <= distance_limit
            )
            if bot_id:
                stmt = stmt.where(FAQModel.bot_id == bot_id)
            if domain_id:
                stmt = stmt.where(FAQModel.domain_id == domain_id)
            stmt = stmt.order_by(FAQModel.embedding.cosine_distance(query_vector)).limit(limit)
            
            result = await self.db.execute(stmt)
            return [(self._to_domain(r[0]), float(r[1])) for r in result.all()]
        else:
            from app.core.shared.math_utils import cosine_similarity
            stmt = select(FAQModel).where(
                FAQModel.tenant_id == tenant_id,
                FAQModel.is_active == True,
                FAQModel.embedding != None
            )
            if bot_id:
                stmt = stmt.where(FAQModel.bot_id == bot_id)
            if domain_id:
                stmt = stmt.where(FAQModel.domain_id == domain_id)
            result = await self.db.execute(stmt)
            faqs = result.scalars().all()
            
            scored_faqs = []
            for faq in faqs:
                sim = cosine_similarity(query_vector, faq.embedding)
                if sim >= threshold:
                    scored_faqs.append((self._to_domain(faq), sim))
            
            scored_faqs.sort(key=lambda x: x[1], reverse=True)
            return scored_faqs[:limit]

    async def get_active(
        self,
        tenant_id: str,
        bot_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> List[domain.BotFAQ]:
        """Lấy danh sách FAQ đang hoạt động"""
        stmt = select(FAQModel).where(
            FAQModel.tenant_id == tenant_id,
            FAQModel.is_active == True
        )
        if bot_id:
            stmt = stmt.where(FAQModel.bot_id == bot_id)
        if domain_id:
            stmt = stmt.where(FAQModel.domain_id == domain_id)
        stmt = stmt.order_by(FAQModel.priority.desc())
        result = await self.db.execute(stmt)
        return [self._to_domain(obj) for obj in result.scalars().all()]
