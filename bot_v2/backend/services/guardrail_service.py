"""Guardrail service - enforces safety and legal constraints"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.catalog import Guardrail
from backend.policies.guardrail_policy import GuardrailPolicy
from backend.errors.domain_errors import GuardrailViolationError


class GuardrailService:
    """Service for guardrail enforcement"""
    
    def __init__(self, session: AsyncSession):
        self.catalog_repo = CatalogRepository(session)
        self.policy = GuardrailPolicy()
    
    async def check_guardrails(
        self,
        tenant_id: UUID,
        query_text: str
    ) -> Dict[str, Any]:
        """
        Check if query violates guardrails.
        If violation → raise GuardrailViolationError.
        
        Returns:
            {
                "violated": bool,
                "allowed": bool,
                "disclaimers": list (if not violated)
            }
        """
        guardrail = await self.catalog_repo.get_guardrail(tenant_id)
        
        if not guardrail:
            return {
                "violated": False,
                "allowed": True,
                "disclaimers": []
            }
        
        # Use policy to check
        result = self.policy.check_query(guardrail, query_text)
        
        if result["violated"]:
            raise GuardrailViolationError(
                message=result["reason"],
                fallback_message=result["fallback_message"]
            )
        
        return {
            "violated": False,
            "allowed": True,
            "disclaimers": result["disclaimers"]
        }
