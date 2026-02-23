"""
Integration tests for Contacts API
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import MagicMock, AsyncMock, patch
from app.infrastructure.database.models.knowledge import KnowledgeDomain
from app.infrastructure.database.models.runtime import RuntimeSession
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository


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
async def test_contacts_list_empty(client, tenant_1):
    """Test contacts list when no sessions"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = tenant_1.id
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        resp = await client.get("/api/v1/contacts", headers={"X-Tenant-ID": tenant_1.id})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_contacts_list_with_sessions(client, tenant_1, db):
    """Test contacts derived from runtime_session với ext_metadata"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = tenant_1.id
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        domain = KnowledgeDomain(code=f"c-{uuid.uuid4().hex[:6]}", name="C")
        db.add(domain)
        await db.flush()

        bot_repo = BotRepository(db)
        ver_repo = BotVersionRepository(db)
        bot = await bot_repo.create({"domain_id": domain.id, "code": f"cb-{uuid.uuid4().hex[:6]}", "name": "CB"}, tenant_id=tenant_1.id)
        ver = await ver_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})

        session = RuntimeSession(
            id=str(uuid.uuid4()),
            bot_id=bot.id, bot_version_id=ver.id,
            tenant_id=tenant_1.id, channel_code="zalo", lifecycle_state="idle",
            ext_metadata={"zalo_user_id": "zalo_123", "user_id": "external_1"}
        )
        db.add(session)
        await db.flush()
        await db.commit()

        resp = await client.get("/api/v1/contacts", headers={"X-Tenant-ID": tenant_1.id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        c = data[0]
        assert "id" in c
        assert "name" in c
        assert "status" in c
        assert "last_active" in c
