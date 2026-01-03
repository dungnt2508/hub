"""
Rate limiting service for multi-tenant bot service.
Redis-based rate limiting per tenant + user_key.
"""

from typing import Optional
from datetime import datetime, timedelta
import hashlib

from ..infrastructure.redis_client import redis_client
from ..shared.auth_config import get_rate_limit_config
from ..shared.logger import logger


class RateLimitService:
    """
    Rate limiting service.
    
    Key pattern: rate_limit:<tenant_id>:<user_key>:<window>
    
    Windows:
    - per_minute: 1-minute window
    - per_hour: hourly window
    - per_day: daily window
    """
    
    @staticmethod
    def _get_window_key(tenant_id: str, user_key: str, window: str) -> str:
        """Generate Redis key for rate limit window"""
        if window == "minute":
            timestamp = int(datetime.now().timestamp() / 60) * 60  # 1-minute bucket
        elif window == "hour":
            timestamp = int(datetime.now().timestamp() / 3600) * 3600  # hourly bucket
        elif window == "day":
            timestamp = int(datetime.now().timestamp() / 86400) * 86400  # daily bucket
        else:
            raise ValueError(f"Invalid window: {window}")
        
        return f"rate_limit:{tenant_id}:{user_key}:{window}:{timestamp}"
    
    @staticmethod
    async def check_rate_limit(
        tenant_id: str,
        user_key: str
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limits.
        
        Args:
            tenant_id: Tenant ID
            user_key: User key
        
        Returns:
            (is_allowed, status_dict)
            - is_allowed: True if request allowed
            - status_dict: {
                "allowed": bool,
                "limit_per_minute": int,
                "current_minute": int,
                "limit_per_hour": int,
                "current_hour": int,
                "retry_after": int (seconds)
              }
        """
        try:
            # Get rate limit config
            config = get_rate_limit_config(tenant_id)
            if not config:
                logger.warning(f"Rate limit config not found for tenant: {tenant_id}")
                return True, {"allowed": True, "reason": "no_config"}
            
            # Check each window
            windows = {
                "minute": config.get("per_minute", 20),
                "hour": config.get("per_hour", 1000),
                "day": config.get("per_day", 10000),
            }
            
            counts = {}
            for window, limit in windows.items():
                key = RateLimitService._get_window_key(tenant_id, user_key, window)
                count = await redis_client.client.incr(key)
                
                # Set expiration on first increment
                if count == 1:
                    if window == "minute":
                        ttl = 60
                    elif window == "hour":
                        ttl = 3600
                    else:  # day
                        ttl = 86400
                    
                    await redis_client.client.expire(key, ttl)
                
                counts[window] = count
                
                # Check if exceeded
                if count > limit:
                    logger.warning(
                        f"Rate limit exceeded - "
                        f"tenant: {tenant_id}, user: {user_key}, "
                        f"window: {window}, limit: {limit}, current: {count}"
                    )
                    
                    return False, {
                        "allowed": False,
                        "exceeded_window": window,
                        f"limit_per_{window}": limit,
                        f"current_{window}": count,
                        "retry_after": RateLimitService._get_retry_after(window),
                    }
            
            # All limits OK
            return True, {
                "allowed": True,
                "limit_per_minute": config["per_minute"],
                "current_minute": counts["minute"],
                "limit_per_hour": config["per_hour"],
                "current_hour": counts["hour"],
                "limit_per_day": config["per_day"],
                "current_day": counts["day"],
            }
        
        except Exception as e:
            logger.error(
                f"Error checking rate limit for {tenant_id}: {e}",
                exc_info=True
            )
            # On error, allow request (fail open)
            return True, {"allowed": True, "reason": "error_checking_rate_limit"}
    
    @staticmethod
    def _get_retry_after(window: str) -> int:
        """Get retry-after seconds based on window"""
        if window == "minute":
            return 60
        elif window == "hour":
            return 3600
        else:  # day
            return 86400
        return 60
    
    @staticmethod
    async def reset_rate_limit(tenant_id: str, user_key: str = None):
        """
        Reset rate limits for a tenant or specific user.
        
        Args:
            tenant_id: Tenant ID
            user_key: If provided, reset only for this user. Otherwise all users.
        """
        try:
            if user_key:
                # Reset specific user
                for window in ["minute", "hour", "day"]:
                    key = RateLimitService._get_window_key(tenant_id, user_key, window)
                    await redis_client.client.delete(key)
                logger.info(
                    f"Reset rate limit for tenant {tenant_id}, user {user_key}"
                )
            else:
                # Reset entire tenant - use SCAN to find all keys
                pattern = f"rate_limit:{tenant_id}:*"
                cursor = 0
                while True:
                    cursor, keys = await redis_client.client.scan(cursor, match=pattern, count=100)
                    if keys:
                        await redis_client.client.delete(*keys)
                    if cursor == 0:
                        break
                logger.info(f"Reset rate limit for tenant {tenant_id}")
        
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}", exc_info=True)
    
    @staticmethod
    async def get_usage_stats(tenant_id: str, user_key: str) -> dict:
        """Get current usage stats for tenant/user"""
        try:
            config = get_rate_limit_config(tenant_id)
            if not config:
                return {}
            
            stats = {}
            for window in ["minute", "hour", "day"]:
                key = RateLimitService._get_window_key(tenant_id, user_key, window)
                count = await redis_client.client.get(key)
                stats[f"current_{window}"] = int(count) if count else 0
                stats[f"limit_{window}"] = config.get(f"per_{window}", 0)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}", exc_info=True)
            return {}


# ============================================================================
# MIDDLEWARE INTEGRATION
# ============================================================================

async def rate_limit_middleware(request, call_next):
    """
    Rate limit middleware for FastAPI.
    Check rate limits before processing request.
    """
    try:
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get user context from state
        if not hasattr(request.state, "user_context"):
            return await call_next(request)
        
        context = request.state.user_context
        
        # Check rate limit
        allowed, status = await RateLimitService.check_rate_limit(
            context.tenant_id,
            context.user_key
        )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded: {status}")
            return {
                "error": True,
                "message": "Rate limit exceeded",
                "status_code": 429,
                "details": status,
            }
        
        # Continue to next middleware/handler
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit-Minute"] = str(
            status.get("limit_per_minute", 0)
        )
        response.headers["X-RateLimit-Current-Minute"] = str(
            status.get("current_minute", 0)
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in rate limit middleware: {e}", exc_info=True)
        # Fail open - allow request
        return await call_next(request)

