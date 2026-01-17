"""Domain handler service - routes to appropriate domain service"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.intent import Intent, IntentAction
from backend.services.product_service import ProductService
from backend.services.faq_service import FAQService
from backend.services.use_case_service import UseCaseService
from backend.services.comparison_service import ComparisonService
from backend.errors.domain_errors import DataNotFoundError


class DomainHandlerService:
    """Service for routing to domain-specific handlers"""
    
    def __init__(self, session: AsyncSession):
        self.product_service = ProductService(session)
        self.faq_service = FAQService(session)
        self.use_case_service = UseCaseService(session)
        self.comparison_service = ComparisonService(session)
    
    async def handle_query_db_action(
        self,
        intent: Intent,
        action: IntentAction,
        tenant_id: UUID,
        query_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle query_db action by routing to appropriate domain service.
        
        Returns:
            Answer dict or None if no answer found
        """
        action_config = action.config_json or {}
        handler = action_config.get("handler")
        
        # Route based on intent domain and handler config
        if intent.domain == "product":
            return await self._handle_product_domain(
                intent=intent,
                handler=handler,
                tenant_id=tenant_id,
                query_text=query_text,
                action_config=action_config
            )
        
        # Try FAQ as fallback
        return await self._try_faq(tenant_id, query_text, action_config)
    
    async def _handle_product_domain(
        self,
        intent: Intent,
        handler: Optional[str],
        tenant_id: UUID,
        query_text: str,
        action_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle product domain queries"""
        
        # Price query
        if intent.name == "ask_price" or handler == "product_price":
            product_id = action_config.get("product_id")
            sku = action_config.get("sku")
            
            if product_id or sku:
                try:
                    price_info = await self.product_service.get_price(
                        tenant_id=tenant_id,
                        product_id=product_id,
                        sku=sku
                    )
                    return price_info
                except DataNotFoundError:
                    pass
        
        # Comparison query
        elif intent.name == "compare" or handler == "product_comparison":
            product_a_id = action_config.get("product_a_id")
            product_b_id = action_config.get("product_b_id")
            
            if product_a_id and product_b_id:
                try:
                    comparison = await self.comparison_service.compare_products(
                        tenant_id=tenant_id,
                        product_a_id=product_a_id,
                        product_b_id=product_b_id
                    )
                    return {
                        "type": "product_comparison",
                        "comparison": comparison
                    }
                except DataNotFoundError:
                    pass
        
        # Suitability query
        elif intent.name == "suitability" or handler == "suitability_check":
            product_id = action_config.get("product_id")
            use_case = action_config.get("use_case", query_text)
            
            if product_id:
                suitability = await self.use_case_service.check_suitability(
                    tenant_id=tenant_id,
                    product_id=product_id,
                    use_case_description=use_case
                )
                return {
                    "type": "suitability_check",
                    "suitability": suitability
                }
        
        return None
    
    async def _try_faq(
        self,
        tenant_id: UUID,
        query_text: str,
        action_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to get FAQ answer"""
        product_id = action_config.get("product_id")
        
        faq_answer = await self.faq_service.get_faq_answer(
            tenant_id=tenant_id,
            question=query_text,
            product_id=product_id
        )
        
        if faq_answer:
            return {
                "type": "faq",
                "faq": faq_answer
            }
        
        return None
