"""
Auth configuration helper functions.
Phục vụ multi-tenant auth system.
"""

from typing import Optional, List
from ..schemas.multi_tenant_types import TenantConfig
from ..shared.logger import logger


# ============================================================================
# MULTI-TENANT AUTH HELPERS
# ============================================================================

# Placeholder: Trong production, dữ liệu này sẽ đến từ database
_TENANT_CONFIGS: dict = {}
_TENANT_SECRETS: dict = {}


def get_tenant_config(tenant_id: str) -> Optional[TenantConfig]:
    """
    Get tenant configuration from database.
    TODO: Implement database lookup
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        TenantConfig or None if not found
    """
    # Placeholder implementation
    if tenant_id in _TENANT_CONFIGS:
        return _TENANT_CONFIGS[tenant_id]
    
    logger.warning(f"Tenant config not found: {tenant_id}")
    return None


def get_jwt_secret(tenant_id: str) -> Optional[str]:
    """
    Get JWT secret for tenant.
    TODO: Implement database lookup and caching
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        JWT secret or None if not found
    """
    # Placeholder implementation
    if tenant_id in _TENANT_SECRETS:
        return _TENANT_SECRETS[tenant_id]
    
    logger.warning(f"JWT secret not found for tenant: {tenant_id}")
    return None


def validate_origin(tenant_id: str, origin: str) -> bool:
    """
    Validate if origin is allowed for tenant's web embed.
    
    Args:
        tenant_id: Tenant ID
        origin: Request origin (from Origin header)
    
    Returns:
        True if origin is allowed
    """
    config = get_tenant_config(tenant_id)
    if not config or not config.web_embed_enabled:
        logger.warning(f"Web embed not enabled for tenant: {tenant_id}")
        return False
    
    if not config.web_embed_origins:
        logger.warning(f"No allowed origins configured for tenant: {tenant_id}")
        return False
    
    # Check if origin in allowed list
    # Support wildcards for development: *.example.com
    for allowed in config.web_embed_origins:
        if allowed == "*":
            return True  # Only for development!
        
        if allowed == origin:
            return True
        
        # Wildcard matching (simple)
        if allowed.startswith("*.") and origin.endswith(allowed[1:]):
            return True
    
    logger.warning(f"Origin not allowed for tenant {tenant_id}: {origin}")
    return False


def get_rate_limit_config(tenant_id: str) -> Optional[dict]:
    """
    Get rate limit configuration for tenant.
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        Rate limit config {per_minute, per_hour, per_day}
    """
    config = get_tenant_config(tenant_id)
    if not config:
        return None
    
    # Map plan to rate limits
    # See multi_tenant_types.py for actual config
    limits = {
        "basic": {"per_minute": 20, "per_hour": 1000, "per_day": 10000},
        "professional": {"per_minute": 100, "per_hour": 5000, "per_day": 50000},
        "enterprise": {"per_minute": 1000, "per_hour": 100000, "per_day": 1000000},
    }
    
    return limits.get(config.plan, limits["basic"])


def is_tenant_active(tenant_id: str) -> bool:
    """Check if tenant is active (not suspended/deleted)"""
    config = get_tenant_config(tenant_id)
    return config is not None


def is_channel_enabled(tenant_id: str, channel: str) -> bool:
    """Check if channel is enabled for tenant"""
    config = get_tenant_config(tenant_id)
    if not config:
        return False
    
    if channel == "web":
        return config.web_embed_enabled
    elif channel == "telegram":
        return config.telegram_enabled
    elif channel == "teams":
        return config.teams_enabled
    
    return False


# ============================================================================
# TEST HELPERS (development only)
# ============================================================================

def register_test_tenant(
    tenant_id: str,
    name: str,
    jwt_secret: str,
    config: Optional[TenantConfig] = None
):
    """Register a test tenant (development only)"""
    _TENANT_SECRETS[tenant_id] = jwt_secret
    
    if config:
        _TENANT_CONFIGS[tenant_id] = config
    else:
        _TENANT_CONFIGS[tenant_id] = TenantConfig(
            id=tenant_id,
            name=name,
            api_key=f"api_key_{tenant_id}",
            web_embed_jwt_secret=jwt_secret,
            web_embed_origins=[
                "http://localhost:3000",
                "http://localhost:3001",  # Catalog frontend default port
                "https://example.com",
                "*"  # Allow all origins in development
            ],
        )
    
    logger.info(f"Registered test tenant: {tenant_id}")
