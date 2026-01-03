"""
Config Loader Service - Load configs from DB with Redis cache
"""
import json
import time
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..shared.logger import logger
from .config_repository import config_repository
from .redis_client import redis_client


class ConfigLoader:
    """
    Config loader service with Redis caching.
    
    Loads configs from database and caches in Redis.
    Cache invalidation on config changes.
    """
    
    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "config:"
    
    def __init__(self):
        self.repository = config_repository
        # In-memory cache with TTL for fast access
        self._memory_cache: Dict[str, tuple] = {}  # {key: (data, expiry_time)}
        self._memory_cache_ttl = 60  # 1 minute
    
    def _cache_key(self, config_type: str, tenant_id: Optional[UUID] = None, **filters) -> str:
        """Generate cache key"""
        key_parts = [self.CACHE_PREFIX, config_type]
        if tenant_id:
            key_parts.append(str(tenant_id))
        else:
            key_parts.append("global")
        
        # Add filter keys
        if filters:
            filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
            if filter_str:
                key_parts.append(filter_str)
        
        return ":".join(key_parts)
    
    async def _get_from_redis(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get config from Redis cache"""
        try:
            redis = redis_client.client
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
        return None
    
    async def _set_to_redis(self, cache_key: str, data: List[Dict[str, Any]]):
        """Set config to Redis cache"""
        try:
            redis = redis_client.client
            await redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")
    
    def _get_from_memory(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get config from in-memory cache"""
        if cache_key in self._memory_cache:
            data, expiry = self._memory_cache[cache_key]
            if time.time() < expiry:
                return data
            else:
                # Expired, remove
                del self._memory_cache[cache_key]
        return None
    
    def _set_to_memory(self, cache_key: str, data: List[Dict[str, Any]]):
        """Set config to in-memory cache"""
        expiry = time.time() + self._memory_cache_ttl
        self._memory_cache[cache_key] = (data, expiry)
    
    async def get_pattern_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get pattern rules with caching"""
        cache_key = self._cache_key("pattern_rules", tenant_id, enabled=enabled_only)
        
        # Try memory cache first
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        # Try Redis cache
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        # Load from DB
        logger.debug(f"Loading pattern rules from DB (tenant_id={tenant_id})")
        rules = await self.repository.get_pattern_rules(tenant_id, enabled_only)
        
        # Cache results
        self._set_to_memory(cache_key, rules)
        await self._set_to_redis(cache_key, rules)
        
        return rules
    
    async def get_keyword_hints(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get keyword hints with caching"""
        cache_key = self._cache_key("keyword_hints", tenant_id, enabled=enabled_only)
        
        # Try memory cache
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        # Try Redis cache
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        # Load from DB
        logger.debug(f"Loading keyword hints from DB (tenant_id={tenant_id})")
        hints = await self.repository.get_keyword_hints(tenant_id, enabled_only)
        
        # Cache results
        self._set_to_memory(cache_key, hints)
        await self._set_to_redis(cache_key, hints)
        
        return hints
    
    async def get_routing_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get routing rules with caching"""
        cache_key = self._cache_key("routing_rules", tenant_id, enabled=enabled_only)
        
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        logger.debug(f"Loading routing rules from DB (tenant_id={tenant_id})")
        rules = await self.repository.get_routing_rules(tenant_id, enabled_only)
        
        self._set_to_memory(cache_key, rules)
        await self._set_to_redis(cache_key, rules)
        
        return rules
    
    async def get_prompt_templates(
        self,
        tenant_id: Optional[UUID] = None,
        template_type: Optional[str] = None,
        domain: Optional[str] = None,
        agent: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get prompt templates with caching"""
        cache_key = self._cache_key(
            "prompt_templates",
            tenant_id,
            template_type=template_type,
            domain=domain,
            agent=agent,
            active_only=active_only
        )
        
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        logger.debug(f"Loading prompt templates from DB (tenant_id={tenant_id}, type={template_type})")
        templates = await self.repository.get_prompt_templates(
            tenant_id, template_type, domain, agent, active_only
        )
        
        self._set_to_memory(cache_key, templates)
        await self._set_to_redis(cache_key, templates)
        
        return templates
    
    async def get_tool_permissions(
        self,
        tenant_id: Optional[UUID] = None,
        agent_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get tool permissions with caching"""
        cache_key = self._cache_key("tool_permissions", tenant_id, agent_name=agent_name, enabled=enabled_only)
        
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        logger.debug(f"Loading tool permissions from DB (tenant_id={tenant_id}, agent={agent_name})")
        permissions = await self.repository.get_tool_permissions(tenant_id, agent_name, enabled_only)
        
        self._set_to_memory(cache_key, permissions)
        await self._set_to_redis(cache_key, permissions)
        
        return permissions
    
    async def get_guardrails(
        self,
        tenant_id: Optional[UUID] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get guardrails with caching"""
        cache_key = self._cache_key("guardrails", tenant_id, rule_type=rule_type, enabled=enabled_only)
        
        cached = self._get_from_memory(cache_key)
        if cached is not None:
            return cached
        
        cached = await self._get_from_redis(cache_key)
        if cached is not None:
            self._set_to_memory(cache_key, cached)
            return cached
        
        logger.debug(f"Loading guardrails from DB (tenant_id={tenant_id}, type={rule_type})")
        guardrails = await self.repository.get_guardrails(tenant_id, rule_type, enabled_only)
        
        self._set_to_memory(cache_key, guardrails)
        await self._set_to_redis(cache_key, guardrails)
        
        return guardrails
    
    async def invalidate_cache(
        self,
        config_type: str,
        tenant_id: Optional[UUID] = None,
        **filters
    ):
        """Invalidate cache for specific config type"""
        try:
            # Invalidate memory cache
            pattern = self._cache_key(config_type, tenant_id, **filters)
            keys_to_delete = [
                key for key in self._memory_cache.keys()
                if key.startswith(pattern)
            ]
            for key in keys_to_delete:
                del self._memory_cache[key]
            
            # Invalidate Redis cache
            if tenant_id:
                patterns = [
                    f"{self.CACHE_PREFIX}{config_type}:{tenant_id}:*",
                    f"{self.CACHE_PREFIX}{config_type}:global:*",
                ]
            else:
                patterns = [f"{self.CACHE_PREFIX}{config_type}:*"]
            
            redis = redis_client.client
            for pattern in patterns:
                # Redis SCAN and delete matching keys
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await redis.delete(*keys)
                    if cursor == 0:
                        break
            
            logger.info(f"Invalidated cache for {config_type} (tenant_id={tenant_id})")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)
    
    async def invalidate_all_cache(self):
        """Invalidate all config caches"""
        self._memory_cache.clear()
        
        try:
            redis = redis_client.client
            pattern = f"{self.CACHE_PREFIX}*"
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Invalidated all config caches")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)


# Global config loader instance
config_loader = ConfigLoader()

