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
from .handlers.embed_init_handler import EmbedInitHandler
from .api_handler import APIHandler
from backend.infrastructure.rate_limiter import RateLimitService
from backend.shared.logger import logger, set_logging_context
from backend.shared.metrics import RequestMetrics
from backend.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
    RouterError,
    InvalidInputError,
)
from backend.shared.error_formatter import ErrorFormatter, ErrorCode
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
        
        # Priority 2 Fix: Remove test data from production
        # Test data should only be created via scripts or tests, not in application startup
        # Use scripts/create_tenant.py or POST /admin/tenants to create real tenants
    
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
                        # Task 8: Use standardized error formatter
                        return ErrorFormatter.format_error(
                            error_code=ErrorCode.INVALID_FORMAT,
                            status_code=400,
                            custom_message="Invalid JSON in request body",
                            log_context={
                                "endpoint": "embed_init",
                                "exception": json_error,
                            }
                        )
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
                # Task 8: Use standardized error formatter
                return ErrorFormatter.format_error(
                    error_code=ErrorCode.MISSING_REQUIRED_FIELD,
                    status_code=400,
                    custom_message="Origin header is required for web embed",
                    log_context={"endpoint": "embed_init"}
                )
            
            # Initialize embed session
            result = await EmbedInitHandler.initialize(
                request_body=body,
                origin=origin,
                ip=ip
            )
            
            return result
        
        except Exception as e:
            # Task 8: Use standardized error formatter
            return ErrorFormatter.format_exception(
                exception=e,
                status_code=500,
                log_context={"endpoint": "embed_init"}
            )
    
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
                # Task 8: Use standardized error formatter
                return ErrorFormatter.format_error(
                    error_code=ErrorCode.INVALID_FORMAT,
                    status_code=400,
                    custom_message="Invalid JSON in request body",
                    log_context={"endpoint": "bot_message", "exception": json_error}
                )
            
            if not body:
                # Task 8: Use standardized error formatter
                return ErrorFormatter.format_error(
                    error_code=ErrorCode.MISSING_REQUIRED_FIELD,
                    status_code=400,
                    custom_message="Request body is required",
                    log_context={"endpoint": "bot_message"}
                )
            
            # Extract JWT from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                # Task 8: Use standardized error formatter
                return ErrorFormatter.format_error(
                    error_code=ErrorCode.MISSING_TOKEN,
                    status_code=401,
                    log_context={"endpoint": "bot_message"}
                )
            
            token = auth_header[7:]
            
            # Priority 1 Fix: Extract tenant_id from JWT payload, NOT from query param
            # This prevents tenant spoofing attacks
            try:
                # Decode JWT without verification first to get tenant_id
                import jwt as jwt_lib
                unverified_payload = jwt_lib.decode(token, options={"verify_signature": False})
                tenant_id_from_jwt = unverified_payload.get("tenant_id")
                
                if not tenant_id_from_jwt:
                    # Task 8: Use standardized error formatter
                    return ErrorFormatter.format_error(
                        error_code=ErrorCode.INVALID_TOKEN,
                        status_code=401,
                        custom_message="Invalid token: missing tenant_id",
                        log_context={"endpoint": "bot_message"}
                    )
            except Exception as e:
                # Task 8: Use standardized error formatter
                return ErrorFormatter.format_error(
                    error_code=ErrorCode.INVALID_TOKEN,
                    status_code=401,
                    custom_message="Invalid token format",
                    log_context={"endpoint": "bot_message", "exception": e}
                )
            
            # Get origin from header
            origin = request.headers.get("Origin", "")
            ip = request.client.host if request.client else None
            
            # Task 9: Set logging context (will be available in all logs)
            request_id = str(uuid.uuid4())
            set_logging_context(
                tenant_id=tenant_id_from_jwt,
                request_id=request_id,
            )
            
            # Task 9: Track request metrics
            with RequestMetrics(
                tenant_id=tenant_id_from_jwt,
                endpoint="/bot/message",
                method="POST",
            ) as metrics:
                # Resolve context from JWT (this will verify signature and validate tenant_id)
                try:
                    context = await MultiTenantAuthMiddleware.resolve_context_from_jwt(
                        token,
                        tenant_id_from_jwt,  # Use tenant_id from JWT, not query param
                        origin,
                        ip
                    )
                except AuthenticationError as e:
                    # Task 8: Use standardized error formatter
                    metrics.status_code = 401
                    return ErrorFormatter.format_exception(
                        exception=e,
                        status_code=401,
                        request_id=request_id,
                        log_context={
                            "endpoint": "bot_message",
                            "tenant_id": tenant_id_from_jwt,
                        }
                    )
                
                # Check rate limit
                allowed, rate_status = await RateLimitService.check_rate_limit(
                    context.tenant_id,
                    context.user_key
                )
                
                if not allowed:
                    # Task 8: Use standardized error formatter
                    metrics.status_code = 429
                    return ErrorFormatter.format_error(
                        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                        status_code=429,
                        request_id=request_id,
                        details=ErrorFormatter._sanitize_details(rate_status),
                        log_context={
                            "endpoint": "bot_message",
                            "tenant_id": context.tenant_id,
                            "user_key": context.user_key,
                        }
                    )
                
                # Extract message
                message = body.get("message", "").strip()
                if not message:
                    # Task 8: Use standardized error formatter
                    metrics.status_code = 400
                    return ErrorFormatter.format_error(
                        error_code=ErrorCode.MISSING_REQUIRED_FIELD,
                        status_code=400,
                        request_id=request_id,
                        custom_message="message is required and non-empty",
                        log_context={
                            "endpoint": "bot_message",
                            "tenant_id": context.tenant_id,
                        }
                    )
                
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
                
                # Save conversation to database (user_keys, conversations, conversation_messages)
                try:
                    from backend.domain.tenant.conversation_service import ConversationService
                    from backend.infrastructure.database_client import database_client
                    
                    async with database_client.pool.acquire() as conn:
                        conv_service = ConversationService(conn)
                        
                        # 1. Ensure user_key exists
                        await conv_service.ensure_user_key(
                            tenant_id=context.tenant_id,
                            channel=context.channel,
                            user_key=context.user_key,
                        )
                        
                        # 2. Get or create conversation
                        conversation_id = await conv_service.get_or_create_conversation(
                            tenant_id=context.tenant_id,
                            channel=context.channel,
                            user_key=context.user_key,
                        )
                        
                        if conversation_id:
                            # 3. Add user message
                            await conv_service.add_message(
                                conversation_id=conversation_id,
                                role="user",
                                content=message,
                                metadata={
                                    "trace_id": trace_id,
                                    "ip": context.ip,
                                    "origin": context.origin,
                                }
                            )
                            
                            # 4. Add assistant response
                            await conv_service.add_message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=response_text,
                                intent=intent,
                                confidence=confidence,
                                metadata={
                                    "trace_id": trace_id,
                                    "domain": domain,
                                }
                            )
                            
                            # 5. Update conversation context if needed
                            if domain or intent:
                                await conv_service.save_conversation_context(
                                    conversation_id=conversation_id,
                                    context_data={
                                        "last_domain": domain,
                                        "last_intent": intent,
                                        "last_confidence": confidence,
                                    }
                                )
                        
                except Exception as e:
                    # Don't fail the request if conversation saving fails
                    logger.warning(f"Failed to save conversation: {e}", exc_info=True)
                
                # Priority 2: Audit log bot message
                from backend.shared.audit_helper import log_tenant_operation
                await log_tenant_operation(
                    tenant_id=context.tenant_id,
                    operation="message",
                    resource_type="conversation",
                    resource_id=session_id,
                    user_key=context.user_key,
                    channel=context.channel,
                    ip_address=context.ip,
                    request_id=trace_id,
                    metadata={
                        "intent": intent,
                        "domain": domain,
                        "confidence": confidence,
                        "message_length": len(message),
                    }
                )
                
                    # Task 9: Update metrics status code and trace_id
                    metrics.status_code = 200
                    set_logging_context(
                        tenant_id=context.tenant_id,
                        request_id=request_id,
                        trace_id=trace_id,
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
                    # Task 8: Use standardized error formatter
                    metrics.status_code = 400
                    return ErrorFormatter.format_exception(
                        exception=e,
                        status_code=400,
                        request_id=request_id,
                        log_context={
                            "endpoint": "bot_message",
                            "tenant_id": context.tenant_id,
                        }
                    )
                except RouterError as e:
                    # Task 8: Use standardized error formatter
                    metrics.status_code = 500
                    return ErrorFormatter.format_exception(
                        exception=e,
                        status_code=500,
                        request_id=request_id,
                        log_context={
                            "endpoint": "bot_message",
                            "tenant_id": context.tenant_id,
                        }
                    )
        
        except Exception as e:
            # Task 8: Use standardized error formatter
            return ErrorFormatter.format_exception(
                exception=e,
                status_code=500,
                log_context={"endpoint": "bot_message"}
            )
    
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
            # Task 3.3: Get bot token from query param and resolve tenant_id from database
            # DO NOT trust tenant_id from header (security risk)
            bot_token = request.query_params.get("token")
            if not bot_token:
                return {
                    "error": True,
                    "message": "Missing bot token",
                    "status_code": 400
                }
            
            # Resolve tenant_id from bot token (from database, not from header)
            from backend.infrastructure.database_client import database_client
            if not database_client.pool:
                return {
                    "error": True,
                    "message": "Database connection not available",
                    "status_code": 500
                }
            
            async with database_client.pool.acquire() as conn:
                from backend.domain.tenant.tenant_service import TenantService
                tenant_service = TenantService(conn)
                
                tenant_id = await tenant_service.resolve_tenant_id_from_telegram_bot_token(bot_token)
                
                if not tenant_id:
                    logger.warning(f"Telegram bot token not found or tenant inactive: {bot_token[:8]}...")
                    return {
                        "error": True,
                        "message": "Invalid bot token or tenant not found",
                        "status_code": 401
                    }
            
            # Validate tenant exists and is active
            from backend.shared.auth_config import validate_tenant_id
            if not await validate_tenant_id(tenant_id):
                return {
                    "error": True,
                    "message": "Tenant not found or inactive",
                    "status_code": 403
                }
            
            # Parse body
            body = await request.body()
            
            # Verify Telegram webhook (verify bot token matches tenant config)
            try:
                await MultiTenantAuthMiddleware.verify_telegram_webhook(
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
            
            # Priority 2: Audit log Telegram message
            from backend.shared.audit_helper import log_tenant_operation
            ip = request.client.host if request.client else None
            await log_tenant_operation(
                tenant_id=context.tenant_id,
                operation="message",
                resource_type="conversation",
                user_key=context.user_key,
                channel="telegram",
                ip_address=ip,
                metadata={
                    "telegram_user_id": telegram_user_id,
                    "message_length": len(message_text),
                }
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
        POST /webhook/teams
        
        Receive webhook from Microsoft Teams.
        
        Auth: JWT verification (from Microsoft)
        Rate Limit: Per tenant + aadObjectId
        
        Task 1.3: Extract tenant_id from JWT payload, NOT from query param.
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
            
            # Task 1.3: Verify Teams JWT FIRST to extract tenant_id from payload
            # DO NOT trust tenant_id from query param (security risk)
            try:
                payload = await MultiTenantAuthMiddleware.verify_teams_jwt(
                    teams_jwt,
                    tenant_id=None  # Extract from JWT payload
                )
            except AuthenticationError as e:
                logger.warning(f"Teams JWT verification failed: {e}")
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 401
                }
            
            # Extract tenant_id from verified JWT payload
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                # Try alternative locations in payload
                tenant_id = payload.get("tenantId") or payload.get("conversation", {}).get("tenantId")
            
            if not tenant_id:
                logger.error("No tenant_id found in Teams JWT payload")
                return {
                    "error": True,
                    "message": "JWT missing tenant_id",
                    "status_code": 401
                }
            
            # Validate tenant exists and is active
            from backend.shared.auth_config import is_tenant_active
            if not await is_tenant_active(tenant_id):
                logger.warning(f"Tenant not found or inactive: {tenant_id}")
                return {
                    "error": True,
                    "message": "Tenant not found or inactive",
                    "status_code": 403
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
            
            # Priority 2: Audit log Teams message
            from backend.shared.audit_helper import log_tenant_operation
            ip = request.client.host if request.client else None
            await log_tenant_operation(
                tenant_id=context.tenant_id,
                operation="message",
                resource_type="conversation",
                user_key=context.user_key,
                channel="teams",
                ip_address=ip,
                metadata={
                    "aad_object_id": aad_object_id,
                    "message_length": len(message_text),
                }
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
            from backend.domain.tenant.audit_service import TenantAuditService
            
            admin_api = AdminKnowledgeAPI(db_connection)
            result = await admin_api.sync_knowledge(tenant_id, batch_size)
            
            # Priority 2: Audit log knowledge sync
            if result.get("success"):
                audit_service = TenantAuditService(db_connection)
                await audit_service.log_operation(
                    tenant_id=tenant_id,
                    operation="sync",
                    resource_type="knowledge",
                    channel="api",
                    metadata={
                        "batch_size": batch_size,
                        "products_synced": result.get("data", {}).get("products_synced", 0),
                        "products_failed": result.get("data", {}).get("products_failed", 0),
                    }
                )
            
            return result
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
            from backend.domain.tenant.audit_service import TenantAuditService
            
            admin_api = AdminKnowledgeAPI(db_connection)
            result = await admin_api.delete_knowledge(tenant_id)
            
            # Priority 2: Audit log knowledge deletion
            if result.get("success"):
                audit_service = TenantAuditService(db_connection)
                await audit_service.log_operation(
                    tenant_id=tenant_id,
                    operation="delete",
                    resource_type="knowledge",
                    channel="api",
                    metadata={
                        "deleted_count": result.get("data", {}).get("deleted_count", 0),
                    }
                )
            
            return result
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
        Task 6: Webhook secret verification is done in the endpoint handler.
        
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
            "web_embed_origins": ["https://gsnake.com", "https://www.gsnake.com"],
            "plan": "professional",
            "telegram_enabled": false,
            "teams_enabled": false
        }
        """
        try:
            # Task 2.2: API key verification is handled by require_api_key decorator
            # Context is injected into request.state.user_context by decorator
            # Verify that context exists (should be set by decorator)
            if not hasattr(request, 'state') or not hasattr(request.state, 'user_context'):
                logger.error("API key verification failed: context not found")
                return {
                    "error": True,
                    "message": "Authentication required",
                    "status_code": 401
                }
            
            # Get tenant_id from verified context (set by require_api_key decorator)
            context = request.state.user_context
            verified_tenant_id = context.tenant_id
            
            body = await request.json()
            
            # Validate required fields
            name = body.get("name")
            site_id = body.get("site_id")
            web_embed_origins = body.get("web_embed_origins", [])
            plan = body.get("plan", "basic")
            telegram_enabled = body.get("telegram_enabled", False)
            teams_enabled = body.get("teams_enabled", False)
            
            if not name or not name.strip():
                return {
                    "error": True,
                    "message": "name is required",
                    "status_code": 400
                }
            
            if not site_id or not site_id.strip():
                return {
                    "error": True,
                    "message": "site_id is required",
                    "status_code": 400
                }
            
            if not web_embed_origins or len(web_embed_origins) == 0:
                return {
                    "error": True,
                    "message": "web_embed_origins is required and non-empty",
                    "status_code": 400
                }
            
            # Get database connection
            from backend.infrastructure.database_client import database_client
            if not database_client.pool:
                return {
                    "error": True,
                    "message": "Database connection not available",
                    "status_code": 500
                }
            
            # Create tenant using TenantService
            async with database_client.pool.acquire() as conn:
                from backend.domain.tenant.tenant_service import TenantService
                from backend.domain.tenant.audit_service import TenantAuditService
                
                tenant_service = TenantService(conn)
                audit_service = TenantAuditService(conn)
                
                result = await tenant_service.create_tenant(
                    name=name,
                    site_id=site_id,
                    web_embed_origins=web_embed_origins,
                    plan=plan,
                    telegram_enabled=telegram_enabled,
                    teams_enabled=teams_enabled,
                )
                
                if result.get("success"):
                    tenant_id = result['data']['tenant_id']
                    logger.info(f"✅ Tenant created via API: {tenant_id}")
                    
                    # Priority 2: Audit log admin tenant creation
                    # Use verified_tenant_id from API key (the tenant that created this new tenant)
                    ip = request.client.host if request.client else None
                    await audit_service.log_operation(
                        tenant_id=verified_tenant_id,  # Tenant that performed the action
                        operation="create",
                        resource_type="tenant",
                        resource_id=tenant_id,  # New tenant that was created
                        channel="api",
                        ip_address=ip,
                        metadata={
                            "created_via": "admin_api",
                            "site_id": site_id,
                            "plan": plan,
                            "created_by_tenant": verified_tenant_id,
                        }
                    )
                    
                    return result
                else:
                    return {
                        "error": True,
                        "message": result.get("message", "Failed to create tenant"),
                        "status_code": 400
                    }
        
        except Exception as e:
            logger.error(f"Error in admin_create_tenant: {e}", exc_info=True)
            return {
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }

