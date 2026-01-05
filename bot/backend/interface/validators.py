"""
Request Validators - Centralized validation logic
"""
from typing import Dict, Any, Optional
from fastapi import Request

from ..shared.logger import logger
from ..shared.exceptions import InvalidInputError


class RequestValidator:
    """
    Centralized request validation.
    
    Handles:
    - JSON parsing
    - Required field validation
    - Type validation
    - Message validation
    """
    
    @staticmethod
    async def parse_json_body(request: Request) -> Dict[str, Any]:
        """
        Parse JSON body from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Parsed JSON body
            
        Raises:
            InvalidInputError: If JSON parsing fails
        """
        try:
            body = await request.json()
            return body
        except ValueError as e:
            logger.warning(f"Invalid JSON in request body: {e}")
            raise InvalidInputError("Invalid JSON in request body") from e
        except Exception as e:
            logger.warning(f"Failed to parse request body: {e}")
            raise InvalidInputError("Failed to parse request body") from e
    
    @staticmethod
    def validate_required_fields(body: Dict[str, Any], required_fields: list[str]) -> None:
        """
        Validate required fields are present.
        
        Args:
            body: Request body dict
            required_fields: List of required field names
            
        Raises:
            InvalidInputError: If any required field is missing
        """
        missing = []
        for field in required_fields:
            if field not in body or body[field] is None:
                missing.append(field)
        
        if missing:
            raise InvalidInputError(f"Missing required fields: {', '.join(missing)}")
    
    @staticmethod
    def validate_message(message: Optional[str]) -> str:
        """
        Validate and normalize message.
        
        Args:
            message: Message string (can be None)
            
        Returns:
            Normalized message string
            
        Raises:
            InvalidInputError: If message is empty or invalid
        """
        if not message:
            raise InvalidInputError("message is required and non-empty")
        
        message = message.strip()
        if not message:
            raise InvalidInputError("message cannot be empty or whitespace only")
        
        # Check max length
        from ..shared.config import config
        if len(message) > config.MAX_MESSAGE_LENGTH:
            raise InvalidInputError(
                f"message exceeds maximum length of {config.MAX_MESSAGE_LENGTH} characters"
            )
        
        return message
    
    @staticmethod
    def validate_bot_message_request(body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate bot message request body.
        
        Args:
            body: Request body dict
            
        Returns:
            Validated and normalized request data:
            {
                "message": str,
                "session_id": Optional[str],
                "attachments": list
            }
            
        Raises:
            InvalidInputError: If validation fails
        """
        # Validate required fields
        RequestValidator.validate_required_fields(body, ["message"])
        
        # Validate and normalize message
        message = RequestValidator.validate_message(body.get("message"))
        
        # Extract optional fields
        session_id = body.get("sessionId") or body.get("session_id")
        attachments = body.get("attachments", [])
        
        # Validate attachments if present
        if attachments and not isinstance(attachments, list):
            raise InvalidInputError("attachments must be a list")
        
        return {
            "message": message,
            "session_id": session_id,
            "attachments": attachments,
        }

