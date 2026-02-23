"""
Integration tests for Guardrails API
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
async def client(db):
    from app.infrastructure.database.engine import get_session

    async def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    with patch("app.interfaces.middleware.auth.get_bearer_token", return_value="test_token"), \
         patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = "TBD"
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": "Bearer test_token"}
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_guardrails_crud(client, tenant_1):
    """Test Guardrails CRUD"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = tenant_1.id
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        h = {"X-Tenant-ID": tenant_1.id}

        # Create
        create_data = {
            "code": "NO_SENSITIVE",
            "name": "Block Sensitive",
            "condition_expression": "contains_sensitive",
            "violation_action": "block",
            "fallback_message": "Refused.",
            "priority": 10,
            "is_active": True,
        }
        resp = await client.post("/api/v1/guardrails", json=create_data, headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "NO_SENSITIVE"
        assert "id" in data
        gid = data["id"]

        # List
        resp = await client.get("/api/v1/guardrails", headers=h)
        assert resp.status_code == 200
        items = resp.json()
        assert any(g["id"] == gid for g in items)

        # List active_only
        resp = await client.get("/api/v1/guardrails?active_only=true", headers=h)
        assert resp.status_code == 200

        # Update
        resp = await client.put(
            f"/api/v1/guardrails/{gid}",
            json={"name": "Updated Block"},
            headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Block"

        # Delete
        resp = await client.delete(f"/api/v1/guardrails/{gid}", headers=h)
        assert resp.status_code == 200
