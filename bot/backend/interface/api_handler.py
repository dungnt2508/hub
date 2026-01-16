"""
API Handler - Interface Layer Entry Point

This is where HTTP/WebSocket requests enter the system.
Applies personalization and formats responses.
"""
import asyncio
from typing import Dict, Any, Optional

from ..router import RouterOrchestrator
from ..schemas import RouterRequest, RouterResponse
from ..schemas.domain_types import DomainResult
from ..personalization import PersonalizationService, ResponseFormatter
from ..shared.logger import logger
from ..shared.exceptions import RouterError, InvalidInputError, AuthenticationError, DomainError
from ..shared.request_metadata import RequestMetadata
from ..shared.config import config
from ..infrastructure.session_repository import RedisSessionRepository
from ..router.conversation_state_machine import conversation_state_machine, ConversationState
from .domain_dispatcher import domain_dispatcher


class APIHandler:
    """
    Main API handler for Interface Layer.
    
    Responsibilities:
    - Receive HTTP/WebSocket requests
    - Load user preferences
    - Call router
    - Format response with personalization
    - Handle errors
    """
    
    def __init__(
        self,
        router: Optional[RouterOrchestrator] = None,
        personalization_service: Optional[PersonalizationService] = None,
        response_formatter: Optional[ResponseFormatter] = None,
        session_repository: Optional[RedisSessionRepository] = None
    ):
        """
        Initialize API handler.
        
        Args:
            router: Router orchestrator (injected)
            personalization_service: Personalization service (injected)
            response_formatter: Response formatter (injected)
            session_repository: Session repository (injected)
        """
        self.router = router or RouterOrchestrator()
        self.personalization_service = personalization_service or PersonalizationService()
        self.response_formatter = response_formatter or ResponseFormatter(
            self.personalization_service
        )
        self.session_repository = session_repository or RedisSessionRepository()
    
    async def handle_request(
        self,
        raw_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming request.
        
        Args:
            raw_message: User message
            user_id: User ID
            session_id: Optional session ID
            metadata: Optional request metadata (will be validated)
            
        Returns:
            Formatted response dict with personalization
        """
        try:
            # Validate metadata on entry
            if metadata is None:
                metadata = {}
            
            try:
                # Ensure metadata has required fields
                if not metadata.get("tenant_id"):
                    metadata["tenant_id"] = ""
                if not metadata.get("user_id"):
                    metadata["user_id"] = user_id
                
                # Validate metadata
                req_metadata = RequestMetadata.from_dict(metadata)
                metadata = req_metadata.to_dict()
            except InvalidInputError as e:
                logger.warning(
                    f"Invalid request metadata: {e}",
                    extra={"user_id": user_id}
                )
                # Return early with error response
                return {
                    "error": "INVALID_METADATA",
                    "message": str(e),
                    "avatar": {"emoji": "🤖", "url": None, "name": "Bot"},
                }
            
            # Create router request
            request = RouterRequest(
                raw_message=raw_message,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
                preferences_context={}  # Will be populated after routing
            )
            
            # Route request (this is the critical path - should be fast)
            router_response = await self.router.route(request)
            
            # Dispatch to domain handler if routed
            try:
                domain_result = await domain_dispatcher.dispatch(
                    router_response,
                    user_id,
                    metadata
                )
                
                # Persist session after domain response (F1.1)
                if router_response.session_id and router_response.status == "ROUTED":
                    await self._update_session_after_domain_response(
                        router_response,
                        domain_result,
                        user_id
                    )
            except (InvalidInputError, DomainError) as e:
                logger.warning(
                    f"Domain dispatch failed: {e}",
                    extra={
                        "user_id": user_id,
                        "trace_id": router_response.trace_id,
                    }
                )
                # Fallback to router response
                domain_result = {
                    "message": str(e),
                    "status": "ERROR",
                    "trace_id": router_response.trace_id,
                    "domain": router_response.domain,
                    "intent": router_response.intent,
                }
            
            # Lazy load preferences (after routing, less critical)
            try:
                preferences = await asyncio.wait_for(
                    self.personalization_service.get_preferences(user_id),
                    timeout=1.0  # Fail fast
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load preferences: {e}",
                    extra={"user_id": user_id}
                )
                # Use defaults
                from ..personalization import Preferences
                preferences = Preferences()  # Default preferences
            
            # Format response with personalization
            # ResponseFormatter will load preferences internally
            formatted_response = await self.response_formatter.format_router_response(
                domain_result if isinstance(domain_result, RouterResponse) else router_response,
                user_id
            )
            
            logger.info(
                "Request handled successfully",
                extra={
                    "user_id": user_id,
                    "trace_id": router_response.trace_id,
                    "status": router_response.status,
                }
            )
            
            return {
                **formatted_response,
                **(domain_result if isinstance(domain_result, dict) and domain_result.get("data") else {})
            }
            
        except InvalidInputError as e:
            logger.warning(
                f"Invalid input: {e}",
                extra={"user_id": user_id}
            )
            return {
                "error": "INVALID_INPUT",
                "message": str(e),
                "avatar": await self._get_default_avatar(user_id),
            }
            
        except RouterError as e:
            logger.error(
                f"Router error: {e}",
                extra={"user_id": user_id},
                exc_info=True
            )
            return {
                "error": "ROUTER_ERROR",
                "message": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
                "avatar": await self._get_default_avatar(user_id),
            }
            
        except Exception as e:
            logger.error(
                f"Unexpected error: {e}",
                extra={"user_id": user_id},
                exc_info=True
            )
            return {
                "error": "SYSTEM_ERROR",
                "message": "Xin lỗi, có lỗi hệ thống. Vui lòng thử lại sau.",
                "avatar": await self._get_default_avatar(user_id),
            }
    
    async def _get_default_avatar(self, user_id: str) -> Dict[str, Any]:
        """Get default avatar for error responses"""
        preferences = await self.personalization_service.get_preferences(user_id)
        return {
            "emoji": preferences.avatar.avatar_emoji or "🤖",
            "url": preferences.avatar.avatar_url,
            "name": preferences.avatar.custom_name or "Bot",
        }
    
    async def _update_session_after_domain_response(
        self,
        router_response: RouterResponse,
        domain_result: Dict[str, Any],
        user_id: str
    ) -> None:
        """
        Update session state after domain response.
        
        This implements F1.1: Session Persistence Sau Domain Response.
        
        Args:
            router_response: Router response with domain/intent
            domain_result: Domain handler response
            user_id: User ID for validation
        """
        if not router_response.session_id:
            return
        
        try:
            # Load session
            session_state = await self.session_repository.get(router_response.session_id)
            if not session_state:
                logger.warning(
                    f"Session not found for persistence: {router_response.session_id}",
                    extra={"user_id": user_id, "trace_id": router_response.trace_id}
                )
                return
            
            # Validate user_id matches
            if session_state.user_id != user_id:
                logger.warning(
                    f"User ID mismatch in session: expected {user_id}, got {session_state.user_id}",
                    extra={"trace_id": router_response.trace_id}
                )
                return
            
            # Update session based on domain response status and next_action (F2.3)
            domain_status = domain_result.get("status")
            next_action = domain_result.get("next_action")
            next_action_params = domain_result.get("next_action_params", {})
            
            # Transition state based on domain response (F3.2)
            try:
                if domain_status == DomainResult.NEED_MORE_INFO.value:
                    session_state.conversation_state = conversation_state_machine.transition(
                        session_state.conversation_state,
                        ConversationState.NEED_INFO,
                        context={"domain": router_response.domain, "intent": router_response.intent}
                    )
                elif domain_status == DomainResult.SUCCESS.value:
                    session_state.conversation_state = conversation_state_machine.transition(
                        session_state.conversation_state,
                        ConversationState.COMPLETE,
                        context={"domain": router_response.domain, "intent": router_response.intent}
                    )
                elif domain_status in [
                    DomainResult.ERROR.value,
                    DomainResult.SYSTEM_ERROR.value,
                    DomainResult.INVALID_REQUEST.value
                ]:
                    session_state.conversation_state = conversation_state_machine.transition(
                        session_state.conversation_state,
                        ConversationState.ERROR,
                        context={"error": domain_status}
                    )
            except ValueError as e:
                logger.warning(
                    f"Invalid state transition: {e}",
                    extra={
                        "current_state": session_state.conversation_state.value,
                        "domain_status": domain_status,
                        "trace_id": router_response.trace_id,
                    }
                )
            
            if domain_status == DomainResult.NEED_MORE_INFO.value:
                # User needs to provide more information
                session_state.active_domain = router_response.domain
                session_state.pending_intent = router_response.intent
                session_state.missing_slots = domain_result.get("missing_slots", [])
                # Keep last_domain and last_intent for context
                if router_response.domain:
                    session_state.last_domain = router_response.domain
                if router_response.intent:
                    session_state.last_intent = router_response.intent
                    session_state.last_intent_type = router_response.intent_type
                
                logger.debug(
                    "Session updated for NEED_MORE_INFO",
                    extra={
                        "session_id": session_state.session_id,
                        "pending_intent": session_state.pending_intent,
                        "missing_slots": session_state.missing_slots,
                        "next_action": next_action,
                        "next_action_params": next_action_params,
                    }
                )
            elif domain_status == DomainResult.SUCCESS.value:
                # Intent completed successfully
                # Clear pending state
                session_state.active_domain = None
                session_state.pending_intent = None
                session_state.missing_slots = []
                # Reset retry_count on success (F4.3)
                session_state.retry_count = 0
                session_state.escalation_flag = False
                # Update last_domain and last_intent for context
                if router_response.domain:
                    session_state.last_domain = router_response.domain
                if router_response.intent:
                    session_state.last_intent = router_response.intent
                    session_state.last_intent_type = router_response.intent_type
                # Clear slots after successful completion
                session_state.clear_slots()
                # Transition to IDLE after completion
                try:
                    session_state.conversation_state = conversation_state_machine.transition(
                        session_state.conversation_state,
                        ConversationState.IDLE
                    )
                except ValueError:
                    pass  # Already handled above
                
                logger.debug(
                    "Session updated for SUCCESS",
                    extra={
                        "session_id": session_state.session_id,
                        "last_domain": session_state.last_domain,
                        "last_intent": session_state.last_intent,
                        "conversation_state": session_state.conversation_state.value,
                    }
                )
            else:
                # For other statuses (ERROR, REJECT, etc.), increment retry_count (F4.3)
                if domain_status in [
                    DomainResult.ERROR.value,
                    DomainResult.SYSTEM_ERROR.value,
                    DomainResult.INVALID_REQUEST.value
                ]:
                    session_state.retry_count += 1
                    logger.debug(
                        "Incremented retry_count after error",
                        extra={
                            "session_id": session_state.session_id,
                            "retry_count": session_state.retry_count,
                            "threshold": config.ESCALATION_RETRY_THRESHOLD,
                        }
                    )
                
                # Update last_domain and last_intent
                if router_response.domain:
                    session_state.last_domain = router_response.domain
                if router_response.intent:
                    session_state.last_intent = router_response.intent
                    session_state.last_intent_type = router_response.intent_type
                
                # Reset retry_count on success (even if not SUCCESS status, but not error)
                if domain_status not in [
                    DomainResult.ERROR.value,
                    DomainResult.SYSTEM_ERROR.value,
                    DomainResult.INVALID_REQUEST.value
                ]:
                    session_state.retry_count = 0
            
            # Persist session
            await self.session_repository.save(session_state)
            
            logger.debug(
                "Session persisted after domain response",
                extra={
                    "session_id": session_state.session_id,
                    "status": domain_status,
                    "trace_id": router_response.trace_id,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to update session after domain response: {e}",
                extra={
                    "session_id": router_response.session_id,
                    "trace_id": router_response.trace_id,
                },
                exc_info=True
            )
            # Don't raise - session persistence is not critical for response
    
    @staticmethod
    def format_error_response(
        error_type: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format standardized error response.
        
        Args:
            error_type: Error type (e.g., "INVALID_INPUT", "AUTHENTICATION_ERROR")
            message: Error message
            status_code: HTTP status code
            details: Optional additional details
            
        Returns:
            Formatted error response dict
        """
        response = {
            "error": True,
            "message": message,
            "status_code": status_code,
        }
        
        if details:
            response["details"] = details
        
        return response
    
    @staticmethod
    def format_success_response(
        data: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format standardized success response.
        
        Args:
            data: Response data
            trace_id: Optional trace ID
            
        Returns:
            Formatted success response dict
        """
        response = {
            "success": True,
            "data": data,
        }
        
        if trace_id:
            response["data"]["traceId"] = trace_id
        
        return response

