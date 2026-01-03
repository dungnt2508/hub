"""
JWT Service - Token generation, verification, refresh
Phase 1: Foundation - Core JWT infrastructure for web embed flow

Implements:
- JWT generation for web embed (with origin binding)
- JWT verification (signature + expiration + origin)
- Token refresh logic
- Secret management per tenant
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import hashlib
from functools import lru_cache

from ..schemas.multi_tenant_types import JWTPayload, AuthMethod, ChannelType
from ..shared.logger import logger
from ..shared.exceptions import (
    AuthenticationError,
    TenantNotFoundError,
)


class JWTService:
    """
    JWT Service - generates and verifies tokens for web embed and other channels.
    
    Features:
    - Generate short-lived tokens (3-5 min)
    - Bind tokens to origin (prevent cross-site reuse)
    - Verify signature + expiration + origin
    - Auto-refresh logic
    - Per-tenant secret management
    """
    
    # Token settings
    WEB_EMBED_EXPIRY_SECONDS = 300  # 5 minutes
    TOKEN_ALGORITHM = "HS256"
    
    def __init__(self, db_connection=None):
        """
        Initialize JWT service.
        
        Args:
            db_connection: PostgreSQL connection (optional, for caching)
        """
        self.db = db_connection
        self._secret_cache: Dict[str, str] = {}  # Simple in-memory cache
        logger.info("JWTService initialized")
    
    async def get_jwt_secret(self, tenant_id: str) -> Optional[str]:
        """
        Get JWT secret for tenant.
        
        Implements caching to avoid DB hits on every request.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            JWT secret or None if not found
        """
        try:
            # Check in-memory cache
            if tenant_id in self._secret_cache:
                return self._secret_cache[tenant_id]
            
            # Query database
            if not self.db:
                logger.warning("Database connection not available")
                return None
            
            query = "SELECT web_embed_jwt_secret FROM tenants WHERE id = $1"
            result = await self.db.fetchval(query, tenant_id)
            
            if not result:
                logger.warning(f"Tenant not found: {tenant_id}")
                return None
            
            # Cache it
            self._secret_cache[tenant_id] = result
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching JWT secret: {e}", exc_info=True)
            return None
    
    def clear_secret_cache(self, tenant_id: str = None):
        """
        Clear secret cache (for tenant secret rotation).
        
        Args:
            tenant_id: If provided, clear only that tenant. Otherwise clear all.
        """
        if tenant_id:
            self._secret_cache.pop(tenant_id, None)
            logger.info(f"Cleared cache for tenant: {tenant_id}")
        else:
            self._secret_cache.clear()
            logger.info("Cleared all secret cache")
    
    async def generate_jwt(
        self,
        tenant_id: str,
        user_key: str,
        origin: str,
        channel: str = ChannelType.WEB,
        expiry_seconds: int = None,
    ) -> str:
        """
        Generate JWT token for web embed.
        
        Args:
            tenant_id: Tenant UUID
            user_key: Technical user identifier (hash of session_id)
            origin: Request origin (for binding)
            channel: Channel type (default: web)
            expiry_seconds: Token lifetime (default: 300s = 5 min)
        
        Returns:
            Signed JWT token
        
        Raises:
            TenantNotFoundError: If tenant not found
            Exception: If JWT generation fails
        """
        try:
            # Get tenant's JWT secret
            jwt_secret = await self.get_jwt_secret(tenant_id)
            if not jwt_secret:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            if not jwt_secret or len(jwt_secret) < 32:
                raise Exception("Invalid JWT secret (min 32 chars)")
            
            # Set expiry
            if expiry_seconds is None:
                expiry_seconds = self.WEB_EMBED_EXPIRY_SECONDS
            
            now = datetime.utcnow()
            exp = now + timedelta(seconds=expiry_seconds)
            
            # Create payload
            payload = {
                "tenant_id": tenant_id,
                "channel": channel,
                "user_key": user_key,
                "origin": origin,
                "iat": int(now.timestamp()),
                "exp": int(exp.timestamp()),
                "auth_method": AuthMethod.JWT_WEB_EMBED,
            }
            
            # Sign token
            token = jwt.encode(
                payload,
                jwt_secret,
                algorithm=self.TOKEN_ALGORITHM,
            )
            
            logger.info(
                f"✅ JWT generated for tenant={tenant_id}, "
                f"user_key={user_key[:8]}..., channel={channel}"
            )
            
            return token
        
        except TenantNotFoundError:
            raise
        
        except Exception as e:
            logger.error(f"Error generating JWT: {e}", exc_info=True)
            raise Exception(f"Failed to generate JWT: {e}")
    
    async def verify_jwt(
        self,
        token: str,
        tenant_id: str,
        origin: str,
    ) -> JWTPayload:
        """
        Verify JWT token and return payload.
        
        Validates:
        - JWT signature (HMAC-SHA256)
        - Expiration time
        - Origin binding (prevent cross-site reuse)
        - Tenant ID match
        - Channel (must be 'web')
        
        Args:
            token: JWT token to verify
            tenant_id: Expected tenant ID
            origin: Expected origin
        
        Returns:
            JWTPayload object
        
        Raises:
            AuthenticationError: If token invalid/expired/mismatched
        """
        try:
            # Get tenant's JWT secret
            jwt_secret = await self.get_jwt_secret(tenant_id)
            if not jwt_secret:
                raise AuthenticationError(f"Tenant not found: {tenant_id}")
            
            # Decode and verify signature
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=[self.TOKEN_ALGORITHM],
                )
            except jwt.InvalidSignatureError:
                logger.warning(f"Invalid JWT signature for tenant {tenant_id}")
                raise AuthenticationError("Invalid token signature")
            
            except jwt.ExpiredSignatureError:
                logger.warning(f"Expired JWT for tenant {tenant_id}")
                raise AuthenticationError("Token expired")
            
            except jwt.DecodeError as e:
                logger.warning(f"Failed to decode JWT: {e}")
                raise AuthenticationError("Invalid token format")
            
            # Validate payload fields
            if payload.get("tenant_id") != tenant_id:
                logger.warning(
                    f"Tenant mismatch: token={payload.get('tenant_id')}, "
                    f"expected={tenant_id}"
                )
                raise AuthenticationError("Token tenant mismatch")
            
            if payload.get("channel") != ChannelType.WEB:
                logger.warning(f"Token not for web channel: {payload.get('channel')}")
                raise AuthenticationError("Token not for web channel")
            
            # Validate origin binding
            token_origin = payload.get("origin")
            if token_origin != origin:
                logger.warning(
                    f"Origin mismatch: token={token_origin}, request={origin}"
                )
                raise AuthenticationError("Token origin mismatch")
            
            # All validations passed
            logger.info(
                f"✅ JWT verified for tenant={tenant_id}, "
                f"user_key={payload.get('user_key')[:8]}..."
            )
            
            return JWTPayload(**payload)
        
        except AuthenticationError:
            raise
        
        except Exception as e:
            logger.error(f"Error verifying JWT: {e}", exc_info=True)
            raise AuthenticationError("Token verification failed")
    
    async def refresh_jwt(
        self,
        old_token: str,
        tenant_id: str,
        origin: str,
    ) -> Optional[str]:
        """
        Refresh JWT token (issue new one before expiry).
        
        Strategy:
        - Verify old token is still valid
        - Extract user_key and other data
        - Generate new token with same payload (except iat/exp)
        - Return new token
        
        Args:
            old_token: Current JWT token
            tenant_id: Tenant ID
            origin: Request origin
        
        Returns:
            New JWT token or None if refresh fails
        """
        try:
            # Verify old token
            old_payload = await self.verify_jwt(old_token, tenant_id, origin)
            
            # Generate new token
            new_token = await self.generate_jwt(
                tenant_id=old_payload.tenant_id,
                user_key=old_payload.user_key,
                origin=old_payload.origin,
                channel=old_payload.channel,
            )
            
            logger.info(
                f"✅ JWT refreshed for tenant={tenant_id}, "
                f"user_key={old_payload.user_key[:8]}..."
            )
            
            return new_token
        
        except AuthenticationError as e:
            logger.warning(f"JWT refresh failed: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error refreshing JWT: {e}", exc_info=True)
            return None
    
    def get_token_expiry_seconds(self) -> int:
        """Get configured token expiry in seconds"""
        return self.WEB_EMBED_EXPIRY_SECONDS
    
    async def rotate_jwt_secret(self, tenant_id: str, new_secret: str) -> bool:
        """
        Rotate JWT secret for tenant (security best practice).
        
        Args:
            tenant_id: Tenant UUID
            new_secret: New JWT secret (min 32 chars)
        
        Returns:
            True if successful
        """
        try:
            if len(new_secret) < 32:
                raise Exception("Secret must be at least 32 characters")
            
            if not self.db:
                raise Exception("Database connection not available")
            
            query = """
            UPDATE tenants
            SET web_embed_jwt_secret = $1, updated_at = $2
            WHERE id = $3
            """
            
            result = await self.db.execute(
                query,
                new_secret,
                datetime.now(),
                tenant_id,
            )
            
            # Clear cache
            self.clear_secret_cache(tenant_id)
            
            logger.info(f"✅ JWT secret rotated for tenant: {tenant_id}")
            return result != "UPDATE 0"
        
        except Exception as e:
            logger.error(f"Error rotating JWT secret: {e}", exc_info=True)
            return False


# ============================================================================
# UTILITIES
# ============================================================================

def generate_user_key(site_id: str, session_id: str) -> str:
    """
    Generate technical user key from site_id + session_id.
    
    This ensures:
    - User key is generated server-side (not from user input)
    - Deterministic but unique per session
    - Non-PII (no email, name, etc)
    
    Args:
        site_id: Tenant/site identifier
        session_id: Browser session ID (random)
    
    Returns:
        SHA-256 hash (first 16 chars)
    """
    combined = f"{site_id}:{session_id}"
    user_key = hashlib.sha256(combined.encode()).hexdigest()[:16]
    return user_key


def generate_session_id() -> str:
    """Generate random session ID"""
    import secrets
    return secrets.token_urlsafe(16)

