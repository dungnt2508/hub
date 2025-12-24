"""
Authentication Type Definitions
"""
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class UserRole(str, Enum):
    """User roles (shared với Catalog service)"""
    USER = "user"
    ADMIN = "admin"
    SELLER = "seller"
    SERVICE = "service"  # For service-to-service communication


@dataclass
class JWTPayload:
    """
    JWT Payload structure (shared với Catalog service)
    
    RULE: JWT phải có aud và iss bắt buộc (validate ở AuthService)
    """
    userId: str
    email: str
    role: UserRole
    aud: Optional[str] = None  # Audience - bắt buộc theo rules
    iss: Optional[str] = None  # Issuer - bắt buộc theo rules
    iat: Optional[int] = None  # Issued at
    exp: Optional[int] = None  # Expires at
    
    def to_user_context(self) -> dict:
        """Convert to user context for router"""
        return {
            "user_id": self.userId,
            "email": self.email,
            "role": self.role.value,
            "auth_method": "jwt",
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "JWTPayload":
        """Create JWTPayload from dictionary"""
        return cls(
            userId=data["userId"],
            email=data["email"],
            role=UserRole(data["role"]),
            aud=data.get("aud"),
            iss=data.get("iss"),
            iat=data.get("iat"),
            exp=data.get("exp"),
        )


@dataclass(frozen=True)  # RULE: UserContext là immutable - không sửa sau khi tạo
class UserContext:
    """
    User context extracted from authentication
    
    RULE: UserContext là immutable - build một lần, không sửa trong handler
    RULE: Không inject thêm quyền động, không trust data từ client
    """
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None
    auth_method: str = "unknown"
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "auth_method": self.auth_method,
            "metadata": self.metadata or {},
        }

