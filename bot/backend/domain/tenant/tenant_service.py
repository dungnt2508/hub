"""
Tenant Service - CRUD operations for multi-tenant management
Phase 1: Foundation - Tenant registration, configuration, activation
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import secrets
import hashlib

from ...schemas.multi_tenant_types import TenantConfig, PlanType
from ...shared.logger import logger
from ...shared.exceptions import (
    TenantNotFoundError,
    TenantAlreadyExistsError,
    ValidationError,
)


class TenantService:
    """
    Tenant Service - manages multi-tenant configuration and lifecycle.
    
    Responsibilities:
    - Create new tenants
    - Retrieve tenant configuration
    - Update tenant settings
    - Manage API keys
    - Rate limit configuration
    """
    
    def __init__(self, db_connection):
        """
        Initialize tenant service with database connection.
        
        Args:
            db_connection: PostgreSQL connection pool
        """
        self.db = db_connection
        logger.info("TenantService initialized")
    
    async def create_tenant(
        self,
        name: str,
        site_id: Optional[str] = None,
        web_embed_origins: List[str] = None,
        plan: str = PlanType.BASIC,
        telegram_enabled: bool = False,
        teams_enabled: bool = False,
    ) -> Dict[str, Any]:
        """
        Create new tenant with configuration.
        
        Args:
            name: Tenant name (e.g., "GSNAKE Catalog") - must be unique
            site_id: Site identifier (optional, will be auto-generated from UUID if not provided)
            web_embed_origins: List of allowed origins for web embed
            plan: Rate limit plan (basic/professional/enterprise)
            telegram_enabled: Enable Telegram bot
            teams_enabled: Enable Teams bot
        
        Returns:
            {
                "tenant_id": "uuid",
                "api_key": "secure_key",
                "jwt_secret": "secret_for_web_embed",
                "created_at": "2025-12-20T..."
            }
        
        Raises:
            TenantAlreadyExistsError: If tenant name already exists
            ValidationError: If inputs invalid
        """
        try:
            # Validate inputs
            name = name.strip() if name else ""
            if not name:
                raise ValidationError("name is required and non-empty")
            
            if len(name) < 3:
                raise ValidationError("name must be at least 3 characters")
            
            if len(name) > 255:
                raise ValidationError("name must not exceed 255 characters")
            
            # Validate name format (alphanumeric, spaces, hyphens, underscores)
            import re
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
                raise ValidationError("name can only contain letters, numbers, spaces, hyphens, and underscores")
            
            if not web_embed_origins or len(web_embed_origins) == 0:
                raise ValidationError("at least one origin required")
            
            if plan not in [PlanType.BASIC, PlanType.PROFESSIONAL, PlanType.ENTERPRISE]:
                raise ValidationError(f"invalid plan: {plan}")
            
            # Check if tenant name already exists (name must be unique)
            existing = await self.get_tenant_by_site_id(name)  # Using name as site_id lookup
            if existing:
                raise TenantAlreadyExistsError(f"tenant name already exists: {name}")
            
            # Generate credentials
            tenant_id = str(uuid.uuid4())
            # Auto-generate site_id from UUID if not provided
            if not site_id:
                site_id = f"tenant-{tenant_id[:8]}"
            
            api_key = f"api_{site_id}_{secrets.token_urlsafe(16)}"
            jwt_secret = secrets.token_urlsafe(32)  # Min 32 chars
            
            # Prepare SQL
            query = """
            INSERT INTO tenants (
                id, name, api_key, plan,
                web_embed_enabled, web_embed_origins, web_embed_jwt_secret,
                web_embed_token_expiry_seconds,
                telegram_enabled, teams_enabled,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10,
                $11, $12
            )
            RETURNING id, name, api_key, plan, created_at;
            """
            
            values = (
                tenant_id,
                name,
                api_key,
                plan,
                # Web embed
                True,
                web_embed_origins,  # PostgreSQL array
                jwt_secret,
                300,  # 5 minutes
                # Channels
                telegram_enabled,
                teams_enabled,
                # Timestamps
                datetime.now(),
                datetime.now(),
            )
            
            # Execute
            result = await self.db.fetchrow(query, *values)
            
            logger.info(
                f"✅ Tenant created: {tenant_id} (site_id: {site_id}, plan: {plan})"
            )
            
            return {
                "success": True,
                "data": {
                    "tenant_id": result['id'],
                    "site_id": site_id,
                    "name": result['name'],
                    "api_key": result['api_key'],
                    "jwt_secret": jwt_secret,
                    "plan": result['plan'],
                    "created_at": result['created_at'].isoformat(),
                }
            }
        
        except (TenantAlreadyExistsError, ValidationError) as e:
            logger.warning(f"Create tenant failed: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error creating tenant: {e}", exc_info=True)
            raise Exception(f"Failed to create tenant: {e}")
    
    async def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant configuration by tenant_id.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            TenantConfig object or None
        """
        try:
            query = "SELECT * FROM tenants WHERE id = $1"
            row = await self.db.fetchrow(query, tenant_id)
            
            if not row:
                logger.warning(f"Tenant not found: {tenant_id}")
                return None
            
            config = TenantConfig(
                id=str(row['id']),
                name=row['name'],
                api_key=row['api_key'],
                webhook_secret=row['webhook_secret'],
                plan=row['plan'],
                rate_limit_per_hour=row['rate_limit_per_hour'],
                rate_limit_per_day=row['rate_limit_per_day'],
                # Web embed
                web_embed_enabled=row['web_embed_enabled'],
                web_embed_origins=row['web_embed_origins'] or [],
                web_embed_jwt_secret=row['web_embed_jwt_secret'],
                web_embed_token_expiry_seconds=row['web_embed_token_expiry_seconds'],
                # Telegram
                telegram_enabled=row['telegram_enabled'],
                telegram_bot_token=row['telegram_bot_token'],
                # Teams
                teams_enabled=row['teams_enabled'],
                teams_app_id=row['teams_app_id'],
                teams_app_password=row['teams_app_password'],
                # Timestamps
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
            
            return config
        
        except Exception as e:
            logger.error(f"Error fetching tenant config: {e}", exc_info=True)
            return None
    
    async def get_tenant_by_site_id(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant by site_id (for embed initialization).
        
        Args:
            site_id: Site identifier (currently matches with tenant name)
        
        Returns:
            Tenant record or None
        """
        try:
            # TODO: Implement site_id → tenant_id mapping table
            # For now: assume site_id matches tenant name
            # In production: need a separate site_id column or mapping table
            query = """
            SELECT id, name, web_embed_enabled, web_embed_origins, web_embed_jwt_secret, web_embed_token_expiry_seconds
            FROM tenants
            WHERE name = $1
            LIMIT 1
            """
            
            row = await self.db.fetchrow(query, site_id)
            return dict(row) if row else None
        
        except Exception as e:
            logger.error(f"Error fetching tenant by site_id: {e}", exc_info=True)
            return None
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update tenant configuration.
        
        Args:
            tenant_id: Tenant UUID
            updates: Dict of fields to update
        
        Returns:
            True if successful
        """
        try:
            # Build dynamic UPDATE query
            allowed_fields = {
                'name', 'plan', 'rate_limit_per_hour', 'rate_limit_per_day',
                'web_embed_enabled', 'web_embed_origins', 'web_embed_token_expiry_seconds',
                'telegram_enabled', 'teams_enabled',
            }
            
            set_clause_parts = []
            values = []
            param_num = 1
            
            for field, value in updates.items():
                if field not in allowed_fields:
                    logger.warning(f"Skipping disallowed field: {field}")
                    continue
                
                set_clause_parts.append(f"{field} = ${param_num}")
                values.append(value)
                param_num += 1
            
            if not set_clause_parts:
                logger.warning(f"No valid fields to update for tenant {tenant_id}")
                return False
            
            # Add updated_at and tenant_id
            set_clause_parts.append(f"updated_at = ${param_num}")
            values.append(datetime.now())
            param_num += 1
            
            values.append(tenant_id)
            
            query = f"""
            UPDATE tenants
            SET {', '.join(set_clause_parts)}
            WHERE id = ${param_num}
            """
            
            result = await self.db.execute(query, *values)
            
            if result == "UPDATE 0":
                logger.warning(f"Tenant not found: {tenant_id}")
                return False
            
            logger.info(f"✅ Tenant updated: {tenant_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating tenant: {e}", exc_info=True)
            return False
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """
        Activate a tenant (if deactivated).
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            True if successful
        """
        # TODO: Implement soft delete / activation flag
        logger.info(f"Activating tenant: {tenant_id}")
        return True
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant (soft delete).
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            True if successful
        """
        # TODO: Implement soft delete / deactivation flag
        logger.info(f"Deactivating tenant: {tenant_id}")
        return True
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all tenants (admin only).
        
        Args:
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of tenant records
        """
        try:
            query = """
            SELECT id, name, plan, created_at
            FROM tenants
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """
            
            rows = await self.db.fetch(query, limit, offset)
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error listing tenants: {e}", exc_info=True)
            return []
    
    async def create_api_key(
        self,
        tenant_id: str,
        name: str = None,
    ) -> Optional[str]:
        """
        Create new API key for tenant (for service-to-service auth).
        
        Args:
            tenant_id: Tenant UUID
            name: Optional key name (for identification)
        
        Returns:
            Generated API key or None
        """
        try:
            key_id = str(uuid.uuid4())
            key = f"sk_{tenant_id}_{secrets.token_urlsafe(32)}"
            
            query = """
            INSERT INTO tenant_api_keys (id, tenant_id, key, name)
            VALUES ($1, $2, $3, $4)
            RETURNING key;
            """
            
            result = await self.db.fetchrow(
                query,
                key_id,
                tenant_id,
                key,
                name or f"key-{key_id[:8]}"
            )
            
            logger.info(f"✅ API key created for tenant: {tenant_id}")
            return result['key'] if result else None
        
        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            return None
    
    async def verify_api_key(self, api_key: str) -> Optional[str]:
        """
        Verify API key and return tenant_id.
        
        Args:
            api_key: API key to verify
        
        Returns:
            Tenant ID if valid, None otherwise
        """
        try:
            query = """
            SELECT tenant_id, revoked_at
            FROM tenant_api_keys
            WHERE key = $1
            """
            
            result = await self.db.fetchrow(query, api_key)
            
            if not result:
                logger.warning(f"API key not found")
                return None
            
            if result['revoked_at']:
                logger.warning(f"API key revoked")
                return None
            
            # Update last_used_at
            update_query = """
            UPDATE tenant_api_keys
            SET last_used_at = $1
            WHERE key = $2
            """
            await self.db.execute(update_query, datetime.now(), api_key)
            
            return str(result['tenant_id'])
        
        except Exception as e:
            logger.error(f"Error verifying API key: {e}", exc_info=True)
            return None


# ============================================================================
# REPOSITORY PATTERN (Optional: for testing, can use service directly)
# ============================================================================

class TenantRepository:
    """
    Repository for tenant data access (optional abstraction).
    Use this if you want to decouple service from database.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def find_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find tenant by ID"""
        query = "SELECT * FROM tenants WHERE id = $1"
        return await self.db.fetchrow(query, tenant_id)
    
    async def find_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Find tenant by API key"""
        query = "SELECT * FROM tenants WHERE api_key = $1"
        return await self.db.fetchrow(query, api_key)
    
    async def save(self, tenant: Dict[str, Any]) -> bool:
        """Save/insert tenant"""
        query = """
        INSERT INTO tenants (id, name, api_key, plan, ...)
        VALUES (...)
        """
        # TODO: Implement
        pass

