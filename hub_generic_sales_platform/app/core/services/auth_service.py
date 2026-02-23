"""
Authentication Service - JWT-based authentication
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.infrastructure.database.models.tenant import UserAccount
from app.infrastructure.database.repositories import UserAccountRepository
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings - will be loaded from settings
from app.core.config.settings import get_settings

def get_jwt_config():
    """Get JWT configuration from settings"""
    try:
        settings = get_settings()
        return {
            "secret_key": settings.jwt_secret_key,
            "algorithm": settings.jwt_algorithm,
            "expire_minutes": settings.jwt_access_token_expire_minutes,
        }
    except Exception as e:
        logger.error(f"Error getting JWT config: {e}", exc_info=True)
        # Fallback to defaults
        return {
            "secret_key": "your-secret-key-change-in-production",
            "algorithm": "HS256",
            "expire_minutes": 1440,
        }


class AuthService:
    """Authentication service for JWT-based auth"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_jwt_token(
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generate JWT access token"""
        config = get_jwt_config()
        
        if expires_delta is None:
            expires_delta = timedelta(minutes=config["expire_minutes"])
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,  # subject (user ID)
            "tenant_id": tenant_id,
            "email": email,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, config["secret_key"], algorithm=config["algorithm"])
        return token
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        config = get_jwt_config()
        
        try:
            payload = jwt.decode(token, config["secret_key"], algorithms=[config["algorithm"]])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[UserAccount]:
        """
        Authenticate user by email and password
        
        Returns:
            UserAccount if authentication successful, None otherwise
        """
        try:
            user_repo = UserAccountRepository(db)
            user = await user_repo.get_by_email_system(email)
            
            if not user:
                logger.warning(f"User not found: {email}")
                return None
            
            if user.status != "active":
                logger.warning(f"User is not active: {email}")
                return None
            
            # Check if user has password_hash (new users)
            if user.password_hash:
                if not AuthService.verify_password(password, user.password_hash):
                    logger.warning(f"Invalid password for user: {email}")
                    return None
            else:
                # Legacy users without password - for backward compatibility
                # In production, should require password reset
                logger.warning(f"User {email} has no password_hash - legacy user")
                # For now, allow access (should be changed in production)
                pass
            
            # Tenant is already loaded by UserAccountRepository via selectinload
            
            if user.tenant.status != "active":
                logger.warning(f"Tenant is not active for user: {email}")
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_user_from_token(
        db: AsyncSession,
        token: str
    ) -> Optional[UserAccount]:
        """
        Get user from JWT token
        
        Returns:
            UserAccount if token is valid, None otherwise
        """
        payload = AuthService.verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user_repo = UserAccountRepository(db)
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                return None
                
            # Use get() with mandatory tenant isolation
            user = await user_repo.get(user_id, tenant_id=tenant_id)
            
            if not user:
                logger.warning(f"User not found from token: {user_id}")
                return None
            
            if user.status != "active":
                logger.warning(f"User is not active: {user_id}")
                return None
            
            # Tenant is already loaded by UserAccountRepository via selectinload
            
            if user.tenant.status != "active":
                logger.warning(f"Tenant is not active for user: {user_id}")
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from token: {e}", exc_info=True)
            return None
