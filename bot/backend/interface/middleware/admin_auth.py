"""
Admin Authentication Middleware
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...domain.admin.admin_auth_service import admin_auth_service
from ...shared.logger import logger
from ...shared.exceptions import AuthenticationError, AuthorizationError


# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current admin user from JWT token.
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        token = credentials.credentials
        user = await admin_auth_service.get_user_from_token(token)
        return user
    except AuthenticationError as e:
        logger.warning(f"Admin authentication failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in admin authentication: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")


def require_role(allowed_roles: list[str]):
    """
    Dependency factory: Require specific role(s).
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            current_user: dict = Depends(require_role(["admin", "operator"]))
        ):
            ...
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_admin_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory: Require specific permission.
    
    Usage:
        @router.delete("/endpoint")
        async def endpoint(
            current_user: dict = Depends(require_permission("can_delete_configs"))
        ):
            ...
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_admin_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        user_permissions = current_user.get("permissions", {})
        
        # Admin has all permissions
        if user_role == "admin":
            return current_user
        
        # Check specific permission
        if not user_permissions.get(permission, False):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required permission: {permission}"
            )
        
        return current_user
    
    return permission_checker


# Role-based dependencies
require_admin = require_role(["admin"])
require_admin_or_operator = require_role(["admin", "operator"])
require_any_role = require_role(["admin", "operator", "viewer"])

