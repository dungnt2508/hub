import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.services.migration_service import MigrationService, BaseMigrationProvider
from app.infrastructure.database.models.knowledge import (
    MigrationJob, MigrationJobStatus, MigrationSourceType,
    KnowledgeDomain, DomainAttributeDefinition
)
from app.infrastructure.database.repositories import MigrationJobRepository
from unittest.mock import AsyncMock, MagicMock

class MockProvider(BaseMigrationProvider):
    async def fetch_and_parse(self, job, db):
        return {
            "offerings": [
                {
                    "code": "PROD-MIG-1",
                    "name": "Migrated Product 1",
                    "description": "Description 1",
                    "attributes": {
                        "color": "Red",
                        "weight": 1.5
                    },
                    "variants": [
                        {"sku": "SKU-MIG-1-A", "name": "Variant A"}
                    ]
                }
            ]
        }

@pytest.mark.asyncio
async def test_migration_lifecycle(db: AsyncSession, tenant_1):
    # 1. Setup Domain and Attribute definitions
    domain = KnowledgeDomain(code="mig-dom", name="Migration Domain")
    db.add(domain)
    await db.flush()
    
    attr_color = DomainAttributeDefinition(
        domain_id=domain.id,
        key="color",
        value_type="text"
    )
    attr_weight = DomainAttributeDefinition(
        domain_id=domain.id,
        key="weight",
        value_type="number"
    )
    db.add_all([attr_color, attr_weight])
    await db.flush()

    service = MigrationService(db)
    # Use valid source type from enum
    service.register_provider(MigrationSourceType.EXCEL_UPLOAD, MockProvider)

    # 2. Create Job
    job = await service.create_job(
        tenant_id=tenant_1.id,
        domain_id=domain.id,
        source_type=MigrationSourceType.EXCEL_UPLOAD,
        metadata={"file": "test.xlsx"}
    )
    assert job.status == MigrationJobStatus.PENDING
    assert job.tenant_id == tenant_1.id

    # 3. Run Job Sync
    await service.run_job_sync(job.id, tenant_id=tenant_1.id)
    # Refreshing job to get updated state
    job_staged = await MigrationJobRepository(db).get(job.id, tenant_id=tenant_1.id)
    assert job_staged.status == MigrationJobStatus.STAGED
    assert "offerings" in job_staged.staged_data

    # 4. Commit Job
    await service.commit_job(job.id, tenant_id=tenant_1.id)
    job_completed = await MigrationJobRepository(db).get(job.id, tenant_id=tenant_1.id)
    assert job_completed.status == MigrationJobStatus.COMPLETED

    # 5. Verify Database State
    from app.infrastructure.database.repositories import OfferingRepository, OfferingVariantRepository
    offering_repo = OfferingRepository(db)
    variant_repo = OfferingVariantRepository(db)
    
    offerings = await offering_repo.get_multi(tenant_id=tenant_1.id)
    assert len(offerings) >= 1
    migrated_offering = next(o for o in offerings if o.code == "PROD-MIG-1")
    assert migrated_offering.domain_id == domain.id

    variants = await variant_repo.get_multi(tenant_id=tenant_1.id)
    assert any(v.sku == "SKU-MIG-1-A" for v in variants)

@pytest.mark.asyncio
async def test_migration_job_not_found(db: AsyncSession, tenant_1):
    service = MigrationService(db)
    # Should not raise exception, just return
    await service.run_job_sync(str(uuid.uuid4()), tenant_id=tenant_1.id)

@pytest.mark.asyncio
async def test_migration_provider_not_found(db: AsyncSession, tenant_1):
    domain = KnowledgeDomain(code="mig-dom-2", name="Migration Domain 2")
    db.add(domain)
    await db.flush()
    
    service = MigrationService(db)
    # Use valid source type from enum that is NOT registered
    job = await service.create_job(
        tenant_id=tenant_1.id,
        domain_id=domain.id,
        source_type=MigrationSourceType.HARAVAN_SYNC,
        metadata={}
    )
    
    await service.run_job_sync(job.id, tenant_id=tenant_1.id)
    job_failed = await MigrationJobRepository(db).get(job.id, tenant_id=tenant_1.id)
    assert job_failed.status == MigrationJobStatus.FAILED
    assert "Provider not found" in job_failed.error_log

@pytest.mark.asyncio
async def test_migration_commit_wrong_status(db: AsyncSession, tenant_1):
    domain = KnowledgeDomain(code="mig-dom-3", name="Migration Domain 3")
    db.add(domain)
    await db.flush()
    
    service = MigrationService(db)
    job = await service.create_job(
        tenant_id=tenant_1.id,
        domain_id=domain.id,
        source_type=MigrationSourceType.EXCEL_UPLOAD,
        metadata={}
    )
    
    with pytest.raises(Exception) as excinfo:
        await service.commit_job(job.id, tenant_id=tenant_1.id)
    assert "Job không ở trạng thái STAGED" in str(excinfo.value)
