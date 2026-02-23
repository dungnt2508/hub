"""
Integration tests for Logs API (Sprint 3: handover, ext_metadata)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.infrastructure.database.repositories import BotVersionRepository


def _mock_user(tenant_id):
    u = MagicMock(tenant_id=tenant_id, role="admin", status="active")
    u.tenant = MagicMock(status="active")
    return u


@pytest.mark.asyncio
async def test_list_sessions(client, tenant_1):
    """Test GET /sessions - includes ext_metadata (zalo_user_id, etc.)"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        resp = await client.get(
            "/api/v1/sessions",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    # Sprint 3: response schema includes ext_metadata (zalo_user_id, etc.)
    sessions = resp.json()
    if sessions:
        assert "ext_metadata" in sessions[0]


@pytest.mark.asyncio
async def test_list_sessions_with_active_only(client, tenant_1):
    """Test GET /sessions?active_only=true"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        resp = await client.get(
            "/api/v1/sessions",
            params={"active_only": "true"},
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_handover_session(client, tenant_1, bot_1, db):
    """Test POST /sessions/{id}/handover - flow_step -> handover, WebSocket broadcast"""
    from app.infrastructure.database.repositories import SessionRepository

    ver_repo = BotVersionRepository(db)
    bv = await ver_repo.create({"bot_id": bot_1.id, "version": 1, "is_active": True})
    await db.flush()
    session_repo = SessionRepository(db)
    session_domain = await session_repo.create(
        {
            "id": "test-session-handover",
            "bot_id": bot_1.id,
            "bot_version_id": str(bv.id),
            "channel_code": "zalo",
            "lifecycle_state": "idle",
            "ext_metadata": {"zalo_user_id": "zalo_123"},
        },
        tenant_id=tenant_1.id,
    )
    session_id = str(session_domain.id)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        with patch("app.interfaces.api.logs.get_monitor_ws_manager") as mock_ws:
            mock_manager = AsyncMock()
            mock_ws.return_value = mock_manager
            with patch("app.interfaces.api.logs._notify_customer_handover", new_callable=AsyncMock):
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/handover",
                    headers={"Authorization": "Bearer test_token"},
                )
    assert resp.status_code == 200
    data = resp.json()
    assert data["lifecycle_state"] == "handover"
    assert data["session_id"] == session_id
    mock_manager.broadcast_handover.assert_called_once_with(
        tenant_1.id, session_id, lifecycle_state="handover"
    )


@pytest.mark.asyncio
async def test_handover_session_404(client, tenant_1):
    """Test handover returns 404 for non-existent session"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        resp = await client.post(
            "/api/v1/sessions/non-existent-session/handover",
            headers={"Authorization": "Bearer test_token"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_session_state(client, tenant_1, bot_1, db):
    """Test GET /sessions/{id}/state - lifecycle_state and slots"""
    from app.infrastructure.database.repositories import SessionRepository

    ver_repo = BotVersionRepository(db)
    bv = await ver_repo.create({"bot_id": bot_1.id, "version": 1, "is_active": True})
    await db.flush()
    session_repo = SessionRepository(db)
    session_domain = await session_repo.create(
        {
            "id": "test-session-state",
            "bot_id": bot_1.id,
            "bot_version_id": str(bv.id),
            "channel_code": "web",
            "lifecycle_state": "browsing",
        },
        tenant_id=tenant_1.id,
    )
    session_id = str(session_domain.id)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        resp = await client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"Authorization": "Bearer test_token"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["lifecycle_state"] == "browsing"
    assert "slots" in data
    assert isinstance(data["slots"], list)


@pytest.mark.asyncio
async def test_get_session_state_404(client, tenant_1):
    """Test GET /sessions/{id}/state returns 404 for non-existent session"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = _mock_user(tenant_1.id)
        resp = await client.get(
            "/api/v1/sessions/non-existent-session/state",
            headers={"Authorization": "Bearer test_token"},
        )
    assert resp.status_code == 404
