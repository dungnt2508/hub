"""
Admin Auth Service - JWT generation and verification for admin dashboard
"""
import jwt
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import os

from ...shared.logger import logger
from ...shared.exceptions import AuthenticationError
from .admin_user_service import admin_user_service


class AdminAuthService:
    """JWT authentication service for admin dashboard"""
    
    # JWT settings
    SECRET_KEY = os.getenv("ADMIN_JWT_SECRET", "admin_jwt_secret_change_in_production")
    ALGORITHM = "HS256"
    TOKEN_EXPIRY_HOURS = 24  # 24 hours
    
    def __init__(self):
        self.user_service = admin_user_service
    
    def generate_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT token for admin user"""
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
        
        payload = {
            "sub": str(user["id"]),  # Subject (user ID)
            "email": user["email"],
            "role": user["role"],
            "tenant_id": str(user["tenant_id"]) if user.get("tenant_id") else None,
            "permissions": user.get("permissions", {}),
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiration
            "type": "admin",  # Token type
        }
        
        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        logger.info(f"Generated admin JWT for user {user['email']}")
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
                options={"verify_exp": True}
            )
            
            # Validate token type
            if payload.get("type") != "admin":
                raise AuthenticationError("Invalid token type")
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid admin JWT: {e}")
            raise AuthenticationError("Invalid token")
    
    async def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Get admin user from JWT token"""
        payload = self.verify_token(token)
        
        user_id = UUID(payload["sub"])
        user = await self.user_service.get_admin_user(user_id)
        
        # Check if user is still active
        if not user.get("active"):
            raise AuthenticationError("User account is inactive")
        
        # Remove password_hash
        user.pop("password_hash", None)
        
        return user
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and return user + token"""
        user = await self.user_service.authenticate_user(email, password)
        token = self.generate_token(user)
        
        return {
            "user": user,
            "token": token,
            "expires_in": self.TOKEN_EXPIRY_HOURS * 3600,  # seconds
        }


# Global auth service instance
admin_auth_service = AdminAuthService()

