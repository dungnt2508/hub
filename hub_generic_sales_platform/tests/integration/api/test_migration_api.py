"""
Integration tests for Migration API
"""
import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from app.infrastructure.database.models.knowledge import MigrationJob, MigrationJobStatus, MigrationSourceType


@pytest.mark.asyncio
async def test_list_migration_jobs(client, tenant_1):
    """Test GET /catalog/migrate/jobs"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get(
            "/api/v1/catalog/migrate/jobs",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_migration_job_200(client, tenant_1, db):
    """Test GET /catalog/migrate/jobs/{job_id} - job tồn tại"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain

    dom = KnowledgeDomain(code=f"mig-{uuid.uuid4().hex[:6]}", name="Mig Domain")
    db.add(dom)
    await db.flush()

    job = MigrationJob(
        tenant_id=tenant_1.id,
        domain_id=dom.id,
        source_type=MigrationSourceType.WEB_SCRAPER,
        status=MigrationJobStatus.PENDING,
        batch_metadata={"url": "https://example.com"},
    )
    db.add(job)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get(
            f"/api/v1/catalog/migrate/jobs/{job.id}",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job.id
    assert data["status"] == MigrationJobStatus.PENDING
    assert data.get("metadata") and data["metadata"].get("url") == "https://example.com"


@pytest.mark.asyncio
async def test_get_migration_job_404(client, tenant_1):
    """Test GET /catalog/migrate/jobs/{job_id} - job không tồn tại"""
    fake_id = str(uuid.uuid4())
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get(
            f"/api/v1/catalog/migrate/jobs/{fake_id}",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_scrape_400_no_domain(client, tenant_1):
    """Test POST /catalog/migrate/scrape - thiếu domain_id trả 400"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            "/api/v1/catalog/migrate/scrape",
            json={"url": "https://example.com"},
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 400
    assert "domain_id" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_scrape_200_with_domain(client, tenant_1, bot_tenant_1):
    """Test POST /catalog/migrate/scrape - có domain_id trả 200"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        with patch("app.interfaces.api.migration.MigrationService") as mock_svc:
            from app.infrastructure.database.models.knowledge import MigrationJob, MigrationJobStatus
            fake_job = MagicMock()
            fake_job.id = str(uuid.uuid4())
            fake_job.status = MigrationJobStatus.PENDING
            mock_inst = AsyncMock()
            mock_inst.create_job = AsyncMock(return_value=fake_job)
            mock_inst.run_job_sync = AsyncMock()
            mock_svc.return_value = mock_inst

            resp = await client.post(
                "/api/v1/catalog/migrate/scrape",
                json={
                    "url": "https://example.com",
                    "domain_id": str(bot_tenant_1.domain_id),
                },
                headers={"X-Tenant-ID": tenant_1.id},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == MigrationJobStatus.PENDING


@pytest.mark.asyncio
async def test_commit_migration_400(client, tenant_1, db):
    """Test POST /jobs/{id}/confirm - job không ở trạng thái STAGED trả 400"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain

    dom = KnowledgeDomain(code=f"commit-{uuid.uuid4().hex[:6]}", name="Commit Domain")
    db.add(dom)
    await db.flush()

    job = MigrationJob(
        tenant_id=tenant_1.id,
        domain_id=dom.id,
        source_type=MigrationSourceType.WEB_SCRAPER,
        status=MigrationJobStatus.PENDING,  # Not STAGED
        batch_metadata={"url": "https://x.com"},
    )
    db.add(job)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            f"/api/v1/catalog/migrate/jobs/{job.id}/confirm",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 400
