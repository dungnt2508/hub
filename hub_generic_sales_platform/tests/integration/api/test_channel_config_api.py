"""
Integration tests for Channel Config API
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.infrastructure.database.repositories import BotVersionRepository


@pytest.mark.asyncio
async def test_list_channel_configs(client, tenant_1, bot_1, db):
    """Test list channel configs"""
    ver_repo = BotVersionRepository(db)
    await ver_repo.create({"bot_id": bot_1.id, "version": 1, "is_active": True})
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))

        resp = await client.get(
            "/api/v1/channel-configs",
            params={"bot_id": bot_1.id},
            headers={"X-Tenant-ID": tenant_1.id}
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
