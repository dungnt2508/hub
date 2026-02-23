"""
Authentication Middleware - JWT-based authentication
"""

from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from app.core.services.auth_service import AuthService
from app.infrastructure.database.engine import get_session_maker
import logging

logger = logging.getLogger(__name__)


def get_bearer_token(request: Request) -> Optional[str]:
    """
    Extract Bearer token from Authorization header
    
    Args:
        request: FastAPI request
        
    Returns:
        Token string or None
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    # Check if it's Bearer token
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "").strip()
    return token if token else None


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for JWT-based auth
    
    Validates JWT token and sets user/tenant info in request.state
    """
    
    def __init__(self, app, require_auth: bool = True):
        """
        Args:
            app: ASGI application
            require_auth: Whether authentication is required (default: True)
        """
        super().__init__(app)
        self.require_auth = require_auth
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add user/tenant info to request.state
        
        Skip authentication for public endpoints
        """
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
            response = await call_next(request)
            return response
        
        # Skip authentication for public endpoints
        public_paths = [
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            # /api/v1/tenants REMOVED - Admin API requires JWT
            "/api/v1/chat/widget-message",  # Public widget chat
            "/webhooks/zalo/message",
            "/webhooks/facebook/message",
        ]
        
        if request.url.path in public_paths:
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
            response = await call_next(request)
            return response

        # WebSocket Monitor (token validation in endpoint - browser WS cannot send headers)
        if request.url.path.startswith("/api/v1/ws/"):
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
            response = await call_next(request)
            return response

        # Webhook paths (including path-based: /webhooks/zalo/{tenant_id}/{bot_id}/message)
        if request.url.path.startswith("/webhooks/"):
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
            response = await call_next(request)
            return response
        
        # Extract token
        token = get_bearer_token(request)
        
        # If authentication is required but no token provided
        if self.require_auth and not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required. Please provide a valid JWT token in Authorization header."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # If no token, continue without auth (for backward compatibility)
        if not token:
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
            response = await call_next(request)
            return response
        
        # Validate token and get user
        session_maker = get_session_maker()
        async with session_maker() as db:
            user = await AuthService.get_user_from_token(db, token)
            
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Set user info in request state
            request.state.user_id = user.id
            request.state.tenant_id = user.tenant_id
            request.state.user_role = user.role
            request.state.user_email = user.email
        
        response = await call_next(request)
        return response
