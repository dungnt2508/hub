"""Bot service - main orchestrator for query processing"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.routing_service import RoutingService
from backend.services.intent_service import IntentService
from backend.services.guardrail_service import GuardrailService
from backend.services.domain_handler_service import DomainHandlerService
from backend.repositories.observability_repository import ObservabilityRepository
from backend.contexts.request_context import RequestContext
from backend.errors.domain_errors import (
    IntentNotFoundError,
    GuardrailViolationError,
    NoActionConfiguredError,
    DataNotFoundError,
)


class BotService:
    """
    Main bot service - orchestrates query processing.
    
    Responsibilities:
    - Orchestrate flow: guardrail → routing → intent → domain handler
    - Log results
    - Return response
    
    Does NOT:
    - Query database directly
    - Handle domain-specific logic
    - Process business rules
    """
    
    def __init__(self, session: AsyncSession):
        self.routing_service = RoutingService(session)
        self.intent_service = IntentService(session)
        self.guardrail_service = GuardrailService(session)
        self.domain_handler = DomainHandlerService(session)
        self.observability_repo = ObservabilityRepository(session)
    
    async def process_query(
        self,
        tenant_id: UUID,
        channel_id: UUID | None,
        query_text: str
    ) -> Dict[str, Any]:
        """
        Process user query - main entry point.
        
        Runtime flow:
        1. Check guardrails
        2. Route to intent
        3. Get intent actions
        4. Execute action
        5. Get answer from domain handler (if query_db)
        6. Log conversation
        7. Return response
        """
        context = RequestContext(
            tenant_id=tenant_id,
            channel_id=channel_id,
            query_text=query_text
        )
        
        try:
            # Step 1: Check guardrails
            guardrail_result = await self.guardrail_service.check_guardrails(
                tenant_id=context.tenant_id,
                query_text=context.query_text
            )
            
        except GuardrailViolationError as e:
            # Log and return fallback
            await self._log_failure(context, None, None)
            return {
                "success": False,
                "message": e.fallback_message,
                "reason": "guardrail_violation"
            }
        
        try:
            # Step 2: Route to intent
            intent = await self.routing_service.route_query(
                tenant_id=context.tenant_id,
                query_text=context.query_text
            )
            
            if not intent:
                raise IntentNotFoundError("No intent matched")
            
            context.intent_name = intent.name
            context.domain = intent.domain
            
            # Step 3: Get intent actions
            actions = await self.intent_service.get_intent_actions(
                intent.id,
                context.tenant_id
            )
            
            if not actions:
                raise NoActionConfiguredError(f"No actions configured for intent {intent.name}")
            
            # Step 4: Execute first action (highest priority)
            action = actions[0]
            context.action_config = action.config_json or {}
            
            action_result = await self.intent_service.execute_action(
                action=action,
                tenant_id=context.tenant_id,
                context={
                    "query": context.query_text,
                    "intent": context.intent_name,
                    "domain": context.domain
                }
            )
            
            # Step 5: Get answer from domain handler if needed
            if action.action_type == "query_db":
                try:
                    answer = await self.domain_handler.handle_query_db_action(
                        intent=intent,
                        action=action,
                        tenant_id=context.tenant_id,
                        query_text=context.query_text
                    )
                    
                    if answer:
                        action_result["answer"] = answer
                except DataNotFoundError:
                    # Data not found - action still succeeds but no answer
                    pass
            
            # Step 6: Log success
            await self._log_success(context)
            
            # Step 7: Return response
            return {
                "success": action_result.get("success", True),
                "intent": context.intent_name,
                "domain": context.domain,
                "action": action_result,
                "disclaimers": guardrail_result.get("disclaimers", [])
            }
            
        except IntentNotFoundError:
            await self._log_failure(context, None, None, "No intent matched")
            return {
                "success": False,
                "message": "Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng thử lại với cách diễn đạt khác.",
                "reason": "no_intent_matched"
            }
            
        except NoActionConfiguredError:
            await self._log_failure(context, context.intent_name, context.domain, "No action configured")
            return {
                "success": False,
                "message": "Xin lỗi, không có hành động được cấu hình cho intent này.",
                "reason": "no_action_configured"
            }
            
        except Exception as e:
            # Unexpected error
            await self._log_failure(context, context.intent_name, context.domain, str(e))
            return {
                "success": False,
                "message": "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn.",
                "reason": "internal_error"
            }
    
    async def _log_success(self, context: RequestContext) -> None:
        """Log successful conversation"""
        await self.observability_repo.create_conversation_log(
            tenant_id=context.tenant_id,
            channel_id=context.channel_id,
            intent=context.intent_name,
            domain=context.domain,
            success=True
        )
    
    async def _log_failure(
        self,
        context: RequestContext,
        intent: str | None,
        domain: str | None,
        reason: str | None = None
    ) -> None:
        """Log failed conversation"""
        await self.observability_repo.create_conversation_log(
            tenant_id=context.tenant_id,
            channel_id=context.channel_id,
            intent=intent,
            domain=domain,
            success=False
        )
        
        if reason:
            await self.observability_repo.create_failed_query(
                tenant_id=context.tenant_id,
                query=context.query_text,
                reason=reason
            )
