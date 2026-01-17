"""Intent service - handles intent actions"""
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.intent_repository import IntentRepository
from backend.domain.intent import Intent, IntentAction


class IntentService:
    """Service for handling intent actions"""
    
    def __init__(self, session: AsyncSession):
        self.intent_repo = IntentRepository(session)
    
    async def get_intent_actions(
        self,
        intent_id: UUID,
        tenant_id: UUID
    ) -> List[IntentAction]:
        """Get actions for an intent, ordered by priority"""
        intent = await self.intent_repo.get_intent(intent_id, tenant_id)
        if not intent:
            return []
        
        actions = await self.intent_repo.get_intent_actions(intent_id)
        return sorted(actions, key=lambda a: a.priority, reverse=True)
    
    async def execute_action(
        self,
        action: IntentAction,
        tenant_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an intent action.
        
        Action types:
        - query_db: Query database for information
        - handoff: Hand off to human agent
        - refuse: Refuse the request
        - rag: Use RAG (if enabled)
        """
        if action.action_type == "query_db":
            return await self._execute_query_db(action, tenant_id, context)
        elif action.action_type == "handoff":
            return await self._execute_handoff(action, tenant_id, context)
        elif action.action_type == "refuse":
            return await self._execute_refuse(action, tenant_id, context)
        elif action.action_type == "rag":
            return await self._execute_rag(action, tenant_id, context)
        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action.action_type}"
            }
    
    async def _execute_query_db(
        self,
        action: IntentAction,
        tenant_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute query_db action - delegates to domain handlers"""
        # This will be handled by domain-specific services
        return {
            "success": True,
            "action_type": "query_db",
            "config": action.config_json,
            "context": context
        }
    
    async def _execute_handoff(
        self,
        action: IntentAction,
        tenant_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute handoff action"""
        config = action.config_json or {}
        return {
            "success": True,
            "action_type": "handoff",
            "message": config.get("message", "Chuyển tiếp đến nhân viên hỗ trợ..."),
            "cta": config.get("cta", {}),
        }
    
    async def _execute_refuse(
        self,
        action: IntentAction,
        tenant_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute refuse action"""
        config = action.config_json or {}
        return {
            "success": True,
            "action_type": "refuse",
            "message": config.get("message", "Xin lỗi, tôi không thể trả lời câu hỏi này."),
        }
    
    async def _execute_rag(
        self,
        action: IntentAction,
        tenant_id: UUID,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute RAG action (not implemented per requirements)"""
        return {
            "success": False,
            "error": "RAG not implemented per system requirements"
        }
