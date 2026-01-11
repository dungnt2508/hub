"""
Config Cache - Centralized caching for configuration data (patterns, keywords, etc.)

This is the ONLY place where config caching logic lives.
All steps use this cache instead of maintaining their own cache.
"""
import asyncio
import time
from typing import Optional, Dict, Any, List
from uuid import UUID

from .logger import logger


class ConfigCache:
    """
    Centralized configuration cache with tenant-aware invalidation.
    
    Features:
    - Per-tenant caching
    - Automatic refresh on timeout
    - Thread-safe (uses asyncio.Lock)
    """
    
    def __init__(self, refresh_interval: int = 300):
        """
        Initialize cache.
        
        Args:
            refresh_interval: Cache TTL in seconds (default 5 minutes)
        """
        self.refresh_interval = refresh_interval
        self._lock = asyncio.Lock()
        
        # Pattern rules cache
        self._pattern_rules_cache: Dict[str, Any] = {}
        self._pattern_rules_tenant: Optional[UUID] = None
        self._pattern_rules_time: float = 0
        
        # Keyword hints cache
        self._keyword_hints_cache: Dict[str, Any] = {}
        self._keyword_hints_tenant: Optional[UUID] = None
        self._keyword_hints_time: float = 0
    
    def _is_expired(self, cache_time: float) -> bool:
        """Check if cache entry has expired"""
        return (time.time() - cache_time) > self.refresh_interval
    
    def _is_tenant_changed(
        self,
        current_tenant: Optional[UUID],
        cached_tenant: Optional[UUID]
    ) -> bool:
        """Check if tenant has changed"""
        return current_tenant != cached_tenant
    
    async def get_pattern_rules(
        self,
        tenant_id: Optional[UUID],
        loader_func,  # async function to load from DB
    ) -> List[Dict[str, Any]]:
        """
        Get pattern rules with caching.
        
        Args:
            tenant_id: Tenant ID (None for global)
            loader_func: Async function(tenant_id) -> List[rules]
            
        Returns:
            List of pattern rule dictionaries
        """
        async with self._lock:
            # Check if we need to refresh
            cache_valid = (
                self._pattern_rules_cache
                and not self._is_tenant_changed(tenant_id, self._pattern_rules_tenant)
                and not self._is_expired(self._pattern_rules_time)
            )
            
            if cache_valid:
                logger.debug(
                    "Pattern rules cache hit",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
                )
                return self._pattern_rules_cache
            
            # Cache miss or expired - load from DB
            logger.info(
                "Loading pattern rules from DB",
                extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
            )
            
            try:
                rules = await loader_func(tenant_id)
                
                # Update cache
                self._pattern_rules_cache = rules
                self._pattern_rules_tenant = tenant_id
                self._pattern_rules_time = time.time()
                
                logger.info(
                    f"Loaded {len(rules)} pattern rules",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
                )
                
                return rules
            except Exception as e:
                logger.error(
                    f"Failed to load pattern rules: {e}",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"},
                    exc_info=True
                )
                raise
    
    async def get_keyword_hints(
        self,
        tenant_id: Optional[UUID],
        loader_func,  # async function to load from DB
    ) -> List[Dict[str, Any]]:
        """
        Get keyword hints with caching.
        
        Args:
            tenant_id: Tenant ID (None for global)
            loader_func: Async function(tenant_id) -> List[hints]
            
        Returns:
            List of keyword hint dictionaries
        """
        async with self._lock:
            # Check if we need to refresh
            cache_valid = (
                self._keyword_hints_cache
                and not self._is_tenant_changed(tenant_id, self._keyword_hints_tenant)
                and not self._is_expired(self._keyword_hints_time)
            )
            
            if cache_valid:
                logger.debug(
                    "Keyword hints cache hit",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
                )
                return self._keyword_hints_cache
            
            # Cache miss or expired - load from DB
            logger.info(
                "Loading keyword hints from DB",
                extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
            )
            
            try:
                hints = await loader_func(tenant_id)
                
                # Update cache
                self._keyword_hints_cache = hints
                self._keyword_hints_tenant = tenant_id
                self._keyword_hints_time = time.time()
                
                logger.info(
                    f"Loaded {len(hints)} keyword hints",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"}
                )
                
                return hints
            except Exception as e:
                logger.error(
                    f"Failed to load keyword hints: {e}",
                    extra={"tenant_id": str(tenant_id) if tenant_id else "global"},
                    exc_info=True
                )
                raise
    
    def invalidate_patterns(self, tenant_id: Optional[UUID] = None) -> None:
        """
        Invalidate pattern rules cache.
        
        Args:
            tenant_id: If provided, only invalidate for this tenant
        """
        if tenant_id is None or tenant_id == self._pattern_rules_tenant:
            logger.info("Invalidating pattern rules cache")
            self._pattern_rules_cache = {}
            self._pattern_rules_tenant = None
            self._pattern_rules_time = 0
    
    def invalidate_keywords(self, tenant_id: Optional[UUID] = None) -> None:
        """
        Invalidate keyword hints cache.
        
        Args:
            tenant_id: If provided, only invalidate for this tenant
        """
        if tenant_id is None or tenant_id == self._keyword_hints_tenant:
            logger.info("Invalidating keyword hints cache")
            self._keyword_hints_cache = {}
            self._keyword_hints_tenant = None
            self._keyword_hints_time = 0
    
    def clear(self) -> None:
        """Clear all caches"""
        logger.info("Clearing all config caches")
        self._pattern_rules_cache = {}
        self._pattern_rules_tenant = None
        self._pattern_rules_time = 0
        
        self._keyword_hints_cache = {}
        self._keyword_hints_tenant = None
        self._keyword_hints_time = 0


# Global cache instance
_global_config_cache: Optional[ConfigCache] = None


def init_config_cache(refresh_interval: int = 300) -> ConfigCache:
    """Initialize global config cache"""
    global _global_config_cache
    _global_config_cache = ConfigCache(refresh_interval)
    return _global_config_cache


def get_config_cache() -> ConfigCache:
    """Get global config cache instance"""
    global _global_config_cache
    if _global_config_cache is None:
        _global_config_cache = ConfigCache()
    return _global_config_cache
