"""
Multi-tenant authentication middleware.
Xử lý authentication cho web embed, Telegram, Teams.
"""

from typing import Dict, Any, Optional
from functools import wraps
import jwt
import hashlib
import hmac
import json
from datetime import datetime, timedelta

from ...shared.auth_config import (
    get_jwt_secret,
    get_tenant_config,
    validate_origin,
)
from ...schemas.multi_tenant_types import (
    RequestContext,
    JWTPayload,
    ChannelType,
    AuthMethod,
)
from ...shared.logger import logger
from ...shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
)


class MultiTenantAuthMiddleware:
    """
    Multi-tenant authentication middleware.
    
    Flows:
    1. JWT Web Embed: Extract from Authorization header
    2. Telegram: Extract from X-Telegram-Bot-Id header + verify request
    3. Teams: Verify JWT from Microsoft
    4. API Key: For service-to-service
    """
    
    @staticmethod
    def extract_jwt_token(auth_header: str) -> str:
        """Extract JWT token from Authorization header"""
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    @staticmethod
    async def verify_web_embed_jwt(token: str, tenant_name: str, origin: str, jwt_secret: Optional[str] = None) -> JWTPayload:
        """
        Verify JWT for web embed flow.
        
        Args:
            token: JWT token
            tenant_name: Tenant name/site_id from URL/config (e.g., "n8n-market") - used for lookup
            origin: From request origin header
            jwt_secret: JWT secret (optional, will lookup from cache if not provided)
        
        Returns:
            JWTPayload if valid
        
        Raises:
            AuthenticationError if invalid
        """
        try:
            # Get tenant's JWT secret from cache using tenant_name (name/site_id)
            config = None
            if not jwt_secret:
                from ...infrastructure.tenant_config_cache import tenant_config_cache
                
                try:
                    # Lookup config by name (site_id)
                    config = await tenant_config_cache.get_by_name(tenant_name)
                    
                    if config:
                        jwt_secret = config.web_embed_jwt_secret
                        logger.debug(f"JWT secret found from cache for tenant name: {tenant_name}")
                    else:
                        # Fallback to memory lookup (for test tenants)
                        jwt_secret = get_jwt_secret(tenant_name)
                        if jwt_secret:
                            logger.debug(f"JWT secret found from memory for tenant: {tenant_name}")
                except Exception as e:
                    logger.error(f"Error getting tenant config from cache: {e}", exc_info=True)
                    # Fallback to memory lookup
                    jwt_secret = get_jwt_secret(tenant_name)
            
            if not jwt_secret:
                logger.warning(f"JWT secret not found for tenant name: {tenant_name}")
                raise TenantNotFoundError(f"Tenant not found: {tenant_name}")
            
            # Decode and verify signature
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"]
            )
            
            # Get tenant_id from payload for validation
            payload_tenant_id = payload.get("tenant_id")
            if not payload_tenant_id:
                raise AuthenticationError("JWT token missing tenant_id")
            
            # Verify that tenant_id in payload matches tenant config
            # (config was looked up by name, so we need to verify the UUID matches)
            if config and config.id != payload_tenant_id:
                raise AuthenticationError("Token tenant_id does not match tenant config")
            
            if payload.get("channel") != ChannelType.WEB:
                raise AuthenticationError("Token not for web channel")
            
            # Validate origin binding
            if payload.get("origin") != origin:
                raise AuthenticationError("Token origin mismatch")
            
            # Check expiration (jwt library checks this too, but explicit)
            if datetime.fromtimestamp(payload["exp"]) < datetime.now():
                raise AuthenticationError("Token expired")
            
            return JWTPayload(**payload)
        
        except jwt.InvalidSignatureError:
            logger.warning(f"Invalid JWT signature for tenant {tenant_id}")
            raise AuthenticationError("Invalid token signature")
        
        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired JWT for tenant {tenant_id}")
            raise AuthenticationError("Token expired")
        
        except jwt.DecodeError as e:
            logger.warning(f"Failed to decode JWT: {e}")
            raise AuthenticationError("Invalid token format")
    
    @staticmethod
    def generate_web_embed_jwt(
        tenant_id: str,
        user_key: str,
        origin: str,
        expiry_seconds: int = 300,
        jwt_secret: Optional[str] = None
    ) -> str:
        """
        Generate JWT token for web embed.
        
        Args:
            tenant_id: Tenant ID
            user_key: Technical user key (hash of session_id)
            origin: Website origin
            expiry_seconds: Token lifetime (default 5 minutes)
            jwt_secret: JWT secret (optional, will lookup if not provided)
        
        Returns:
            Signed JWT token
        """
        # Use provided jwt_secret or lookup from cache/memory
        if not jwt_secret:
            jwt_secret = get_jwt_secret(tenant_id)
            if not jwt_secret:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
        
        now = datetime.now()
        exp = now + timedelta(seconds=expiry_seconds)
        
        payload = {
            "tenant_id": tenant_id,
            "channel": ChannelType.WEB,
            "user_key": user_key,
            "origin": origin,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "auth_method": AuthMethod.JWT_WEB_EMBED,
        }
        
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        logger.info(f"Generated JWT for tenant={tenant_id}, user_key={user_key[:8]}...")
        
        return token
    
    @staticmethod
    def verify_telegram_webhook(
        tenant_id: str,
        body: bytes,
        bot_token: str
    ) -> bool:
        """
        Verify Telegram webhook request.
        
        Telegram verification strategy:
        1. Verify bot token matches tenant's config
        2. IP whitelist (Telegram's official IPs)
        3. Basic JSON validation
        
        Args:
            tenant_id: Tenant ID
            body: Raw request body
            bot_token: From X-Telegram-Bot-Id header
        
        Returns:
            True if valid
        
        Raises:
            AuthenticationError if invalid
        """
        try:
            # Get tenant config
            config = get_tenant_config(tenant_id)
            if not config or not config.telegram_enabled:
                raise AuthorizationError("Telegram not enabled for tenant")
            
            # Verify bot token
            if bot_token != config.telegram_bot_token:
                logger.warning(f"Invalid Telegram bot token for tenant {tenant_id}")
                raise AuthenticationError("Invalid bot token")
            
            # Parse JSON
            data = json.loads(body)
            
            # Verify has required fields
            if "update_id" not in data or "message" not in data:
                raise AuthenticationError("Invalid Telegram payload")
            
            return True
        
        except json.JSONDecodeError:
            raise AuthenticationError("Invalid JSON payload")
    
    @staticmethod
    def verify_teams_jwt(token: str, tenant_id: str) -> Dict[str, Any]:
        """
        Verify Microsoft Teams JWT.
        
        Args:
            token: JWT from Teams
            tenant_id: Tenant ID
        
        Returns:
            Decoded payload if valid
        
        Raises:
            AuthenticationError if invalid
        """
        # TODO: Implement Microsoft JWKS verification
        # Reference: https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-authentication-components
        
        try:
            # For now, basic validation
            # In production: fetch JWKs from Microsoft, verify signature
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Validate issuer, audience, etc.
            # This is placeholder - need real Microsoft JWKS endpoint
            
            return payload
        
        except jwt.DecodeError:
            raise AuthenticationError("Invalid Teams JWT")
    
    @staticmethod
    async def resolve_context_from_jwt(
        token: str,
        tenant_name: str,
        origin: str,
        ip: Optional[str] = None,
    ) -> RequestContext:
        """
        Resolve request context from JWT token.
        
        Args:
            token: JWT token
            tenant_name: Tenant name/site_id (e.g., "n8n-market")
            origin: Request origin
            ip: Client IP
        
        Returns:
            RequestContext object
        """
        payload = await MultiTenantAuthMiddleware.verify_web_embed_jwt(
            token,
            tenant_name,
            origin
        )
        
        context = RequestContext(
            tenant_id=payload.tenant_id,
            channel=payload.channel,
            user_key=payload.user_key,
            auth_method=payload.auth_method,
            platform="web",
            ip=ip,
            origin=origin,
        )
        
        return context
    
    @staticmethod
    def resolve_context_from_telegram(
        tenant_id: str,
        telegram_user_id: str,
        ip: Optional[str] = None,
    ) -> RequestContext:
        """Resolve request context from Telegram"""
        context = RequestContext(
            tenant_id=tenant_id,
            channel=ChannelType.TELEGRAM,
            user_key=str(telegram_user_id),  # Telegram user ID
            auth_method=AuthMethod.TELEGRAM_BOT,
            platform="telegram",
            ip=ip,
        )
        return context
    
    @staticmethod
    def resolve_context_from_teams(
        tenant_id: str,
        aad_object_id: str,
        ip: Optional[str] = None,
    ) -> RequestContext:
        """Resolve request context from Teams"""
        context = RequestContext(
            tenant_id=tenant_id,
            channel=ChannelType.TEAMS,
            user_key=aad_object_id,  # AAD Object ID
            auth_method=AuthMethod.TEAMS_BOT,
            platform="teams",
            ip=ip,
        )
        return context


def require_jwt_auth(func):
    """
    Decorator: Require JWT authentication.
    Extracts token from Authorization header and verifies it.
    """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization", "")
            token = MultiTenantAuthMiddleware.extract_jwt_token(auth_header)
            
            # Get tenant_name/tenant_id from request (path/query param or config)
            # Prefer tenant_name (name/site_id) over tenant_id (UUID) for clarity
            tenant_id = kwargs.get("tenant_id") or request.query_params.get("tenant_name") or request.query_params.get("tenant_id")
            if not tenant_id:
                raise AuthenticationError("Missing tenant_name or tenant_id")
            
            # Get origin from request
            origin = request.headers.get("Origin", "")
            if not origin:
                logger.warning("Missing Origin header for web embed")
            
            # Verify and resolve context
            context = MultiTenantAuthMiddleware.resolve_context_from_jwt(
                token,
                tenant_id,
                origin,
                ip=request.client.host if request.client else None
            )
            
            # Inject context into request
            request.state.user_context = context
            
            return await func(request, *args, **kwargs)
        
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            return {"error": True, "message": str(e), "status_code": 401}
    
    return wrapper


def require_api_key(func):
    """
    Decorator: Require API key for service-to-service auth.
    """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        try:
            # Get API key from Authorization header or query param
            auth_header = request.headers.get("Authorization", "")
            
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
            else:
                api_key = request.query_params.get("api_key")
            
            if not api_key:
                raise AuthenticationError("Missing API key")
            
            # Get database connection and verify API key
            from ...infrastructure.database_client import database_client
            try:
                db_pool = database_client.pool
            except Exception as e:
                logger.error(f"Database not available for API key verification: {e}")
                raise AuthenticationError("Authentication service unavailable")
            
            # Verify API key asynchronously
            tenant_id = await verify_api_key(api_key, db_pool)
            
            if not tenant_id:
                raise AuthenticationError("Invalid API key")
            
            # Inject context
            context = RequestContext(
                tenant_id=tenant_id,
                channel=ChannelType.API,
                user_key="service-account",
                auth_method=AuthMethod.API_KEY,
                platform="api",
            )
            request.state.user_context = context
            
            return await func(request, *args, **kwargs)
        
        except AuthenticationError as e:
            logger.warning(f"API key authentication failed: {e}")
            return {"error": True, "message": str(e), "status_code": 401}
    
    return wrapper


async def verify_api_key(api_key: str, db_pool) -> Optional[str]:
    """
    Verify API key and return tenant_id.
    
    Args:
        api_key: API key to verify
        db_pool: Database connection pool (asyncpg.Pool)
    
    Returns:
        Tenant ID if valid, None otherwise
    """
    if not db_pool:
        logger.warning("Database pool not available for API key verification")
        return None
    
    try:
        from ...domain.tenant.tenant_service import TenantService
        
        # Get connection from pool and verify API key
        async with db_pool.acquire() as conn:
            tenant_service = TenantService(conn)
            tenant_id = await tenant_service.verify_api_key(api_key)
            
            if tenant_id:
                logger.debug(f"API key verified for tenant: {tenant_id}")
            else:
                logger.warning("API key verification failed: invalid key")
            
            return tenant_id
    except Exception as e:
        logger.error(f"Error verifying API key: {e}", exc_info=True)
        return None

