"""
Embed initialization API handler.
Xử lý POST /embed/init endpoint
"""

from typing import Dict, Any, Optional
import asyncio
import hashlib
import os
from datetime import datetime

from ..middleware.multi_tenant_auth import MultiTenantAuthMiddleware
from ...shared.auth_config import register_test_tenant  # Removed get_tenant_config, validate_origin - now using DB lookup
from ...shared.logger import logger
from ...shared.exceptions import TenantNotFoundError, AuthorizationError
from ...infrastructure.tenant_config_cache import tenant_config_cache
from ...schemas.multi_tenant_types import TenantConfig


class EmbedInitHandler:
    """
    Handle web embed initialization.
    
    Flow:
    1. Customer website loads bot script
    2. Script calls POST /embed/init with site_id + origin
    3. Bot service validates origin against tenant config
    4. Bot service issues short-lived JWT token
    5. Frontend uses JWT for subsequent /bot/message calls
    """
    
    @staticmethod
    def generate_user_key(site_id: str, session_id: str) -> str:
        """
        Generate technical user key (non-PII).
        
        NOT FROM USER INPUT - generated server-side.
        
        Args:
            site_id: Tenant site ID
            session_id: Browser session ID (random)
        
        Returns:
            Hash of site_id + session_id
        """
        combined = f"{site_id}:{session_id}"
        user_key = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return user_key
    
    @staticmethod
    async def initialize(
        request_body: Dict[str, Any],
        origin: str,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize web embed session.
        
        Args:
            request_body: {
                "site_id": "customer-001",
                "platform": "web",
                "user_data": { "email": "user@example.com" }  # optional
            }
            origin: Request origin (from Origin header)
            ip: Client IP
        
        Returns:
            {
                "success": true,
                "data": {
                    "token": "eyJhbGciOiJIUzI1NiIs...",
                    "expiresIn": 300,
                    "botConfig": { ... }
                }
            }
        """
        try:
            site_id = request_body.get("site_id")
            platform = request_body.get("platform", "web")
            user_data = request_body.get("user_data", {})
            
            # Validate inputs
            if not site_id or not site_id.strip():
                return {
                    "error": True,
                    "message": "site_id is required",
                    "status_code": 400
                }
            
            if platform != "web":
                return {
                    "error": True,
                    "message": f"Unsupported platform: {platform}",
                    "status_code": 400
                }
            
            # Get tenant config by site_id with multi-layer caching
            # L1: Memory → L2: Redis → L3: Database
            config = await tenant_config_cache.get_by_name(site_id)
            if not config:
                logger.warning(f"Tenant not found: {site_id}")
                return {
                    "error": True,
                    "message": "Tenant not found",
                    "status_code": 404
                }
            
            tenant_id = config.id
            
            if not config.web_embed_enabled:
                logger.warning(f"Web embed not enabled for tenant: {tenant_id}")
                return {
                    "error": True,
                    "message": "Web embed is not enabled",
                    "status_code": 403
                }
            
            # Validate origin using config from database
            if not config.web_embed_origins:
                logger.warning(f"No allowed origins configured for tenant: {tenant_id}")
                return {
                    "error": True,
                    "message": "Web embed origins not configured",
                    "status_code": 403
                }
            
            # Check if origin is allowed
            origin_allowed = False
            for allowed in config.web_embed_origins:
                if allowed == "*":
                    origin_allowed = True  # Allow all origins in development
                    break
                if allowed == origin:
                    origin_allowed = True
                    break
                # Wildcard matching (simple)
                if allowed.startswith("*.") and origin.endswith(allowed[1:]):
                    origin_allowed = True
                    break
            
            if not origin_allowed:
                logger.warning(
                    f"Origin not allowed - tenant: {tenant_id}, origin: {origin}, allowed: {config.web_embed_origins}"
                )
                return {
                    "error": True,
                    "message": "Origin not allowed",
                    "status_code": 403
                }
            
            # Generate user_key (server-side, not from user input)
            session_id = EmbedInitHandler._generate_session_id()
            user_key = EmbedInitHandler.generate_user_key(site_id, session_id)
            
            # Issue JWT token (use jwt_secret from config)
            token = MultiTenantAuthMiddleware.generate_web_embed_jwt(
                tenant_id=tenant_id,
                user_key=user_key,
                origin=origin,
                expiry_seconds=config.web_embed_token_expiry_seconds,
                jwt_secret=config.web_embed_jwt_secret  # Use secret from cached config
            )
            
            # Log initialization (for analytics)
            logger.info(
                f"Web embed initialized - "
                f"tenant: {tenant_id}, origin: {origin}, ip: {ip}"
            )
            
            # Prepare response
            bot_config = EmbedInitHandler._prepare_bot_config(config)
            
            return {
                "success": True,
                "data": {
                    "token": token,
                    "expiresIn": config.web_embed_token_expiry_seconds,
                    "botConfig": bot_config,
                    # For debugging (remove in production)
                    "userKey": user_key,
                    "issuedAt": datetime.now().isoformat(),
                }
            }
        
        except Exception as e:
            logger.error(f"Error in embed initialization: {e}", exc_info=True)
            return {
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }
    
    
    @staticmethod
    def _resolve_tenant_id(site_id: str) -> str:
        """
        Resolve tenant_id from site_id.
        DEPRECATED: Use _get_tenant_from_db() instead
        
        For now: site_id == tenant_id (kept for backward compatibility)
        """
        return site_id
    
    @staticmethod
    def _generate_session_id() -> str:
        """Generate random session ID"""
        return os.urandom(16).hex()
    
    @staticmethod
    def _prepare_bot_config(config) -> Dict[str, Any]:
        """Prepare non-sensitive bot configuration"""
        return {
            "name": "Hub Assistant",
            "avatar": "https://api.bot.service/avatar/default.png",
            "theme": {
                "primaryColor": "#007bff",
                "accentColor": "#0056b3",
                "borderRadius": "8px",
            },
            "features": {
                "typing_indicator": True,
                "conversation_history": True,
                "user_identification": False,  # Progressive identity
            },
            "supportedActions": [
                "hr.leave_balance",
                "hr.request_leave",
                "hr.attendance",
            ]
        }


# ============================================================================
# API ENDPOINT (FastAPI)
# ============================================================================

async def embed_init_endpoint(request):
    """
    POST /embed/init
    
    Initialize web embed session and issue JWT token.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Get origin from header
        origin = request.headers.get("Origin", "")
        if not origin:
            logger.warning("Missing Origin header")
            return {
                "error": True,
                "message": "Origin header is required",
                "status_code": 400
            }
        
        # Get client IP
        ip = request.client.host if request.client else None
        
        # Initialize
        result = await EmbedInitHandler.initialize(
            request_body=body,
            origin=origin,
            ip=ip
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in embed_init_endpoint: {e}", exc_info=True)
        return {
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }


# ============================================================================
# EXAMPLE / TESTING
# ============================================================================

def setup_test_data():
    """Setup test data for development"""
    # Register test tenant
    register_test_tenant(
        tenant_id="catalog-001",
        name="GSNAKE Catalog",
        jwt_secret="test_jwt_secret_catalog_001_very_long_and_secure",
    )
    
    logger.info("Test data setup complete")

