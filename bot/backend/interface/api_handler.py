"""
API Handler - Interface Layer Entry Point

This is where HTTP/WebSocket requests enter the system.
Applies personalization and formats responses.
"""
import asyncio
from typing import Dict, Any, Optional

from ..router import RouterOrchestrator
from ..schemas import RouterRequest, RouterResponse
from ..personalization import PersonalizationService, ResponseFormatter
from ..shared.logger import logger
from ..shared.exceptions import RouterError, InvalidInputError, AuthenticationError, DomainError
from ..shared.request_metadata import RequestMetadata
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
        response_formatter: Optional[ResponseFormatter] = None
    ):
        """
        Initialize API handler.
        
        Args:
            router: Router orchestrator (injected)
            personalization_service: Personalization service (injected)
            response_formatter: Response formatter (injected)
        """
        self.router = router or RouterOrchestrator()
        self.personalization_service = personalization_service or PersonalizationService()
        self.response_formatter = response_formatter or ResponseFormatter(
            self.personalization_service
        )
    
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
            
            # Add preferences context to response formatting
            preferences_context = {
                "tone": preferences.tone.value if preferences else "neutral",
                "style": preferences.style.value if preferences else "informative",
                "language": preferences.language if preferences else "vi",
            }
            
            # Format response with personalization
            formatted_response = await self.response_formatter.format_router_response(
                domain_result if isinstance(domain_result, RouterResponse) else router_response,
                user_id,
                preferences_context=preferences_context
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

