"""
Integration tests for Knowledge API – FAQs, UseCases, Comparisons (offering_ids)
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import MagicMock, AsyncMock, patch
from app.infrastructure.database.models.knowledge import KnowledgeDomain, BotComparison
from app.infrastructure.database.models.offering import TenantOffering, OfferingStatus


@pytest.fixture
async def client(db):
    """Async client with auth mock"""
    from app.infrastructure.database.engine import get_session

    async def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    with patch("app.interfaces.middleware.auth.get_bearer_token", return_value="test_token"), \
         patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_get_user:
        mock_user = MagicMock()
        mock_user.id = "test_user"
        mock_user.tenant_id = "TBD"
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        mock_get_user.return_value = mock_user

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": "Bearer test_token"}
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_comparison_crud_offering_ids(client, tenant_1, db):
    """Test Comparison CRUD với offering_ids (schema source of truth)"""
    mock_user = MagicMock()
    mock_user.id = "user1"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = mock_user

        domain = KnowledgeDomain(code=f"cmp-{uuid.uuid4().hex[:6]}", name="Compare Domain")
        db.add(domain)
        await db.flush()

        o1 = TenantOffering(
            tenant_id=tenant_1.id, domain_id=domain.id,
            code=f"off1-{uuid.uuid4().hex[:6]}", status=OfferingStatus.ACTIVE
        )
        o2 = TenantOffering(
            tenant_id=tenant_1.id, domain_id=domain.id,
            code=f"off2-{uuid.uuid4().hex[:6]}", status=OfferingStatus.ACTIVE
        )
        db.add_all([o1, o2])
        await db.flush()

        h = {"X-Tenant-ID": tenant_1.id}

        # Create
        create_data = {
            "domain_id": domain.id,
            "title": "So sánh A vs B",
            "description": "Bảng so sánh",
            "offering_ids": [o1.id, o2.id],
            "comparison_data": {"Battery": "5000mAh", "Price": "10M"},
            "is_active": True,
        }
        resp = await client.post("/api/v1/comparisons", json=create_data, headers=h)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["title"] == "So sánh A vs B"
        assert data["offering_ids"] == [o1.id, o2.id]
        assert "id" in data
        comp_id = data["id"]

        # List
        resp = await client.get("/api/v1/comparisons", headers=h)
        assert resp.status_code == 200
        items = resp.json()
        assert any(c["id"] == comp_id for c in items)

        # Update
        resp = await client.put(
            f"/api/v1/comparisons/{comp_id}",
            json={"title": "So sánh Cập nhật", "offering_ids": [o1.id]},
            headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "So sánh Cập nhật"
        assert resp.json()["offering_ids"] == [o1.id]

        # Delete
        resp = await client.delete(f"/api/v1/comparisons/{comp_id}", headers=h)
        assert resp.status_code == 200

        resp = await client.get("/api/v1/comparisons", headers=h)
        assert not any(c["id"] == comp_id for c in resp.json())


@pytest.mark.asyncio
async def test_comparison_list_by_domain(client, tenant_1, db):
    """Test list comparisons filter by domain_id"""
    mock_user = MagicMock()
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = mock_user

        d1 = KnowledgeDomain(code=f"d1-{uuid.uuid4().hex[:6]}", name="Domain 1")
        d2 = KnowledgeDomain(code=f"d2-{uuid.uuid4().hex[:6]}", name="Domain 2")
        db.add_all([d1, d2])
        await db.flush()

        o = TenantOffering(tenant_id=tenant_1.id, domain_id=d1.id, code=f"o-{uuid.uuid4().hex[:6]}", status=OfferingStatus.ACTIVE)
        db.add(o)
        await db.flush()

        comp = BotComparison(
            tenant_id=tenant_1.id, domain_id=d1.id,
            title="Comp D1", offering_ids=[o.id], is_active=True
        )
        db.add(comp)
        await db.flush()

        h = {"X-Tenant-ID": tenant_1.id}
        resp = await client.get(f"/api/v1/comparisons?domain_id={d1.id}", headers=h)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert all(c.get("domain_id") == d1.id for c in items)


@pytest.mark.asyncio
async def test_comparison_404_on_update_nonexistent(client, tenant_1):
    """Test 404 when updating non-existent comparison"""
    mock_user = MagicMock()
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = mock_user

        fake_id = str(uuid.uuid4())
        resp = await client.put(
            f"/api/v1/comparisons/{fake_id}",
            json={"title": "X", "offering_ids": []},
            headers={"X-Tenant-ID": tenant_1.id}
        )
        assert resp.status_code == 404
