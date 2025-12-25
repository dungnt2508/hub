"""
Auth configuration helper functions.
Phục vụ multi-tenant auth system.

Priority 1 Fix: Query từ database thay vì in-memory dict.
"""

from typing import Optional, List
from ..schemas.multi_tenant_types import TenantConfig
from ..shared.logger import logger


# ============================================================================
# MULTI-TENANT AUTH HELPERS
# ============================================================================

# Global database connection (injected at startup)
_db_connection = None


def set_db_connection(db_connection):
    """Set database connection for auth config functions"""
    global _db_connection
    _db_connection = db_connection
    logger.info("Database connection set for auth_config")


async def get_tenant_config(tenant_id: str) -> Optional[TenantConfig]:
    """
    Get tenant configuration from database.
    
    Priority 1 Fix: Query từ database thay vì in-memory dict.
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        TenantConfig or None if not found
    """
    if not _db_connection:
        logger.warning("Database connection not available for get_tenant_config")
        return None
    
    try:
        query = """
        SELECT id, name, api_key, webhook_secret, plan,
               rate_limit_per_hour, rate_limit_per_day,
               web_embed_enabled, web_embed_origins, web_embed_jwt_secret,
               web_embed_token_expiry_seconds,
               telegram_enabled, telegram_bot_token,
               teams_enabled, teams_app_id, teams_app_password,
               created_at, updated_at, is_active
        FROM tenants
        WHERE id = $1 AND is_active = true
        """
        
        # Acquire connection from pool
        async with _db_connection.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id)
            if not row:
                logger.warning(f"Tenant config not found: {tenant_id}")
                return None
            
            # Construct TenantConfig inside the context to ensure row data is accessible
            config = TenantConfig(
                id=str(row['id']),
                name=row['name'],
                api_key=row['api_key'],
                webhook_secret=row['webhook_secret'],
                plan=row['plan'],
                rate_limit_per_hour=row['rate_limit_per_hour'],
                rate_limit_per_day=row['rate_limit_per_day'],
                web_embed_enabled=row['web_embed_enabled'],
                web_embed_origins=row['web_embed_origins'] or [],
                web_embed_jwt_secret=row['web_embed_jwt_secret'],
                web_embed_token_expiry_seconds=row['web_embed_token_expiry_seconds'],
                telegram_enabled=row['telegram_enabled'],
                telegram_bot_token=row['telegram_bot_token'],
                teams_enabled=row['teams_enabled'],
                teams_app_id=row['teams_app_id'],
                teams_app_password=row['teams_app_password'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
        
        return config
    
    except Exception as e:
        logger.error(f"Error fetching tenant config: {e}", exc_info=True)
        return None


async def get_jwt_secret(tenant_id: str) -> Optional[str]:
    """
    Get JWT secret for tenant from database.
    
    Priority 1 Fix: Query từ database thay vì in-memory dict.
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        JWT secret or None if not found
    """
    if not _db_connection:
        logger.warning("Database connection not available for get_jwt_secret")
        return None
    
    try:
        query = """
        SELECT web_embed_jwt_secret
        FROM tenants
        WHERE id = $1 AND is_active = true
        """
        
        # Acquire connection from pool
        async with _db_connection.acquire() as conn:
            secret = await conn.fetchval(query, tenant_id)
            if not secret:
                logger.warning(f"JWT secret not found for tenant: {tenant_id}")
                return None
        
        return secret
    
    except Exception as e:
        logger.error(f"Error fetching JWT secret: {e}", exc_info=True)
        return None


# Synchronous wrapper for backward compatibility (deprecated, use async version)
def get_tenant_config_sync(tenant_id: str) -> Optional[TenantConfig]:
    """
    Synchronous wrapper (deprecated).
    Use get_tenant_config() async version instead.
    """
    logger.warning("get_tenant_config_sync is deprecated, use async get_tenant_config")
    return None


def get_jwt_secret_sync(tenant_id: str) -> Optional[str]:
    """
    Synchronous wrapper (deprecated).
    Use get_jwt_secret() async version instead.
    """
    logger.warning("get_jwt_secret_sync is deprecated, use async get_jwt_secret")
    return None


async def validate_origin(tenant_id: str, origin: str) -> bool:
    """
    Validate if origin is allowed for tenant's web embed.
    
    Priority 1 Fix: Query từ database.
    
    Args:
        tenant_id: Tenant ID
        origin: Request origin (from Origin header)
    
    Returns:
        True if origin is allowed
    """
    config = await get_tenant_config(tenant_id)
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
    
    # Log at INFO level with context for debugging - shows what origins are allowed
    logger.info(
        f"Origin validation failed - tenant: {tenant_id}, "
        f"requested origin: {origin}, "
        f"allowed origins: {config.web_embed_origins}"
    )
    return False


async def get_rate_limit_config(tenant_id: str) -> Optional[dict]:
    """
    Get rate limit configuration for tenant.
    
    Priority 1 Fix: Query từ database.
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        Rate limit config {per_minute, per_hour, per_day}
    """
    config = await get_tenant_config(tenant_id)
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


async def is_tenant_active(tenant_id: str) -> bool:
    """Check if tenant is active (not suspended/deleted)"""
    config = await get_tenant_config(tenant_id)
    return config is not None


async def validate_tenant_id(tenant_id: str) -> bool:
    """
    Validate tenant_id exists and is active.
    
    Task 3.4: Add tenant_id validation function.
    
    Args:
        tenant_id: Tenant UUID to validate
    
    Returns:
        True if tenant exists and is active, False otherwise
    """
    if not tenant_id or not tenant_id.strip():
        logger.warning("Empty tenant_id provided for validation")
        return False
    
    # Check if tenant exists and is active
    is_active = await is_tenant_active(tenant_id)
    
    if not is_active:
        logger.warning(f"Tenant validation failed: {tenant_id} not found or inactive")
        return False
    
    return True


async def is_channel_enabled(tenant_id: str, channel: str) -> bool:
    """Check if channel is enabled for tenant"""
    config = await get_tenant_config(tenant_id)
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
# TEST HELPERS (DEPRECATED - Priority 2 Fix)
# ============================================================================

# Priority 2 Fix: register_test_tenant() is DEPRECATED
# This function is kept for backward compatibility with test scripts only.
# DO NOT use in production code.
# 
# To create tenants, use:
# 1. POST /admin/tenants API endpoint (recommended)
# 2. scripts/create_tenant.py script
# 3. TenantService.create_tenant() directly
#
# All tenant data should come from database, not in-memory dictionaries.

def register_test_tenant(
    tenant_id: str,
    name: str,
    jwt_secret: str,
    config: Optional[TenantConfig] = None
):
    """
    DEPRECATED: Register a test tenant (development/test scripts only)
    
    ⚠️ WARNING: This function is deprecated and should NOT be used in production code.
    It only works with in-memory storage which was removed in Priority 1.
    
    Use TenantService.create_tenant() or POST /admin/tenants instead.
    """
    logger.warning(
        "register_test_tenant() is DEPRECATED. "
        "Use TenantService.create_tenant() or POST /admin/tenants instead."
    )
    # This is now a no-op - all tenant data must come from database
    logger.info(f"register_test_tenant() called but ignored - use database instead")
