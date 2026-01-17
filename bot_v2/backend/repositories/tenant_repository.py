"""Tenant repository"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.domain.tenant import Tenant, TenantSecret, Channel
from backend.repositories.base_repository import BaseRepository


class TenantRepository:
    """Repository for tenant data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        from sqlalchemy import text
        
        # Using raw SQL for now since we don't have ORM models
        stmt = text("""
            SELECT id, name, status, plan, settings_version, created_at, updated_at
            FROM tenants
            WHERE id = :tenant_id
        """)
        result = await self.session.execute(stmt, {"tenant_id": tenant_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return Tenant(
            id=row[0],
            name=row[1],
            status=row[2],
            plan=row[3],
            settings_version=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
    
    async def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Get tenant by name"""
        from sqlalchemy import text
        
        stmt = text("""
            SELECT id, name, status, plan, settings_version, created_at, updated_at
            FROM tenants
            WHERE name = :name
        """)
        result = await self.session.execute(stmt, {"name": name})
        row = result.fetchone()
        
        if not row:
            return None
        
        return Tenant(
            id=row[0],
            name=row[1],
            status=row[2],
            plan=row[3],
            settings_version=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> list[Tenant]:
        """List all tenants"""
        from sqlalchemy import text
        
        stmt = text("""
            SELECT id, name, status, plan, settings_version, created_at, updated_at
            FROM tenants
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.session.execute(stmt, {"limit": limit, "offset": offset})
        rows = result.fetchall()
        
        return [
            Tenant(
                id=row[0],
                name=row[1],
                status=row[2],
                plan=row[3],
                settings_version=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]
    
    async def get_channel(
        self, 
        channel_id: UUID, 
        tenant_id: UUID
    ) -> Optional[Channel]:
        """Get channel by ID with tenant isolation"""
        from sqlalchemy import text
        
        stmt = text("""
            SELECT id, tenant_id, type, enabled, config_json, created_at, updated_at
            FROM channels
            WHERE id = :channel_id AND tenant_id = :tenant_id
        """)
        result = await self.session.execute(
            stmt, 
            {"channel_id": channel_id, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return Channel(
            id=row[0],
            tenant_id=row[1],
            type=row[2],
            enabled=row[3],
            config_json=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
    
    async def list_channels(self, tenant_id: UUID) -> list[Channel]:
        """List channels for tenant"""
        from sqlalchemy import text
        
        stmt = text("""
            SELECT id, tenant_id, type, enabled, config_json, created_at, updated_at
            FROM channels
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """)
        result = await self.session.execute(stmt, {"tenant_id": tenant_id})
        rows = result.fetchall()
        
        return [
            Channel(
                id=row[0],
                tenant_id=row[1],
                type=row[2],
                enabled=row[3],
                config_json=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]
