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
from ..shared.exceptions import RouterError, InvalidInputError
from ..shared.error_formatter import ErrorFormatter, ErrorCode


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
            metadata: Optional request metadata (must contain tenant_id)
            
        Returns:
            Formatted response dict with personalization
        """
        try:
            # Task 7.3: Extract tenant_id from metadata
            if not metadata or "tenant_id" not in metadata:
                raise InvalidInputError("tenant_id is required in metadata")
            
            tenant_id = metadata.get("tenant_id")
            if not tenant_id or not tenant_id.strip():
                raise InvalidInputError("tenant_id cannot be empty")
            
            # Load user preferences
            preferences = await self.personalization_service.get_preferences(user_id)
            
            # Create router request
            request = RouterRequest(
                raw_message=raw_message,
                user_id=user_id,
                tenant_id=tenant_id,  # Task 7.3: Pass tenant_id to RouterRequest
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
            # Task 8: Use standardized error formatter
            error_response = ErrorFormatter.format_exception(
                exception=e,
                status_code=400,
                log_context={
                    "user_id": user_id,
                    "tenant_id": metadata.get("tenant_id") if metadata else None,
                }
            )
            # Add avatar for user-facing errors
            error_response["avatar"] = await self._get_default_avatar(user_id)
            return error_response
            
        except RouterError as e:
            # Task 8: Use standardized error formatter
            error_response = ErrorFormatter.format_exception(
                exception=e,
                status_code=500,
                log_context={
                    "user_id": user_id,
                    "tenant_id": metadata.get("tenant_id") if metadata else None,
                }
            )
            # Add avatar for user-facing errors
            error_response["avatar"] = await self._get_default_avatar(user_id)
            return error_response
            
        except Exception as e:
            # Task 8: Use standardized error formatter
            error_response = ErrorFormatter.format_exception(
                exception=e,
                status_code=500,
                log_context={
                    "user_id": user_id,
                    "tenant_id": metadata.get("tenant_id") if metadata else None,
                }
            )
            # Add avatar for user-facing errors
            error_response["avatar"] = await self._get_default_avatar(user_id)
            return error_response
    
    async def _get_default_avatar(self, user_id: str) -> Dict[str, Any]:
        """Get default avatar for error responses"""
        preferences = await self.personalization_service.get_preferences(user_id)
        return {
            "emoji": preferences.avatar.avatar_emoji or "🤖",
            "url": preferences.avatar.avatar_url,
            "name": preferences.avatar.custom_name or "Bot",
        }

