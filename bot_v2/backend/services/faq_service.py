"""FAQ service - handles FAQ queries"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.catalog import FAQ


class FAQService:
    """Service for FAQ queries"""
    
    def __init__(self, session: AsyncSession):
        self.catalog_repo = CatalogRepository(session)
    
    async def get_faq_answer(
        self,
        tenant_id: UUID,
        question: str,
        product_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get FAQ answer.
        ONLY from faqs table.
        """
        # Get FAQs - try product-specific first, then global
        faqs = await self.catalog_repo.get_faqs(
            tenant_id=tenant_id,
            product_id=product_id,
            scope="product" if product_id else "global"
        )
        
        # Simple keyword matching (in production, might use more sophisticated matching)
        question_lower = question.lower()
        
        for faq in faqs:
            # Check if question matches FAQ question
            if any(keyword in question_lower for keyword in faq.question.lower().split()):
                return {
                    "question": faq.question,
                    "answer": faq.answer,
                    "scope": faq.scope,
                    "product_id": str(faq.product_id) if faq.product_id else None
                }
        
        return None
