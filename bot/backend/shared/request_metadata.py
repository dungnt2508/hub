"""
Request Metadata Schema - Validate and standardize request metadata
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from uuid import UUID
import uuid

from .exceptions import InvalidInputError
from .logger import logger


@dataclass
class RequestMetadata:
    """
    Standardized request metadata.
    
    All incoming requests must be validated against this schema.
    """
    tenant_id: str
    user_id: str
    channel: str = "web"  # web, mobile, api, etc.
    session_id: Optional[str] = None
    
    def validate(self) -> None:
        """
        Validate metadata constraints.
        
        Raises:
            InvalidInputError: If validation fails
        """
        if not self.tenant_id or not self.tenant_id.strip():
            raise InvalidInputError("tenant_id is required and non-empty")
        
        if not self.user_id or not self.user_id.strip():
            raise InvalidInputError("user_id is required and non-empty")
        
        # Try to parse tenant_id as UUID
        try:
            uuid.UUID(self.tenant_id)
        except ValueError:
            raise InvalidInputError(
                f"tenant_id must be a valid UUID, got: {self.tenant_id}"
            )
        
        # Validate channel
        valid_channels = ["web", "mobile", "api", "internal"]
        if self.channel not in valid_channels:
            logger.warning(
                f"Unknown channel: {self.channel}, using default 'web'"
            )
            self.channel = "web"
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'RequestMetadata':
        """
        Create RequestMetadata from dictionary.
        
        Args:
            data: Dictionary with metadata
            
        Returns:
            RequestMetadata instance
            
        Raises:
            InvalidInputError: If data is invalid
        """
        if not data or not isinstance(data, dict):
            raise InvalidInputError("metadata must be a non-empty dictionary")
        
        try:
            metadata = cls(
                tenant_id=data.get("tenant_id", ""),
                user_id=data.get("user_id", ""),
                channel=data.get("channel", "web"),
                session_id=data.get("session_id"),
            )
            metadata.validate()
            return metadata
        except InvalidInputError:
            raise
        except Exception as e:
            raise InvalidInputError(f"Failed to parse metadata: {e}") from e
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for passing through system"""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "session_id": self.session_id,
        }
