"""
Tenant Config Cache - Hybrid caching for tenant configuration
Uses: In-Memory (L1) → Redis (L2) → Database (L3)
"""
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

from ..shared.logger import logger
from ..domain.tenant.tenant_service import TenantService
from ..infrastructure.database_client import database_client
from ..infrastructure.redis_client import redis_client
from ..schemas.multi_tenant_types import TenantConfig


class TenantConfigCache:
    """
    Multi-layer cache for tenant configuration.
    
    Cache Strategy:
    - L1: In-memory cache (60s TTL) - fastest, per-process
    - L2: Redis cache (5min TTL) - shared across instances
    - L3: Database - source of truth
    
    Cache Invalidation:
    - Automatic expiry (TTL-based)
    - Manual invalidation on tenant update
    """
    
    # Cache TTLs
    MEMORY_TTL = 60  # 1 minute - very fast, but per-process
    REDIS_TTL = 300  # 5 minutes - shared across instances
    
    # Cache keys
    REDIS_PREFIX = "tenant_config:"
    REDIS_BY_NAME_PREFIX = "tenant_config_by_name:"
    
    def __init__(self):
        # L1: In-memory cache {key: (config, expiry_time)}
        self._memory_cache: Dict[str, tuple] = {}
        # Cache by tenant_id and by name (site_id)
        self._memory_cache_by_id: Dict[str, tuple] = {}
        self._memory_cache_by_name: Dict[str, tuple] = {}
    
    def _redis_key_by_id(self, tenant_id: str) -> str:
        """Redis cache key by tenant ID"""
        return f"{self.REDIS_PREFIX}{tenant_id}"
    
    def _redis_key_by_name(self, name: str) -> str:
        """Redis cache key by tenant name (site_id)"""
        return f"{self.REDIS_BY_NAME_PREFIX}{name}"
    
    def _get_from_memory_by_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get from L1 cache by tenant ID"""
        if tenant_id in self._memory_cache_by_id:
            config, expiry = self._memory_cache_by_id[tenant_id]
            if time.time() < expiry:
                return config
            else:
                del self._memory_cache_by_id[tenant_id]
        return None
    
    def _get_from_memory_by_name(self, name: str) -> Optional[TenantConfig]:
        """Get from L1 cache by tenant name"""
        if name in self._memory_cache_by_name:
            config, expiry = self._memory_cache_by_name[name]
            if time.time() < expiry:
                return config
            else:
                del self._memory_cache_by_name[name]
        return None
    
    def _set_to_memory(self, config: TenantConfig):
        """Set to L1 cache (both by ID and name)"""
        expiry = time.time() + self.MEMORY_TTL
        self._memory_cache_by_id[config.id] = (config, expiry)
        self._memory_cache_by_name[config.name] = (config, expiry)
    
    async def _get_from_redis_by_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get from L2 cache (Redis) by tenant ID"""
        try:
            redis = redis_client.client
            cached = await redis.get(self._redis_key_by_id(tenant_id))
            if cached:
                data = json.loads(cached)
                return self._deserialize_config(data)
        except Exception as e:
            logger.debug(f"Redis cache read failed (by ID): {e}")
        return None
    
    async def _get_from_redis_by_name(self, name: str) -> Optional[TenantConfig]:
        """Get from L2 cache (Redis) by tenant name"""
        try:
            # Check if Redis is available
            if not hasattr(redis_client, '_redis') or redis_client._redis is None:
                return None
            
            redis = redis_client.client
            cached = await redis.get(self._redis_key_by_name(name))
            if cached:
                data = json.loads(cached)
                return self._deserialize_config(data)
        except Exception as e:
            # Redis unavailable or error - fallback to database
            logger.debug(f"Redis cache read failed (by name): {e}")
        return None
    
    async def _set_to_redis(self, config: TenantConfig):
        """Set to L2 cache (Redis)"""
        try:
            # Check if Redis is available
            if not hasattr(redis_client, '_redis') or redis_client._redis is None:
                return  # Redis not available, skip caching
            
            redis = redis_client.client
            data = self._serialize_config(config)
            
            # Cache by both ID and name
            await redis.setex(
                self._redis_key_by_id(config.id),
                self.REDIS_TTL,
                json.dumps(data, default=str)
            )
            await redis.setex(
                self._redis_key_by_name(config.name),
                self.REDIS_TTL,
                json.dumps(data, default=str)
            )
        except Exception as e:
            # Redis unavailable or error - continue without caching
            logger.debug(f"Redis cache write failed: {e}")
    
    async def _get_from_database_by_name(self, name: str) -> Optional[TenantConfig]:
        """Get from L3 cache (Database) by tenant name"""
        try:
            # Check if database pool is available
            try:
                pool = database_client.pool
            except Exception as e:
                logger.error(f"Database pool not available: {e}")
                return None
            
            async with pool.acquire() as conn:
                tenant_service = TenantService(conn)
                tenant_record = await tenant_service.get_tenant_by_site_id(name)
                
                if not tenant_record:
                    return None
                
                return TenantConfig(
                    id=str(tenant_record['id']),
                    name=tenant_record['name'],
                    api_key="",  # Not needed for embed init
                    web_embed_jwt_secret=tenant_record['web_embed_jwt_secret'],
                    web_embed_origins=tenant_record.get('web_embed_origins', []),
                    web_embed_enabled=tenant_record.get('web_embed_enabled', True),
                    web_embed_token_expiry_seconds=tenant_record.get('web_embed_token_expiry_seconds', 300),
                )
        except Exception as e:
            logger.error(f"Database lookup failed for tenant '{name}': {e}", exc_info=True)
            return None
    
    async def get_by_name(self, name: str) -> Optional[TenantConfig]:
        """
        Get tenant config by name (site_id) with multi-layer caching.
        
        Flow:
        1. Check L1 (in-memory) - fastest
        2. Check L2 (Redis) - shared cache
        3. Check L3 (Database) - source of truth
        4. Populate caches on miss
        """
        # L1: In-memory cache
        config = self._get_from_memory_by_name(name)
        if config:
            logger.debug(f"Tenant config cache HIT (L1): {name}")
            return config
        
        # L2: Redis cache
        config = await self._get_from_redis_by_name(name)
        if config:
            logger.debug(f"Tenant config cache HIT (L2): {name}")
            self._set_to_memory(config)  # Populate L1
            return config
        
        # L3: Database
        logger.debug(f"Tenant config cache MISS: {name}, fetching from database")
        config = await self._get_from_database_by_name(name)
        if config:
            # Populate both caches
            self._set_to_memory(config)
            await self._set_to_redis(config)
            return config
        
        return None
    
    async def get_by_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant config by tenant ID (UUID) with multi-layer caching.
        
        Flow:
        1. Check L1 (in-memory) - fastest
        2. Check L2 (Redis) - shared cache
        3. Check L3 (Database) - source of truth
        4. Populate caches on miss
        """
        # L1: In-memory cache
        config = self._get_from_memory_by_id(tenant_id)
        if config:
            logger.debug(f"Tenant config cache HIT (L1): {tenant_id}")
            return config
        
        # L2: Redis cache
        config = await self._get_from_redis_by_id(tenant_id)
        if config:
            logger.debug(f"Tenant config cache HIT (L2): {tenant_id}")
            self._set_to_memory(config)  # Populate L1
            return config
        
        # L3: Database
        logger.debug(f"Tenant config cache MISS: {tenant_id}, fetching from database")
        config = await self._get_from_database_by_id(tenant_id)
        if config:
            # Populate both caches
            self._set_to_memory(config)
            await self._set_to_redis(config)
            return config
        
        return None
    
    async def _get_from_database_by_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get from L3 cache (Database) by tenant ID (UUID)"""
        try:
            # Check if database pool is available
            try:
                pool = database_client.pool
            except Exception as e:
                logger.error(f"Database pool not available: {e}")
                return None
            
            async with pool.acquire() as conn:
                tenant_service = TenantService(conn)
                tenant_config = await tenant_service.get_tenant_config(tenant_id)
                
                if not tenant_config:
                    return None
                
                # Convert TenantConfig to match our format
                return TenantConfig(
                    id=tenant_config.id,
                    name=tenant_config.name,
                    api_key=tenant_config.api_key,
                    web_embed_jwt_secret=tenant_config.web_embed_jwt_secret,
                    web_embed_origins=tenant_config.web_embed_origins or [],
                    web_embed_enabled=tenant_config.web_embed_enabled,
                    web_embed_token_expiry_seconds=tenant_config.web_embed_token_expiry_seconds,
                )
        except Exception as e:
            logger.error(f"Database lookup failed for tenant ID '{tenant_id}': {e}", exc_info=True)
            return None
    
    async def invalidate(self, tenant_id: str = None, name: str = None):
        """
        Invalidate cache for tenant.
        
        Args:
            tenant_id: Tenant ID to invalidate
            name: Tenant name (site_id) to invalidate
        """
        # Invalidate L1 (memory)
        if tenant_id and tenant_id in self._memory_cache_by_id:
            del self._memory_cache_by_id[tenant_id]
        if name and name in self._memory_cache_by_name:
            del self._memory_cache_by_name[name]
        
        # Invalidate L2 (Redis)
        try:
            redis = redis_client.client
            if tenant_id:
                await redis.delete(self._redis_key_by_id(tenant_id))
            if name:
                await redis.delete(self._redis_key_by_name(name))
        except Exception as e:
            logger.warning(f"Redis cache invalidation failed: {e}")
    
    def _serialize_config(self, config: TenantConfig) -> Dict[str, Any]:
        """Serialize TenantConfig to dict"""
        return {
            "id": config.id,
            "name": config.name,
            "api_key": config.api_key,
            "web_embed_jwt_secret": config.web_embed_jwt_secret,
            "web_embed_origins": config.web_embed_origins or [],
            "web_embed_enabled": config.web_embed_enabled,
            "web_embed_token_expiry_seconds": config.web_embed_token_expiry_seconds,
        }
    
    def _deserialize_config(self, data: Dict[str, Any]) -> TenantConfig:
        """Deserialize dict to TenantConfig"""
        return TenantConfig(
            id=data["id"],
            name=data["name"],
            api_key=data.get("api_key", ""),
            web_embed_jwt_secret=data["web_embed_jwt_secret"],
            web_embed_origins=data.get("web_embed_origins", []),
            web_embed_enabled=data.get("web_embed_enabled", True),
            web_embed_token_expiry_seconds=data.get("web_embed_token_expiry_seconds", 300),
        )


# Global singleton instance
tenant_config_cache = TenantConfigCache()
