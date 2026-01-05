"""
API Handler - Interface Layer Entry Point

This is where HTTP/WebSocket requests enter the system.
Applies personalization and formats responses.
"""
from typing import Dict, Any, Optional

from ..router import RouterOrchestrator
from ..schemas import RouterRequest, RouterResponse
from ..personalization import PersonalizationService, ResponseFormatter
from ..shared.logger import logger
from ..shared.exceptions import RouterError, InvalidInputError, AuthenticationError


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
            metadata: Optional request metadata
            
        Returns:
            Formatted response dict with personalization
        """
        try:
            # Load user preferences
            preferences = await self.personalization_service.get_preferences(user_id)
            
            # Create router request
            request = RouterRequest(
                raw_message=raw_message,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
                preferences_context={
                    "tone": preferences.tone.value,
                    "style": preferences.style.value,
                    "language": preferences.language,
                }
            )
            
            # Route request
            router_response = await self.router.route(request)
            
            # Format response with personalization
            formatted_response = await self.response_formatter.format_router_response(
                router_response,
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
            
            return formatted_response
            
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

