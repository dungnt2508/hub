"""
Migration Hub API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.core.services.migration_service import MigrationService, MigrationSourceType
from app.core.services.migration_providers import RealWebScraperProvider
from app.infrastructure.database.repositories import MigrationJobRepository, BotRepository
from app.interfaces.api.dependencies import get_current_tenant_id

migration_router = APIRouter(prefix="/catalog/migrate", tags=["migration"])

# ========== Schemas ==========

class ScrapeRequest(BaseModel):
    url: str
    bot_id: Optional[str] = None
    domain_id: Optional[str] = None
    status: Optional[str] = None

# ========== Endpoints ==========

@migration_router.post("/scrape")
async def start_web_scrape(
    payload: ScrapeRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Bắt đầu quá trình cào dữ liệu từ Website bằng AI"""
    service = MigrationService(db)
    service.register_provider(MigrationSourceType.WEB_SCRAPER, RealWebScraperProvider)
    
    metadata = {"url": payload.url}
    
    # 1. Resolve domain_id from payload or bot_id
    resolved_domain_id = payload.domain_id
    if payload.bot_id and not resolved_domain_id:
        bot_repo = BotRepository(db)
        bot = await bot_repo.get(payload.bot_id, tenant_id=tenant_id)
        if bot and bot.domain_id:
            resolved_domain_id = bot.domain_id
            
    if not resolved_domain_id:
        raise HTTPException(
            status_code=400, 
            detail="domain_id là bắt buộc để bắt đầu cào dữ liệu (có thể truyền trực tiếp hoặc lấy từ bot_id)."
        )

    job = await service.create_job(
        tenant_id=tenant_id,
        domain_id=resolved_domain_id,
        source_type="web_scraper",
        metadata=metadata,
        bot_id=payload.bot_id
    )
    
    background_tasks.add_task(service.run_job_sync, job.id, tenant_id)
    
    return {
        "job_id": job.id,
        "status": job.status,
        "message": "Quá trình cào dữ liệu đã bắt đầu ngầm."
    }

@migration_router.get("/jobs/{job_id}")
async def get_migration_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Kiểm tra trạng thái và lấy dữ liệu đã bóc tách (Staged)"""
    repo = MigrationJobRepository(db)
    job = await repo.get(job_id, tenant_id=tenant_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
        
    return {
        "id": job.id,
        "status": job.status,
        "source_type": job.source_type,
        "metadata": job.batch_metadata,
        "staged_data": job.staged_data,
        "error_log": job.error_log,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "bot_id": job.bot_id,
        "domain_id": job.domain_id,
    }

@migration_router.post("/jobs/{job_id}/confirm")
async def commit_migration(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Xác nhận và đẩy dữ liệu từ vùng đệm vào Catalog chính thức"""
    service = MigrationService(db)
    try:
        await service.commit_job(job_id, tenant_id)
        return {"message": "Dữ liệu đã được nạp vào Catalog thành công."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@migration_router.get("/jobs")
async def list_migration_jobs(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách các đợt migration của tenant"""
    repo = MigrationJobRepository(db)
    jobs = await repo.get_multi(limit=50, tenant_id=tenant_id)
    
    return [
        {
            "id": job.id,
            "status": job.status,
            "source_type": job.source_type,
            "metadata": job.batch_metadata,
            "bot_id": job.bot_id,
            "domain_id": job.domain_id,
            "staged_data": job.staged_data,
            "error_log": job.error_log,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }
        for job in jobs
    ]
