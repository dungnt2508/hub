"""Use case service - handles suitability queries"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.catalog import UseCase


class UseCaseService:
    """Service for use case/suitability queries"""
    
    def __init__(self, session: AsyncSession):
        self.catalog_repo = CatalogRepository(session)
    
    async def check_suitability(
        self,
        tenant_id: UUID,
        product_id: UUID,
        use_case_description: str
    ) -> Dict[str, Any]:
        """
        Check product suitability for a use case.
        ONLY from use_cases table.
        """
        use_cases = await self.catalog_repo.get_use_cases(
            product_id,
            tenant_id
        )
        
        # Check if use case matches any allowed/disallowed cases
        # Simple keyword matching (in production, might use more sophisticated matching)
        use_case_lower = use_case_description.lower()
        
        allowed = []
        disallowed = []
        
        for uc in use_cases:
            if uc.type == "allowed":
                if any(keyword in use_case_lower for keyword in uc.description.lower().split()):
                    allowed.append(uc.description)
            elif uc.type == "disallowed":
                if any(keyword in use_case_lower for keyword in uc.description.lower().split()):
                    disallowed.append(uc.description)
        
        if disallowed:
            return {
                "suitable": False,
                "reason": "Sản phẩm không phù hợp cho trường hợp sử dụng này.",
                "disallowed_cases": disallowed
            }
        
        if allowed:
            return {
                "suitable": True,
                "reason": "Sản phẩm phù hợp cho trường hợp sử dụng này.",
                "allowed_cases": allowed
            }
        
        # No explicit use case found
        return {
            "suitable": None,
            "reason": "Không có thông tin về trường hợp sử dụng này trong cơ sở dữ liệu."
        }
