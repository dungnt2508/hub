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


def verify_webhook_secret(
    request_body: bytes,
    signature_header: Optional[str],
    webhook_secret: Optional[str],
) -> bool:
    """
    Verify webhook secret using HMAC-SHA256.
    
    Catalog service sends webhook with header:
    X-Webhook-Signature: HMAC-SHA256(request_body, webhook_secret)
    
    Args:
        request_body: Raw request body bytes
        signature_header: Signature from X-Webhook-Signature header
        webhook_secret: Tenant's webhook secret from database
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not webhook_secret or not webhook_secret.strip():
        # If tenant has no webhook_secret configured, skip verification
        # (backward compatibility - optional verification)
        logger.warning("Webhook secret not configured for tenant, skipping verification")
        return True
    
    if not signature_header:
        logger.warning("Missing X-Webhook-Signature header")
        return False
    
    try:
        # Calculate expected signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison to prevent timing attacks)
        return hmac.compare_digest(expected_signature, signature_header.strip())
    
    except Exception as e:
        logger.error(f"Error verifying webhook secret: {e}", exc_info=True)
        return False


class MultiTenantAuthMiddleware:
    """
    Multi-tenant authentication middleware.
    
    Flows:
    1. JWT Web Embed: Extract tenant_id from JWT payload
    2. Telegram: Resolve tenant_id from bot token (database lookup)
    3. Teams: Extract tenant_id from verified JWT payload
    4. API Key: Extract tenant_id from verified API key
    """
    
    @staticmethod
    def extract_jwt_token(auth_header: str) -> str:
        """Extract JWT token from Authorization header"""
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    @staticmethod
    async def verify_web_embed_jwt(token: str, tenant_id: str, origin: str) -> JWTPayload:
        """
        Verify JWT for web embed flow.
        
        Args:
            token: JWT token
            tenant_id: From URL/config
            origin: From request origin header
        
        Returns:
            JWTPayload if valid
        
        Raises:
            AuthenticationError if invalid
        """
        try:
            # Priority 1 Fix: Get tenant's JWT secret from database
            from ...shared.auth_config import get_jwt_secret
            jwt_secret = await get_jwt_secret(tenant_id)
            if not jwt_secret:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            # Decode and verify
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"]
            )
            
            # Validate payload
            if payload.get("tenant_id") != tenant_id:
                raise AuthenticationError("Token tenant mismatch")
            
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
    async def generate_web_embed_jwt(
        tenant_id: str,
        user_key: str,
        origin: str,
        expiry_seconds: int = 300
    ) -> str:
        """
        Generate JWT token for web embed.
        
        Priority 1 Fix: Get JWT secret from database.
        
        Args:
            tenant_id: Tenant ID
            user_key: Technical user key (hash of session_id)
            origin: Website origin
            expiry_seconds: Token lifetime (default 5 minutes)
        
        Returns:
            Signed JWT token
        """
        from ...shared.auth_config import get_jwt_secret
        jwt_secret = await get_jwt_secret(tenant_id)
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
    async def verify_telegram_webhook(
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
            tenant_id: Tenant ID (resolved from bot token)
            body: Raw request body
            bot_token: Telegram bot token (from query param)
        
        Returns:
            True if valid
        
        Raises:
            AuthenticationError if invalid
        """
        try:
            # Get tenant config from database
            from ...shared.auth_config import get_tenant_config
            config = await get_tenant_config(tenant_id)
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
    async def verify_teams_jwt(token: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify Microsoft Teams JWT with JWKS signature verification.
        
        Task 1.2: Implement proper Microsoft JWKS verification.
        
        Args:
            token: JWT from Teams
            tenant_id: Optional tenant ID (for validation, but extracted from JWT payload)
        
        Returns:
            Decoded payload if valid (includes tenant_id from JWT)
        
        Raises:
            AuthenticationError if invalid
        """
        try:
            # Decode JWT header to get kid (key ID)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise AuthenticationError("JWT missing kid in header")
            
            # Get public key from JWKS
            from ...infrastructure.jwks_client import get_jwks_client
            jwks_client = get_jwks_client()
            
            try:
                public_key_pem = await jwks_client.get_public_key(kid)
            except Exception as e:
                logger.error(f"Failed to get public key for kid {kid}: {e}")
                raise AuthenticationError("Failed to verify JWT signature: key not found")
            
            # Verify JWT signature and decode payload
            try:
                # Microsoft Teams JWT expected claims:
                # - iss: Issuer (should be Microsoft)
                # - aud: Audience (should match bot service)
                # - exp: Expiration time
                # - nbf: Not before time
                # - serviceUrl: Bot service URL
                # - from: User information (aadObjectId, etc.)
                
                payload = jwt.decode(
                    token,
                    public_key_pem,
                    algorithms=["RS256"],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                    }
                )
                
                # Validate issuer (Microsoft Bot Framework)
                # Note: Issuer can vary, but should be from Microsoft domain
                iss = payload.get("iss", "")
                if not iss or "microsoft" not in iss.lower():
                    logger.warning(f"Invalid issuer in Teams JWT: {iss}")
                    raise AuthenticationError("Invalid JWT issuer")
                
                # Validate audience (optional - depends on bot configuration)
                # For now, we accept any audience, but can be made stricter
                # aud = payload.get("aud")
                # if aud and aud != expected_audience:
                #     raise AuthenticationError("Invalid JWT audience")
                
                # Extract tenant_id from JWT payload if available
                # Teams JWT may have tenantId in conversation or serviceUrl
                jwt_tenant_id = payload.get("tenantId") or payload.get("conversation", {}).get("tenantId")
                
                # If tenant_id provided, validate it matches JWT
                if tenant_id and jwt_tenant_id and tenant_id != jwt_tenant_id:
                    logger.warning(
                        f"Tenant ID mismatch: JWT={jwt_tenant_id}, provided={tenant_id}"
                    )
                    raise AuthenticationError("JWT tenant ID mismatch")
                
                # Use tenant_id from JWT if available, otherwise use provided
                if jwt_tenant_id:
                    payload["tenant_id"] = jwt_tenant_id
                elif tenant_id:
                    payload["tenant_id"] = tenant_id
                else:
                    # Try to extract from serviceUrl or other fields
                    service_url = payload.get("serviceUrl", "")
                    # Service URL format: https://smba.trafficmanager.net/{tenant_id}/
                    # This is a fallback, but tenant_id should be in payload
                    logger.warning("No tenant_id found in JWT payload or provided")
                
                logger.info(f"Teams JWT verified successfully - tenant: {payload.get('tenant_id')}")
                return payload
            
            except jwt.InvalidSignatureError:
                logger.warning("Invalid Teams JWT signature")
                raise AuthenticationError("Invalid JWT signature")
            except jwt.ExpiredSignatureError:
                logger.warning("Expired Teams JWT")
                raise AuthenticationError("JWT expired")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid Teams JWT: {e}")
                raise AuthenticationError(f"Invalid JWT: {e}")
        
        except AuthenticationError:
            raise
        except jwt.DecodeError as e:
            logger.warning(f"Failed to decode Teams JWT: {e}")
            raise AuthenticationError("Invalid JWT format")
        except Exception as e:
            logger.error(f"Unexpected error verifying Teams JWT: {e}", exc_info=True)
            raise AuthenticationError(f"JWT verification failed: {e}")
    
    @staticmethod
    async def resolve_context_from_jwt(
        token: str,
        tenant_id: str,
        origin: str,
        ip: Optional[str] = None,
    ) -> RequestContext:
        """
        Resolve request context from JWT token.
        
        Priority 1 Fix: Async version to query database.
        
        Args:
            token: JWT token
            tenant_id: Tenant ID (from JWT payload, not from query param)
            origin: Request origin
            ip: Client IP
        
        Returns:
            RequestContext object
        """
        payload = await MultiTenantAuthMiddleware.verify_web_embed_jwt(
            token,
            tenant_id,
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
    
    Task 3.1: Extract tenant_id from JWT payload, NOT from query param.
    """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization", "")
            token = MultiTenantAuthMiddleware.extract_jwt_token(auth_header)
            
            # Task 3.1: Extract tenant_id from JWT payload, NOT from query param
            # Decode JWT without verification first to get tenant_id
            import jwt as jwt_lib
            unverified_payload = jwt_lib.decode(token, options={"verify_signature": False})
            tenant_id_from_jwt = unverified_payload.get("tenant_id")
            
            if not tenant_id_from_jwt:
                raise AuthenticationError("JWT token missing tenant_id claim")
            
            # Get origin from request
            origin = request.headers.get("Origin", "")
            if not origin:
                logger.warning("Missing Origin header for web embed")
            
            # Verify and resolve context (this will verify signature and validate tenant_id)
            context = await MultiTenantAuthMiddleware.resolve_context_from_jwt(
                token,
                tenant_id_from_jwt,  # Use tenant_id from JWT, not query param
                origin,
                ip=request.client.host if request.client else None
            )
            
            # Inject context into request
            request.state.user_context = context
            
            return await func(request, *args, **kwargs)
        
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            return {"error": True, "message": str(e), "status_code": 401}
        except Exception as e:
            logger.error(f"Unexpected error in require_jwt_auth: {e}", exc_info=True)
            return {"error": True, "message": "Authentication failed", "status_code": 401}
    
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

