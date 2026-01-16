"""
Domain Dispatcher - Routes domain requests to appropriate domain handlers

This module dispatches DomainRequest to the correct domain handler
based on the domain field in the request.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from ..schemas import DomainRequest, DomainResponse, DomainResult, RouterResponse
from ..domain.hr.entry_handler import HREntryHandler
from ..domain.catalog.entry_handler import CatalogEntryHandler
from ..domain.dba.entry_handler import DBAEntryHandler
from ..infrastructure.session_repository import RedisSessionRepository
from ..shared.logger import logger
from ..shared.exceptions import DomainError, InvalidInputError


class DomainDispatcher:
    """
    Dispatches domain requests to appropriate domain handlers.
    
    Supports:
    - HR Domain (OPERATION intents)
    - Catalog Domain (KNOWLEDGE intents)
    - DBA Domain (OPERATION intents)
    """
    
    def __init__(self):
        """Initialize domain dispatcher with all domain handlers"""
        self.handlers: Dict[str, Any] = {
            "hr": HREntryHandler(),
            "catalog": CatalogEntryHandler(),
            "dba": DBAEntryHandler(),
        }
        self.session_repository = RedisSessionRepository()
        logger.info(f"DomainDispatcher initialized with {len(self.handlers)} handlers")
    
    async def dispatch(
        self,
        router_response: RouterResponse,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispatch router response to appropriate domain handler.
        
        Args:
            router_response: Response from router with domain and intent
            user_id: User ID
            metadata: Optional request metadata
            
        Returns:
            Formatted response with domain result
            
        Raises:
            DomainError: If domain handling fails
        """
        try:
            # Check if this is a routed request (not META_HANDLED or UNKNOWN)
            if router_response.status != "ROUTED":
                # Not a routed domain request, return router response as-is
                logger.debug(
                    f"Not a routed request, skipping dispatcher",
                    extra={
                        "trace_id": router_response.trace_id,
                        "status": router_response.status,
                    }
                )
                return self._format_non_domain_response(router_response)
            
            # Get domain and intent
            domain = router_response.domain
            intent = router_response.intent
            
            if not domain or not intent:
                logger.warning(
                    "Router response missing domain or intent",
                    extra={
                        "trace_id": router_response.trace_id,
                        "domain": domain,
                        "intent": intent,
                    }
                )
                raise InvalidInputError("Domain and intent are required for ROUTED requests")
            
            # Check if domain handler exists
            if domain not in self.handlers:
                logger.warning(
                    f"Unknown domain: {domain}",
                    extra={
                        "trace_id": router_response.trace_id,
                        "domain": domain,
                    }
                )
                raise DomainError(f"Unknown domain: {domain}")
            
            # Merge session slots with router slots (F2.2)
            merged_slots = await self._merge_session_slots(
                router_response.session_id,
                router_response.slots or {},
                user_id
            )
            
            # Create domain request from router response
            domain_request = DomainRequest(
                domain=domain,
                intent=intent,
                intent_type=router_response.intent_type or "OPERATION",
                slots=merged_slots,
                user_context={
                    "user_id": user_id,
                    "tenant_id": metadata.get("tenant_id") if metadata else None,
                    "channel": metadata.get("channel") if metadata else None,
                    "raw_message": router_response.message or "",
                },
                trace_id=router_response.trace_id,
            )
            
            logger.info(
                "Dispatching to domain handler",
                extra={
                    "trace_id": router_response.trace_id,
                    "domain": domain,
                    "intent": intent,
                    "user_id": user_id,
                }
            )
            
            # Get handler and execute
            handler = self.handlers[domain]
            domain_response = await handler.handle(domain_request)
            
            logger.info(
                "Domain handler executed",
                extra={
                    "trace_id": router_response.trace_id,
                    "domain": domain,
                    "intent": intent,
                    "status": domain_response.status,
                }
            )
            
            # Format response
            return self._format_domain_response(
                domain_response,
                router_response,
                domain,
                intent
            )
            
        except InvalidInputError:
            raise
        except DomainError:
            raise
        except Exception as e:
            logger.error(
                f"Error in domain dispatcher: {e}",
                extra={"trace_id": router_response.trace_id},
                exc_info=True
            )
            raise DomainError(f"Domain dispatch failed: {e}") from e
    
    @staticmethod
    def _format_non_domain_response(router_response: RouterResponse) -> Dict[str, Any]:
        """
        Format response for non-domain requests (META_HANDLED, UNKNOWN).
        
        Args:
            router_response: Router response
            
        Returns:
            Formatted response dict
        """
        return {
            "message": router_response.message,
            "status": router_response.status,
            "trace_id": router_response.trace_id,
            "domain": router_response.domain,
            "intent": router_response.intent,
            "source": router_response.source,
        }
    
    @staticmethod
    def _format_domain_response(
        domain_response: DomainResponse,
        router_response: RouterResponse,
        domain: str,
        intent: str
    ) -> Dict[str, Any]:
        """
        Format domain response for API output.
        
        Args:
            domain_response: Domain handler response
            router_response: Original router response
            domain: Domain name
            intent: Intent name
            
        Returns:
            Formatted response dict
        """
        response = {
            "status": domain_response.status.value,
            "message": domain_response.message,
            "trace_id": router_response.trace_id,
            "domain": domain,
            "intent": intent,
            "confidence": router_response.confidence,
        }
        
        # Add data if success
        if domain_response.status == DomainResult.SUCCESS and domain_response.data:
            response["data"] = domain_response.data
        
        # Add missing slots if need more info
        if domain_response.status == DomainResult.NEED_MORE_INFO:
            response["missing_slots"] = domain_response.missing_slots
        
        # Add next_action and next_action_params (F2.3)
        if domain_response.next_action:
            response["next_action"] = domain_response.next_action
        if domain_response.next_action_params:
            response["next_action_params"] = domain_response.next_action_params
        
        # Add error details if error
        if domain_response.status in [
            DomainResult.ERROR,
            DomainResult.SYSTEM_ERROR,
            DomainResult.INVALID_REQUEST
        ]:
            if domain_response.error_code:
                response["error_code"] = domain_response.error_code
            if domain_response.error_details:
                response["error_details"] = domain_response.error_details
        
        # Add audit info if present
        if domain_response.audit:
            response["audit"] = domain_response.audit
        
        return response
    
    async def _merge_session_slots(
        self,
        session_id: Optional[str],
        router_slots: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Merge session slots with router slots.
        
        This implements F2.2: Domain Dispatcher Merge Session Slots.
        Session slots take precedence (they're from previous turns).
        
        Args:
            session_id: Session ID from router response
            router_slots: Slots extracted by router
            user_id: User ID for validation
            
        Returns:
            Merged slots dict
        """
        if not session_id:
            # No session, return router slots only
            return router_slots.copy()
        
        try:
            # Load session
            session_state = await self.session_repository.get(session_id)
            if not session_state:
                logger.debug(
                    f"Session not found for slot merge: {session_id}",
                    extra={"user_id": user_id}
                )
                return router_slots.copy()
            
            # Validate user_id matches
            if session_state.user_id != user_id:
                logger.warning(
                    f"User ID mismatch in session for slot merge: expected {user_id}, got {session_state.user_id}",
                    extra={"session_id": session_id}
                )
                return router_slots.copy()
            
            # Merge: session slots first (from previous turns), then router slots (new)
            merged = session_state.slots_memory.copy()
            merged.update(router_slots)  # Router slots override session slots if conflict
            
            logger.debug(
                "Slots merged from session and router",
                extra={
                    "session_id": session_id,
                    "session_slots_count": len(session_state.slots_memory),
                    "router_slots_count": len(router_slots),
                    "merged_slots_count": len(merged),
                }
            )
            
            return merged
            
        except Exception as e:
            logger.error(
                f"Failed to merge session slots: {e}",
                extra={"session_id": session_id, "user_id": user_id},
                exc_info=True
            )
            # Return router slots only on error
            return router_slots.copy()


# Global dispatcher instance
domain_dispatcher = DomainDispatcher()
