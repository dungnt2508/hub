"""Routing service - routes user input to intents"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.intent_repository import IntentRepository
from backend.repositories.catalog_repository import CatalogRepository
from backend.domain.intent import Intent
from backend.config import settings


class RoutingService:
    """Service for routing user queries to intents"""
    
    def __init__(self, session: AsyncSession):
        self.intent_repo = IntentRepository(session)
        self.catalog_repo = CatalogRepository(session)
    
    async def route_query(
        self,
        tenant_id: UUID,
        query_text: str
    ) -> Optional[Intent]:
        """
        Route user query to an intent.
        
        Process:
        1. Pattern matching (shortlist)
        2. LLM-based intent resolution (if needed)
        3. Return matched intent or None
        """
        # Step 1: Pattern matching to shortlist intents
        candidate_intents = await self.intent_repo.find_intents_by_patterns(
            tenant_id=tenant_id,
            query_text=query_text
        )
        
        if not candidate_intents:
            return None
        
        # Step 2: If multiple candidates, use LLM to resolve (if configured)
        if len(candidate_intents) == 1:
            return candidate_intents[0]
        
        # Multiple candidates - use LLM if available
        if settings.llm_provider and settings.llm_api_key:
            resolved_intent = await self._resolve_intent_with_llm(
                tenant_id=tenant_id,
                query_text=query_text,
                candidate_intents=candidate_intents
            )
            return resolved_intent
        
        # No LLM - return highest priority intent
        return candidate_intents[0]
    
    async def _resolve_intent_with_llm(
        self,
        tenant_id: UUID,
        query_text: str,
        candidate_intents: List[Intent]
    ) -> Optional[Intent]:
        """Use LLM to resolve intent from candidates"""
        try:
            # Get hints for all candidate intents
            intent_hints_map = {}
            for intent in candidate_intents:
                hints = await self.intent_repo.get_intent_hints(intent.id)
                intent_hints_map[intent.id] = [h.hint_text for h in hints]
            
            # Build prompt for LLM
            hints_text = "\n".join([
                f"- {intent.name} ({intent.domain}): {', '.join(intent_hints_map.get(intent.id, []))}"
                for intent in candidate_intents
            ])
            
            prompt = f"""You are an intent classifier for a catalog chatbot.
Given the user query, choose the most appropriate intent from the candidates.

User query: {query_text}

Available intents:
{hints_text}

Respond with ONLY the intent name (e.g., "ask_price", "compare", "suitability").
Do not explain, do not add any other text."""
            
            # Call LLM (simplified - in production, use proper client)
            if settings.llm_provider == "openai":
                import openai
                client = openai.AsyncOpenAI(
                    api_key=settings.llm_api_key,
                    base_url=settings.llm_base_url
                )
                response = await client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": "You are an intent classifier. Respond with only the intent name."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=50
                )
                intent_name = response.choices[0].message.content.strip()
                
                # Find matching intent
                for intent in candidate_intents:
                    if intent.name.lower() == intent_name.lower():
                        return intent
            
            # Fallback: return highest priority
            return candidate_intents[0]
            
        except Exception as e:
            # Log error and fallback
            print(f"LLM intent resolution failed: {e}")
            return candidate_intents[0]
