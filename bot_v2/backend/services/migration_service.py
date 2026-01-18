"""Migration service - handles data migration jobs"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.migration_repository import MigrationRepository
from backend.domain.migration import MigrationJob, MigrationVersion


class MigrationService:
    """Service for migration job management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.migration_repo = MigrationRepository(session)
    
    async def create_migration_job(
        self,
        tenant_id: UUID,
        source_type: str,
        source_data: Dict[str, Any]
    ) -> MigrationJob:
        """Create a new migration job"""
        from uuid import uuid4
        from datetime import datetime
        from sqlalchemy import text
        
        job_id = uuid4()
        stmt = text("""
            INSERT INTO migration_jobs (id, tenant_id, source_type, status, created_at, updated_at)
            VALUES (:id, :tenant_id, :source_type, :status, :created_at, :updated_at)
            RETURNING id, tenant_id, source_type, status, created_at, updated_at
        """)
        result = await self.session.execute(
            stmt,
            {
                "id": job_id,
                "tenant_id": tenant_id,
                "source_type": source_type,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        await self.session.commit()
        row = result.fetchone()
        
        return MigrationJob(
            id=row[0],
            tenant_id=row[1],
            source_type=row[2],
            status=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
    
    async def process_migration_job(
        self,
        job_id: UUID,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Process a migration job asynchronously.
        This would typically be called by a background worker.
        """
        job = await self.migration_repo.get_migration_job(job_id, tenant_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if job.status != "pending":
            return {"success": False, "error": f"Job already {job.status}"}
        
        # Update status to processing
        await self._update_job_status(job_id, "processing")
        
        try:
            # Process based on source_type
            if job.source_type == "excel":
                result = await self._process_excel_migration(job, tenant_id)
            elif job.source_type == "cms":
                result = await self._process_cms_migration(job, tenant_id)
            elif job.source_type == "crawl":
                result = await self._process_crawl_migration(job, tenant_id)
            elif job.source_type == "ai":
                result = await self._process_ai_migration(job, tenant_id)
            else:
                result = {"success": False, "error": f"Unknown source type: {job.source_type}"}
            
            if result.get("success"):
                await self._update_job_status(job_id, "completed")
            else:
                await self._update_job_status(job_id, "failed")
            
            return result
            
        except Exception as e:
            await self._update_job_status(job_id, "failed")
            return {"success": False, "error": str(e)}
    
    async def _update_job_status(
        self,
        job_id: UUID,
        status: str
    ) -> None:
        """Update job status"""
        from datetime import datetime
        from sqlalchemy import text
        
        stmt = text("""
            UPDATE migration_jobs
            SET status = :status, updated_at = :updated_at
            WHERE id = :job_id
        """)
        await self.session.execute(
            stmt,
            {
                "status": status,
                "updated_at": datetime.utcnow(),
                "job_id": job_id
            }
        )
        await self.session.commit()
    
    async def _process_excel_migration(
        self,
        job: MigrationJob,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Process Excel migration (placeholder)"""
        # In production, this would parse Excel and insert into database
        return {"success": True, "message": "Excel migration processed"}
    
    async def _process_cms_migration(
        self,
        job: MigrationJob,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Process CMS migration (placeholder)"""
        return {"success": True, "message": "CMS migration processed"}
    
    async def _process_crawl_migration(
        self,
        job: MigrationJob,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Process crawl migration (placeholder)"""
        return {"success": True, "message": "Crawl migration processed"}
    
    async def _process_ai_migration(
        self,
        job: MigrationJob,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Process AI migration (placeholder)"""
        return {"success": True, "message": "AI migration processed"}
