"""
Integration tests for Analytics API

Note: Analytics uses date_trunc (PostgreSQL). Skip on SQLite (test DB).
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import MagicMock, AsyncMock, patch
from app.infrastructure.database.models.knowledge import KnowledgeDomain
from app.infrastructure.database.models.runtime import RuntimeSession
from app.infrastructure.database.models.decision import RuntimeDecisionEvent, DecisionType


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


@pytest.mark.skip(reason="Analytics uses date_trunc (PostgreSQL only); test DB is SQLite")
@pytest.mark.asyncio
async def test_analytics_dashboard_empty(client, tenant_1, db):
    """Test analytics dashboard với tenant chưa có sessions"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = tenant_1.id
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        resp = await client.get(
            "/api/v1/analytics/dashboard",
            headers={"X-Tenant-ID": tenant_1.id},
            params={"days": 30}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "total_savings" in data["summary"]
        assert "automation_rate" in data["summary"]
        assert "avg_latency" in data["summary"]
        assert "volume_history" in data
        assert "efficiency_trend" in data


@pytest.mark.skip(reason="Analytics uses date_trunc (PostgreSQL only); test DB is SQLite")
@pytest.mark.asyncio
async def test_analytics_dashboard_with_data(client, tenant_1, db):
    """Test analytics dashboard khi có session và decision"""
    from app.infrastructure.database.repositories import BotRepository, BotVersionRepository

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_user = MagicMock()
        mock_user.tenant_id = tenant_1.id
        mock_user.role = "admin"
        mock_user.status = "active"
        mock_user.tenant.status = "active"
        m.return_value = mock_user

        domain = KnowledgeDomain(code=f"a-{uuid.uuid4().hex[:6]}", name="A")
        db.add(domain)
        await db.flush()

        bot_repo = BotRepository(db)
        ver_repo = BotVersionRepository(db)
        bot = await bot_repo.create({"domain_id": domain.id, "code": f"b-{uuid.uuid4().hex[:6]}", "name": "B"}, tenant_id=tenant_1.id)
        version = await ver_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})

        session = RuntimeSession(
            id=str(uuid.uuid4()),
            bot_id=bot.id, bot_version_id=version.id,
            tenant_id=tenant_1.id, channel_code="web", flow_step="IDLE"
        )
        db.add(session)
        await db.flush()

        evt = RuntimeDecisionEvent(
            session_id=session.id, bot_version_id=version.id,
            tier_code="fast", decision_type=DecisionType.PROCEED,
            estimated_cost=0.001, latency_ms=120, decision_reason="test"
        )
        db.add(evt)
        await db.flush()
        await db.commit()

        resp = await client.get(
            "/api/v1/analytics/dashboard",
            headers={"X-Tenant-ID": tenant_1.id},
            params={"days": 30}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["summary"]["total_savings"].replace("$", "")) >= 0
        assert data["summary"]["automation_rate"] >= 0
