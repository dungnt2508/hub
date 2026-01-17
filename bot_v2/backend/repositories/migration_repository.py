"""Migration repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.domain.migration import MigrationJob, MigrationVersion


class MigrationRepository:
    """Repository for migration data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_migration_job(
        self,
        job_id: UUID,
        tenant_id: UUID
    ) -> Optional[MigrationJob]:
        """Get migration job by ID"""
        stmt = text("""
            SELECT id, tenant_id, source_type, status, created_at, updated_at
            FROM migration_jobs
            WHERE id = :job_id AND tenant_id = :tenant_id
        """)
        result = await self.session.execute(
            stmt,
            {"job_id": job_id, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return MigrationJob(
            id=row[0],
            tenant_id=row[1],
            source_type=row[2],
            status=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
    
    async def list_migration_jobs(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MigrationJob]:
        """List migration jobs"""
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit, "offset": offset}
        
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        where_clause = " AND ".join(conditions)
        
        stmt = text(f"""
            SELECT id, tenant_id, source_type, status, created_at, updated_at
            FROM migration_jobs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        
        return [
            MigrationJob(
                id=row[0],
                tenant_id=row[1],
                source_type=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
            )
            for row in rows
        ]
    
    async def get_latest_migration_version(
        self,
        tenant_id: UUID
    ) -> Optional[MigrationVersion]:
        """Get latest approved migration version"""
        stmt = text("""
            SELECT id, tenant_id, version, approved_by, approved_at, created_at
            FROM migration_versions
            WHERE tenant_id = :tenant_id
              AND approved_at IS NOT NULL
            ORDER BY version DESC
            LIMIT 1
        """)
        result = await self.session.execute(stmt, {"tenant_id": tenant_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return MigrationVersion(
            id=row[0],
            tenant_id=row[1],
            version=row[2],
            approved_by=row[3],
            approved_at=row[4],
            created_at=row[5],
        )
