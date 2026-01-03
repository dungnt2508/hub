"""
Multi-tenant bot API - Main integration point.
Tích hợp authentication, rate limiting, và routing.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os

from .middleware.multi_tenant_auth import (
    MultiTenantAuthMiddleware,
    require_jwt_auth,
)
from .handlers.embed_init_handler import EmbedInitHandler, setup_test_data
from .api_handler import APIHandler
from ..infrastructure.rate_limiter import RateLimitService
from ..shared.logger import logger
from ..shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
    RouterError,
    InvalidInputError,
)
import uuid


class MultiTenantBotAPI:
    """
    Multi-tenant bot service API.
    
    Endpoints:
    - POST /embed/init        → Initialize web embed
    - POST /bot/message       → Send message to bot (requires JWT)
    - POST /webhook/telegram  → Telegram webhook
    - POST /webhook/teams     → Teams webhook
    - POST /admin/tenants     → Create/manage tenants (requires API key)
    """
    
    def __init__(self):
        """Initialize API handler"""
        logger.info("Initializing MultiTenantBotAPI")
        
        # Initialize API handler for routing
        self.api_handler = APIHandler()
        
        # Setup test data if in development
        # Check both "dev" and "development" for compatibility
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["dev", "development"]:
            try:
                setup_test_data()
                logger.info("Test tenant data setup completed")
            except Exception as e:
                logger.warning(f"Failed to setup test data: {e}", exc_info=True)
        else:
            logger.info(f"Skipping test data setup (ENVIRONMENT={env})")
    
    # ========================================================================
    # WEB EMBED FLOW
    # ========================================================================
    
    async def embed_init(self, request) -> Dict[str, Any]:
        """
        POST /embed/init
        
        Initialize web embed session and issue JWT token.
        
        CORS: Handled by framework
        Rate Limit: Per origin (IP-based, before JWT issued)
        """
        try:
            # Parse request body
            body = {}
            if request.method == "POST":
                content_type = request.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    try:
                        body = await request.json()
                    except ValueError as json_error:
                        # Invalid JSON
                        logger.warning(f"Invalid JSON in request body: {json_error}")
                        return {
                            "error": True,
                            "message": "Invalid JSON in request body",
                            "status_code": 400
                        }
                # Empty body or no Content-Type is OK for embed/init (will use defaults)
            
            origin = request.headers.get("Origin", "")
            ip = request.client.host if request.client else None
            
            # Log request
            logger.info(
                f"Embed init request - "
                f"site_id: {body.get('site_id')}, origin: {origin}, ip: {ip}"
            )
            
            # Validate origin is not empty
            if not origin:
                return {
                    "error": True,
                    "message": "Origin header is required for web embed",
                    "status_code": 400
                }
            
            # Initialize embed session
            result = await EmbedInitHandler.initialize(
                request_body=body,
                origin=origin,
                ip=ip
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error in embed_init: {e}", exc_info=True)
            return {
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }
    
    # ========================================================================
    # BOT MESSAGE API
    # ========================================================================
    
    async def bot_message(self, request) -> Dict[str, Any]:
        """
        POST /bot/message
        
        Send message to bot.
        
        Auth: JWT (from Authorization header)
        Rate Limit: Per tenant + user_key
        
        Request:
        {
            "message": "Tôi còn bao nhiêu ngày phép?",
            "sessionId": "session-abc123",
            "attachments": []
        }
        """
        try:
            # Parse request body
            try:
                body = await request.json()
            except Exception as json_error:
                logger.warning(f"Failed to parse JSON body: {json_error}")
                return {
                    "error": True,
                    "message": "Invalid JSON in request body",
                    "status_code": 400
                }
            
            if not body:
                return {
                    "error": True,
                    "message": "Request body is required",
                    "status_code": 400
                }
            
            # Extract JWT from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {
                    "error": True,
                    "message": "Missing or invalid Authorization header",
                    "status_code": 401
                }
            
            token = auth_header[7:]
            
            # Extract tenant_id from query param (for now)
            # In production: could be in JWT or resolved from domain
            tenant_id = request.query_params.get("tenant_id")
            if not tenant_id:
                return {
                    "error": True,
                    "message": "Missing tenant_id parameter",
                    "status_code": 400
                }
            
            # Get origin from header
            origin = request.headers.get("Origin", "")
            ip = request.client.host if request.client else None
            
            # Resolve context from JWT
            try:
                context = MultiTenantAuthMiddleware.resolve_context_from_jwt(
                    token,
                    tenant_id,
                    origin,
                    ip
                )
            except AuthenticationError as e:
                logger.warning(f"JWT verification failed: {e}")
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 401
                }
            
            # Check rate limit
            allowed, rate_status = await RateLimitService.check_rate_limit(
                context.tenant_id,
                context.user_key
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded: {rate_status}")
                return {
                    "error": True,
                    "message": "Rate limit exceeded",
                    "status_code": 429,
                    "details": rate_status,
                }
            
            # Extract message
            message = body.get("message", "").strip()
            if not message:
                return {
                    "error": True,
                    "message": "message is required and non-empty",
                    "status_code": 400
                }
            
            # Get session ID from request or generate from context
            session_id_raw = body.get("sessionId") or body.get("session_id")
            
            # Convert session_id to UUID format if provided (router requires UUID)
            # Create deterministic UUID from session_id + tenant_id for consistency
            if session_id_raw:
                session_id = MultiTenantBotAPI._generate_uuid_from_string(
                    f"{context.tenant_id}:{session_id_raw}"
                )
            else:
                # Generate new session UUID if not provided
                session_id = str(uuid.uuid4())
            
            # Map user_key to UUID for router (create deterministic UUID from user_key)
            # This ensures consistent user_id for router while maintaining multi-tenant isolation
            user_id = MultiTenantBotAPI._generate_user_id_from_key(
                context.tenant_id,
                context.user_key
            )
            
            # Process message through router
            try:
                router_response = await self.api_handler.handle_request(
                    raw_message=message,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "platform": "web_embed",
                        "tenant_id": context.tenant_id,
                        "channel": context.channel,  # Already a string, no .value needed
                        "user_key": context.user_key,
                        "origin": context.origin,
                        "ip": context.ip,
                        "auth_method": context.auth_method,  # Already a string, no .value needed
                    }
                )
                
                # Extract response data
                response_text = router_response.get("message", "Xin lỗi, tôi chưa hiểu câu hỏi của bạn.")
                intent = router_response.get("intent")
                confidence = router_response.get("confidence", 0.0)
                domain = router_response.get("domain")
                trace_id = router_response.get("trace_id")
                
                logger.info(
                    f"Bot message processed - "
                    f"tenant: {context.tenant_id}, user: {context.user_key}, "
                    f"intent: {intent}, confidence: {confidence:.2f}, trace: {trace_id}"
                )
                
                return {
                    "success": True,
                    "data": {
                        "messageId": trace_id or f"msg_{datetime.now().timestamp()}",
                        "response": response_text,
                        "intent": intent,
                        "domain": domain,
                        "confidence": confidence,
                        "followUpActions": router_response.get("followUpActions", []),
                        "traceId": trace_id,
                    }
                }
                
            except InvalidInputError as e:
                logger.warning(f"Invalid input in bot_message: {e}")
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 400
                }
            except RouterError as e:
                logger.error(f"Router error in bot_message: {e}", exc_info=True)
                return {
                    "error": True,
                    "message": "Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn.",
                    "status_code": 500
                }
        
        except Exception as e:
            logger.error(f"Error in bot_message: {e}", exc_info=True)
            return {
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _generate_user_id_from_key(tenant_id: str, user_key: str) -> str:
        """
        Generate deterministic UUID from tenant_id + user_key.
        
        This ensures:
        - Same user_key always maps to same UUID (for session continuity)
        - Different tenants have different UUIDs (isolation)
        - UUID format required by router
        """
        import hashlib
        
        # Create deterministic seed from tenant + user_key
        seed = f"{tenant_id}:{user_key}"
        hash_bytes = hashlib.sha256(seed.encode()).digest()[:16]
        
        # Convert to UUID v4 format (but deterministic)
        return str(uuid.UUID(bytes=hash_bytes))
    
    @staticmethod
    def _generate_uuid_from_string(seed: str) -> str:
        """
        Generate deterministic UUID from string seed.
        
        Args:
            seed: String to generate UUID from
            
        Returns:
            UUID string (deterministic for same seed)
        """
        import hashlib
        
        # Create deterministic hash from seed
        hash_bytes = hashlib.sha256(seed.encode()).digest()[:16]
        
        # Convert to UUID format
        return str(uuid.UUID(bytes=hash_bytes))
    
    # ========================================================================
    # TELEGRAM WEBHOOK
    # ========================================================================
    
    async def telegram_webhook(self, request) -> Dict[str, Any]:
        """
        POST /webhook/telegram?token=<public-token>
        
        Receive webhook from Telegram.
        
        Auth: Bot token verification
        Rate Limit: Per tenant + telegram_user_id
        """
        try:
            # Get bot token from query param
            bot_token = request.query_params.get("token")
            if not bot_token:
                return {
                    "error": True,
                    "message": "Missing bot token",
                    "status_code": 400
                }
            
            # Get tenant ID from header (bot token → tenant mapping)
            # TODO: Implement mapping from bot token to tenant_id
            tenant_id = request.headers.get("X-Telegram-Bot-Id")
            if not tenant_id:
                return {
                    "error": True,
                    "message": "Missing X-Telegram-Bot-Id header",
                    "status_code": 400
                }
            
            # Parse body
            body = await request.body()
            
            # Verify Telegram webhook
            try:
                MultiTenantAuthMiddleware.verify_telegram_webhook(
                    tenant_id,
                    body,
                    bot_token
                )
            except AuthenticationError as e:
                logger.warning(f"Telegram verification failed: {e}")
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 401
                }
            
            # Parse JSON
            data = request.json()
            
            # Extract telegram_user_id
            telegram_user_id = data["message"]["from"]["id"]
            
            # Check rate limit
            allowed, _ = await RateLimitService.check_rate_limit(
                tenant_id,
                str(telegram_user_id)
            )
            
            if not allowed:
                logger.warning(f"Telegram rate limit exceeded: {tenant_id}")
                # Still return 200 OK to Telegram, but don't process
                return {"ok": True}
            
            # Resolve context
            context = MultiTenantAuthMiddleware.resolve_context_from_telegram(
                tenant_id,
                telegram_user_id,
                ip=request.client.host if request.client else None
            )
            
            # TODO: Process message through router
            message_text = data["message"].get("text", "")
            
            logger.info(
                f"Telegram message - "
                f"tenant: {context.tenant_id}, user: {telegram_user_id}, "
                f"message: {message_text[:50]}..."
            )
            
            # Return 200 OK to Telegram (even if processing fails)
            return {"ok": True}
        
        except Exception as e:
            logger.error(f"Error in telegram_webhook: {e}", exc_info=True)
            # Always return 200 OK to Telegram
            return {"ok": True}
    
    # ========================================================================
    # TEAMS WEBHOOK
    # ========================================================================
    
    async def teams_webhook(self, request) -> Dict[str, Any]:
        """
        POST /webhook/teams?token=<public-token>
        
        Receive webhook from Microsoft Teams.
        
        Auth: JWT verification (from Microsoft)
        Rate Limit: Per tenant + aadObjectId
        """
        try:
            # Get authorization header (JWT from Teams)
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {
                    "error": True,
                    "message": "Missing Teams JWT",
                    "status_code": 401
                }
            
            teams_jwt = auth_header[7:]
            
            # Get tenant from query param
            tenant_id = request.query_params.get("tenant_id")
            if not tenant_id:
                return {
                    "error": True,
                    "message": "Missing tenant_id",
                    "status_code": 400
                }
            
            # Verify Teams JWT
            try:
                payload = MultiTenantAuthMiddleware.verify_teams_jwt(
                    teams_jwt,
                    tenant_id
                )
            except AuthenticationError as e:
                logger.warning(f"Teams JWT verification failed: {e}")
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 401
                }
            
            # Parse body
            body = await request.json()
            
            # Extract aadObjectId
            aad_object_id = body["from"].get("aadObjectId")
            
            # Check rate limit
            allowed, _ = await RateLimitService.check_rate_limit(
                tenant_id,
                aad_object_id
            )
            
            if not allowed:
                logger.warning(f"Teams rate limit exceeded: {tenant_id}")
                # Still return to Teams, but don't process
                return {"type": "message", "text": "Rate limit exceeded"}
            
            # Resolve context
            context = MultiTenantAuthMiddleware.resolve_context_from_teams(
                tenant_id,
                aad_object_id,
                ip=request.client.host if request.client else None
            )
            
            # TODO: Process message through router
            message_text = body.get("text", "")
            
            logger.info(
                f"Teams message - "
                f"tenant: {context.tenant_id}, user: {aad_object_id}, "
                f"message: {message_text[:50]}..."
            )
            
            return {
                "type": "message",
                "text": f"Echo: {message_text}"
            }
        
        except Exception as e:
            logger.error(f"Error in teams_webhook: {e}", exc_info=True)
            return {
                "type": "message",
                "text": "Internal server error"
            }
    
    # ========================================================================
    # ADMIN API (Service-to-Service)
    # ========================================================================
    
    async def admin_knowledge_sync(
        self,
        tenant_id: str,
        batch_size: int = 10,
        db_connection = None,
    ) -> Dict[str, Any]:
        """
        POST /admin/tenants/{tenant_id}/knowledge/sync
        
        Trigger manual sync of knowledge base for tenant.
        Requires API key authentication.
        
        Args:
            tenant_id: Tenant UUID
            batch_size: Batch size for processing products
            db_connection: Database connection (injected)
        
        Returns:
            Sync result with statistics
        """
        if not db_connection:
            return {
                "success": False,
                "error": "DATABASE_NOT_AVAILABLE",
                "message": "Database connection not available",
                "status_code": 500,
            }
        
        try:
            from .admin_knowledge_api import AdminKnowledgeAPI
            admin_api = AdminKnowledgeAPI(db_connection)
            return await admin_api.sync_knowledge(tenant_id, batch_size)
        except Exception as e:
            logger.error(f"Error in admin_knowledge_sync: {e}", exc_info=True)
            return {
                "success": False,
                "error": "SYNC_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def admin_knowledge_status(
        self,
        tenant_id: str,
        db_connection = None,
    ) -> Dict[str, Any]:
        """
        GET /admin/tenants/{tenant_id}/knowledge/status
        
        Get current sync status for tenant.
        Requires API key authentication.
        
        Args:
            tenant_id: Tenant UUID
            db_connection: Database connection (injected)
        
        Returns:
            Sync status information
        """
        if not db_connection:
            return {
                "success": False,
                "error": "DATABASE_NOT_AVAILABLE",
                "message": "Database connection not available",
                "status_code": 500,
            }
        
        try:
            from .admin_knowledge_api import AdminKnowledgeAPI
            admin_api = AdminKnowledgeAPI(db_connection)
            return await admin_api.get_sync_status(tenant_id)
        except Exception as e:
            logger.error(f"Error in admin_knowledge_status: {e}", exc_info=True)
            return {
                "success": False,
                "error": "QUERY_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def admin_knowledge_delete(
        self,
        tenant_id: str,
        db_connection = None,
    ) -> Dict[str, Any]:
        """
        DELETE /admin/tenants/{tenant_id}/knowledge
        
        Delete all knowledge base data for tenant.
        Requires API key authentication.
        
        Args:
            tenant_id: Tenant UUID
            db_connection: Database connection (injected)
        
        Returns:
            Deletion result
        """
        if not db_connection:
            return {
                "success": False,
                "error": "DATABASE_NOT_AVAILABLE",
                "message": "Database connection not available",
                "status_code": 500,
            }
        
        try:
            from .admin_knowledge_api import AdminKnowledgeAPI
            admin_api = AdminKnowledgeAPI(db_connection)
            return await admin_api.delete_knowledge(tenant_id)
        except Exception as e:
            logger.error(f"Error in admin_knowledge_delete: {e}", exc_info=True)
            return {
                "success": False,
                "error": "DELETE_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def catalog_webhook(
        self,
        tenant_id: str,
        event_data: Dict[str, Any],
        db_connection = None,
    ) -> Dict[str, Any]:
        """
        POST /webhooks/catalog/product-updated
        
        Receive webhook from catalog service for product updates.
        Requires webhook secret verification (optional).
        
        Args:
            tenant_id: Tenant UUID
            event_data: Webhook payload with event and product_id
            db_connection: Database connection (injected)
        
        Returns:
            Processing result
        """
        if not db_connection:
            return {
                "success": False,
                "error": "DATABASE_NOT_AVAILABLE",
                "message": "Database connection not available",
                "status_code": 500,
            }
        
        try:
            from .webhooks.catalog_webhook import CatalogWebhookHandler
            webhook_handler = CatalogWebhookHandler(db_connection)
            
            event = event_data.get("event")  # 'created', 'updated', 'deleted'
            product_id = event_data.get("product_id")
            
            if not event or not product_id:
                return {
                    "success": False,
                    "error": "INVALID_PAYLOAD",
                    "message": "Missing event or product_id in payload",
                    "status_code": 400,
                }
            
            result = await webhook_handler.handle_product_event(
                tenant_id=tenant_id,
                event=event,
                product_id=product_id,
            )
            
            return {
                "success": result.get("success", False),
                "data": result,
            }
            
        except Exception as e:
            logger.error(f"Error in catalog_webhook: {e}", exc_info=True)
            return {
                "success": False,
                "error": "WEBHOOK_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def admin_create_tenant(self, request) -> Dict[str, Any]:
        """
        POST /admin/tenants
        
        Create new tenant (requires API key).
        
        Auth: API key (Bearer token or query param)
        
        Request:
        {
            "name": "GSNAKE Catalog",
            "site_id": "catalog-001",
            "web_embed_origins": ["https://gsnake.com"],
            "plan": "professional"
        }
        """
        try:
            # TODO: Verify API key
            # Placeholder: skip auth check for now
            
            body = await request.json()
            
            # TODO: Create tenant in database
            # For now: return mock response
            
            tenant_id = "tenant_" + body.get("site_id", "unknown")
            
            logger.info(f"Created tenant: {tenant_id}")
            
            return {
                "success": True,
                "data": {
                    "tenant_id": tenant_id,
                    "api_key": f"api_key_{tenant_id}",
                    "jwt_secret": "secret_" + tenant_id,
                }
            }
        
        except Exception as e:
            logger.error(f"Error in admin_create_tenant: {e}", exc_info=True)
            return {
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }

