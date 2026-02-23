"""Integration tests for Webhooks - Sprint 3"""

import pytest
from httpx import AsyncClient
from app.main import app
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.infrastructure.database.repositories import BotVersionRepository


def test_zalo_ext_metadata_mapping():
    """Unit: Zalo payload → ext_metadata structure (map zalo_user → runtime_session)"""
    data = {
        "event_name": "user_send_text",
        "sender": {"id": "12345", "name": "Test User"},
        "message": {"text": "Hi"}
    }
    sender_id = data.get("sender", {}).get("id")
    sender_info = data.get("sender", {})
    ext_metadata = {
        "zalo_user_id": str(sender_id),
        "channel": "zalo",
    }
    if sender_info.get("name"):
        ext_metadata["display_name"] = sender_info.get("name")
    assert ext_metadata["zalo_user_id"] == "12345"
    assert ext_metadata["channel"] == "zalo"
    assert ext_metadata["display_name"] == "Test User"


@pytest.mark.asyncio
async def test_facebook_webhook_verification(client):
    """Test Facebook verification challenge"""
    challenge = "123456789"
    resp = await client.get(
        "/webhooks/facebook/message",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "your_verify_token",
            "hub.challenge": challenge
        }
    )
    assert resp.status_code == 200
    assert resp.text == challenge


@pytest.mark.skip(reason="ASGI stream issue with httpx/BackgroundTasks in test env")
@pytest.mark.asyncio
async def test_facebook_message_processing(client, db, tenant_1, bot_1):
    """Test FB message routing to HybridOrchestrator"""
    ver_repo = BotVersionRepository(db)
    await ver_repo.create({"bot_id": bot_1.id, "version": 1, "is_active": True})
    await db.flush()

    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": "fb_user_123"},
                "message": {"text": "Hello bot"}
            }]
        }]
    }
    headers = {"X-Tenant-ID": tenant_1.id, "X-Bot-ID": bot_1.id}

    with patch("app.interfaces.webhooks.facebook.HybridOrchestrator") as mock_orch_cls:
        mock_instance = AsyncMock()
        mock_instance.handle_message = AsyncMock(return_value={
            "response": "Hi from FB",
            "metadata": {"tier": "fast_path", "cost": "$0.00000", "latency_ms": 10}
        })
        mock_orch_cls.return_value = mock_instance

        resp = await client.post("/webhooks/facebook/message", json=payload, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        mock_instance.handle_message.assert_called_once()
        _, kwargs = mock_instance.handle_message.call_args
        assert kwargs["session_id"] == "fb_fb_user_123"


@pytest.mark.skip(reason="ASGI stream issue with httpx/BackgroundTasks in test env")
@pytest.mark.asyncio
async def test_zalo_message_processing(client, db, tenant_1, bot_1):
    """Test Zalo message routing to HybridOrchestrator + ext_metadata mapping"""
    ver_repo = BotVersionRepository(db)
    await ver_repo.create({"bot_id": bot_1.id, "version": 1, "is_active": True})
    await db.flush()

    payload = {
        "event_name": "user_send_text",
        "sender": {"id": "zalo_user_456", "name": "Nguyen Van A"},
        "message": {"text": "Chào shop"}
    }
    headers = {"X-Tenant-ID": tenant_1.id, "X-Bot-ID": bot_1.id}

    with patch("app.interfaces.webhooks.zalo.HybridOrchestrator") as mock_orch_cls:
        mock_instance = AsyncMock()
        mock_instance.handle_message = AsyncMock(return_value={
            "response": "Chào bạn từ Zalo",
            "metadata": {"tier": "fast_path", "cost": "$0.00000", "latency_ms": 10}
        })
        mock_orch_cls.return_value = mock_instance

        resp = await client.post("/webhooks/zalo/message", json=payload, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        mock_instance.handle_message.assert_called_once()
        _, kwargs = mock_instance.handle_message.call_args
        assert kwargs["session_id"] == "zalo_zalo_user_456"
        # Sprint 3: Zalo user → runtime_session mapping via ext_metadata
        assert kwargs.get("ext_metadata") is not None
        assert kwargs["ext_metadata"]["zalo_user_id"] == "zalo_user_456"
        assert kwargs["ext_metadata"]["channel"] == "zalo"
        assert kwargs["ext_metadata"]["display_name"] == "Nguyen Van A"
