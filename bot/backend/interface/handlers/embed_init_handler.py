"""
Embed initialization API handler.
Xử lý POST /embed/init endpoint
"""

from typing import Dict, Any, Optional
import hashlib
import os
from datetime import datetime

from ..middleware.multi_tenant_auth import MultiTenantAuthMiddleware
from ...shared.auth_config import get_tenant_config, validate_origin
from ...shared.logger import logger
from ...shared.exceptions import TenantNotFoundError, AuthorizationError
from ...infrastructure.database_client import database_client


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
            
            # Priority 1 Fix: Resolve tenant_id from site_id via database
            tenant_id = await EmbedInitHandler._resolve_tenant_id(site_id)
            if not tenant_id:
                logger.warning(f"Tenant not found for site_id: {site_id}")
                return {
                    "error": True,
                    "message": "Tenant not found",
                    "status_code": 404
                }
            
            # Get tenant config from database
            config = await get_tenant_config(tenant_id)
            if not config:
                logger.warning(f"Tenant config not found: {tenant_id}")
                return {
                    "error": True,
                    "message": "Tenant not found",
                    "status_code": 404
                }
            
            if not config.web_embed_enabled:
                logger.warning(f"Web embed not enabled for tenant: {tenant_id}")
                return {
                    "error": True,
                    "message": "Web embed is not enabled",
                    "status_code": 403
                }
            
            # Validate origin
            origin_allowed = await validate_origin(tenant_id, origin)
            if not origin_allowed:
                # Log already handled in validate_origin() with allowed origins info
                return {
                    "error": True,
                    "message": "Origin not allowed",
                    "status_code": 403
                }
            
            # Check if this is a token refresh (has session_id) or new initialization
            existing_session_id = request_body.get("session_id")
            is_new_session = existing_session_id is None
            
            if is_new_session:
                # New session: generate new session_id
                session_id = EmbedInitHandler._generate_session_id()
                logger.info(
                    f"Web embed init (NEW SESSION) - tenant: {tenant_id}, site_id: {site_id}, "
                    f"session_id: {session_id[:8]}..., origin: {origin}, ip: {ip}"
                )
            else:
                # Token refresh: reuse existing session_id
                session_id = existing_session_id
                logger.debug(
                    f"Web embed init (TOKEN REFRESH) - tenant: {tenant_id}, site_id: {site_id}, "
                    f"session_id: {session_id[:8]}..., origin: {origin}"
                )
            
            # Generate user_key from session_id (consistent for same session)
            user_key = EmbedInitHandler.generate_user_key(site_id, session_id)
            
            # Issue JWT token
            token = await MultiTenantAuthMiddleware.generate_web_embed_jwt(
                tenant_id=tenant_id,
                user_key=user_key,
                origin=origin,
                expiry_seconds=config.web_embed_token_expiry_seconds
            )
            
            # Audit log chỉ khi tạo session mới (không log khi refresh token)
            if is_new_session:
                from backend.shared.audit_helper import log_tenant_operation
                await log_tenant_operation(
                    tenant_id=tenant_id,
                    operation="init",
                    resource_type="embed_session",
                    user_key=user_key,
                    channel="web",
                    ip_address=ip,
                    metadata={
                        "site_id": site_id,
                        "origin": origin,
                        "platform": platform,
                        "session_id": session_id,
                    }
                )
            
            # Prepare response
            bot_config = EmbedInitHandler._prepare_bot_config(config)
            
            return {
                "success": True,
                "data": {
                    "token": token,
                    "expiresIn": config.web_embed_token_expiry_seconds,
                    "botConfig": bot_config,
                    "sessionId": session_id,  # Trả về session_id để frontend reuse
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
    async def _resolve_tenant_id(site_id: str) -> Optional[str]:
        """
        Resolve tenant_id from site_id via database lookup.
        
        Priority 1 Fix: Query tenant_sites table to resolve tenant_id.
        
        Args:
            site_id: Site identifier
        
        Returns:
            Tenant UUID if found and active, None otherwise
        """
        try:
            from ...domain.tenant.tenant_service import TenantService
            
            # Get database connection
            db_pool = database_client.pool
            if not db_pool:
                logger.error("Database pool not available")
                return None
            
            async with db_pool.acquire() as conn:
                tenant_service = TenantService(conn)
                tenant_id = await tenant_service.resolve_tenant_id_from_site_id(site_id)
                return tenant_id
        
        except Exception as e:
            logger.error(f"Error resolving tenant_id from site_id: {e}", exc_info=True)
            return None
    
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
        
        # Log request để track số lượng calls
        site_id = body.get("site_id", "unknown")
        logger.debug(f"POST /embed/init called - site_id: {site_id}, origin: {origin}, ip: {ip}")
        
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

# Priority 2 Fix: Removed setup_test_data() function
# Test tenants should be created via:
# 1. POST /admin/tenants API endpoint
# 2. scripts/create_tenant.py script
# 3. Direct database inserts for testing
#
# DO NOT create test data in application code.

