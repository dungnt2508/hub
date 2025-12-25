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

from backend.schemas.multi_tenant_types import TenantConfig, PlanType
from backend.shared.logger import logger
from backend.shared.exceptions import (
    TenantNotFoundError,
    TenantAlreadyExistsError,
    ValidationError,
)
from backend.domain.tenant.audit_service import TenantAuditService


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
        self.audit_service = TenantAuditService(db_connection)
        logger.info("TenantService initialized")
    
    async def create_tenant(
        self,
        name: str,
        site_id: str,
        web_embed_origins: List[str],
        plan: str = PlanType.BASIC,
        telegram_enabled: bool = False,
        teams_enabled: bool = False,
    ) -> Dict[str, Any]:
        """
        Create new tenant with configuration.
        
        Args:
            name: Tenant name (e.g., "GSNAKE Catalog")
            site_id: Site identifier (e.g., "catalog-001")
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
            TenantAlreadyExistsError: If site_id already exists
            ValidationError: If inputs invalid
        """
        try:
            # Validate inputs
            if not name or not name.strip():
                raise ValidationError("name is required and non-empty")
            
            if not site_id or not site_id.strip():
                raise ValidationError("site_id is required and non-empty")
            
            if not web_embed_origins or len(web_embed_origins) == 0:
                raise ValidationError("at least one origin required")
            
            if plan not in [PlanType.BASIC, PlanType.PROFESSIONAL, PlanType.ENTERPRISE]:
                raise ValidationError(f"invalid plan: {plan}")
            
            # Check if site_id already exists
            existing = await self.get_tenant_by_site_id(site_id)
            if existing:
                raise TenantAlreadyExistsError(f"site_id already exists: {site_id}")
            
            # Generate credentials
            tenant_id = str(uuid.uuid4())
            api_key = f"api_{site_id}_{secrets.token_urlsafe(16)}"
            jwt_secret = secrets.token_urlsafe(32)  # Min 32 chars
            
            # Prepare SQL
            query = """
            INSERT INTO tenants (
                id, name, api_key, plan,
                web_embed_enabled, web_embed_origins, web_embed_jwt_secret,
                web_embed_token_expiry_seconds,
                telegram_enabled, teams_enabled,
                is_active,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10, $11,
                $12, $13
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
                # Status
                True,  # is_active - new tenants are active by default
                # Timestamps
                datetime.now(),
                datetime.now(),
            )
            
            # Execute tenant creation
            result = await self.db.fetchrow(query, *values)
            
            # Priority 1 Fix: Create site_id mapping in tenant_sites table
            import uuid as uuid_lib
            site_mapping_id = str(uuid_lib.uuid4())
            site_mapping_query = """
            INSERT INTO tenant_sites (id, tenant_id, site_id, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """
            await self.db.execute(
                site_mapping_query,
                site_mapping_id,
                tenant_id,
                site_id,
                True,  # is_active
                datetime.now(),
                datetime.now(),
            )
            
            logger.info(
                f"✅ Tenant created: {tenant_id} (site_id: {site_id}, plan: {plan})"
            )
            
            # Priority 2: Audit log tenant creation
            await self.audit_service.log_operation(
                tenant_id=tenant_id,
                operation="create",
                resource_type="tenant",
                resource_id=tenant_id,
                channel="api",
                metadata={
                    "site_id": site_id,
                    "name": name,
                    "plan": plan,
                    "telegram_enabled": telegram_enabled,
                    "teams_enabled": teams_enabled,
                }
            )
            
            # Convert UUID to string for JSON serialization
            tenant_id_str = str(result['id']) if result['id'] else tenant_id
            
            return {
                "success": True,
                "data": {
                    "tenant_id": tenant_id_str,
                    "site_id": site_id,
                    "name": result['name'],
                    "api_key": result['api_key'],
                    "jwt_secret": jwt_secret,
                    "plan": result['plan'],
                    "created_at": result['created_at'].isoformat() if result['created_at'] else None,
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
        
        Priority 1 Fix: Query tenant_sites mapping table to resolve tenant_id from site_id.
        
        Args:
            site_id: Site identifier
        
        Returns:
            Tenant record with tenant_id, or None if not found
        """
        try:
            # First, try to resolve via tenant_sites mapping table
            query_site_mapping = """
            SELECT ts.tenant_id, ts.is_active
            FROM tenant_sites ts
            WHERE ts.site_id = $1 AND ts.is_active = true
            LIMIT 1
            """
            
            site_row = await self.db.fetchrow(query_site_mapping, site_id)
            
            if not site_row:
                logger.warning(f"Site ID not found in tenant_sites mapping: {site_id}")
                return None
            
            tenant_id = str(site_row['tenant_id'])
            
            # Get full tenant config
            query_tenant = """
            SELECT id, name, web_embed_origins, web_embed_jwt_secret, 
                   web_embed_enabled, is_active, plan
            FROM tenants
            WHERE id = $1 AND is_active = true
            """
            
            tenant_row = await self.db.fetchrow(query_tenant, tenant_id)
            if not tenant_row:
                logger.warning(f"Tenant not found or inactive: {tenant_id}")
                return None
            
            return dict(tenant_row)
        
        except Exception as e:
            logger.error(f"Error fetching tenant by site_id: {e}", exc_info=True)
            return None
    
    async def resolve_tenant_id_from_site_id(self, site_id: str) -> Optional[str]:
        """
        Resolve tenant_id from site_id via database lookup.
        
        Priority 1 Fix: Proper tenant resolution from site_id.
        
        Args:
            site_id: Site identifier
        
        Returns:
            Tenant UUID if found and active, None otherwise
        """
        try:
            tenant = await self.get_tenant_by_site_id(site_id)
            if tenant:
                return str(tenant['id'])
            return None
        except Exception as e:
            logger.error(f"Error resolving tenant_id from site_id: {e}", exc_info=True)
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
            
            # Priority 2: Audit log tenant update
            await self.audit_service.log_operation(
                tenant_id=tenant_id,
                operation="update",
                resource_type="tenant",
                resource_id=tenant_id,
                channel="api",
                metadata={
                    "updated_fields": list(updates.keys()),
                }
            )
            
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
    
    async def resolve_tenant_id_from_telegram_bot_token(self, bot_token: str) -> Optional[str]:
        """
        Resolve tenant_id from Telegram bot token.
        
        Task 3.3: Map bot token to tenant_id from database.
        
        Args:
            bot_token: Telegram bot token
        
        Returns:
            Tenant UUID if found and active, None otherwise
        """
        try:
            query = """
            SELECT id, is_active, telegram_enabled
            FROM tenants
            WHERE telegram_bot_token = $1 AND is_active = true AND telegram_enabled = true
            LIMIT 1
            """
            
            row = await self.db.fetchrow(query, bot_token)
            
            if not row:
                logger.warning(f"Telegram bot token not found or tenant inactive: {bot_token[:8]}...")
                return None
            
            tenant_id = str(row['id'])
            logger.debug(f"Resolved tenant_id from Telegram bot token: {tenant_id}")
            return tenant_id
        
        except Exception as e:
            logger.error(f"Error resolving tenant_id from Telegram bot token: {e}", exc_info=True)
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

