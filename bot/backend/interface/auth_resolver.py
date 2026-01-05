"""
Auth Context Resolver - Centralized authentication context resolution
"""
from typing import Optional, Dict, Any, Tuple
from fastapi import Request

from .middleware.multi_tenant_auth import MultiTenantAuthMiddleware, RequestContext
from ..shared.logger import logger
from ..shared.exceptions import AuthenticationError, InvalidInputError


class AuthContextResolver:
    """
    Centralized authentication context resolution.
    
    Handles:
    - JWT token extraction
    - Context resolution from JWT
    - Tenant ID extraction
    - Rate limiting checks
    """
    
    @staticmethod
    def extract_jwt_token(request: Request) -> str:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JWT token string
            
        Raises:
            AuthenticationError: If token is missing or invalid
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    @staticmethod
    def extract_tenant_id(request: Request, required: bool = True) -> Optional[str]:
        """
        Extract tenant_id from query params or path.
        
        Args:
            request: FastAPI request object
            required: Whether tenant_id is required
            
        Returns:
            Tenant ID string or None
            
        Raises:
            InvalidInputError: If tenant_id is required but missing
        """
        tenant_id = request.query_params.get("tenant_id")
        
        # Try path param if not in query
        if not tenant_id and hasattr(request, "path_params"):
            tenant_id = request.path_params.get("tenant_id")
        
        if required and not tenant_id:
            raise InvalidInputError("Missing tenant_id parameter")
        
        return tenant_id
    
    @staticmethod
    def extract_request_metadata(request: Request) -> dict:
        """
        Extract request metadata (origin, IP, etc.).
        
        Args:
            request: FastAPI request object
            
        Returns:
            Metadata dict with origin, ip, etc.
        """
        return {
            "origin": request.headers.get("Origin", ""),
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent", ""),
        }
    
    @staticmethod
    def resolve_context_from_jwt(
        request: Request,
        tenant_id: Optional[str] = None
    ) -> RequestContext:
        """
        Resolve authentication context from JWT token.
        
        Args:
            request: FastAPI request object
            tenant_id: Optional tenant_id (will extract from request if not provided)
            
        Returns:
            RequestContext with tenant_id, user_key, channel, etc.
            
        Raises:
            AuthenticationError: If JWT verification fails
            InvalidInputError: If tenant_id is missing
        """
        # Extract JWT token
        token = AuthContextResolver.extract_jwt_token(request)
        
        # Extract tenant_id if not provided
        if not tenant_id:
            tenant_id = AuthContextResolver.extract_tenant_id(request, required=True)
        
        # Extract metadata
        metadata = AuthContextResolver.extract_request_metadata(request)
        
        # Resolve context from JWT
        try:
            context = MultiTenantAuthMiddleware.resolve_context_from_jwt(
                token=token,
                tenant_id=tenant_id,
                origin=metadata["origin"],
                ip=metadata["ip"]
            )
            return context
        except AuthenticationError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise
    
    @staticmethod
    async def resolve_context_with_rate_limit(
        request: Request,
        tenant_id: Optional[str] = None
    ) -> Tuple[RequestContext, Optional[Dict[str, Any]]]:
        """
        Resolve context and check rate limit.
        
        Args:
            request: FastAPI request object
            tenant_id: Optional tenant_id
            
        Returns:
            Tuple of (RequestContext, rate_status)
            - If rate limit OK: (context, None)
            - If rate limit exceeded: (context, rate_status dict)
            
        Raises:
            AuthenticationError: If authentication fails
            InvalidInputError: If validation fails
        """
        from ..infrastructure.rate_limiter import RateLimitService
        
        # Resolve context
        context = AuthContextResolver.resolve_context_from_jwt(request, tenant_id)
        
        # Check rate limit
        allowed, rate_status = await RateLimitService.check_rate_limit(
            context.tenant_id,
            context.user_key
        )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded: {rate_status}")
            return (context, rate_status)
        
        return (context, None)

