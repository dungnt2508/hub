"""Unit tests for WebSocket MonitorConnectionManager (Sprint 3)"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.websocket.manager import MonitorConnectionManager


@pytest.mark.asyncio
async def test_ws_manager_connect_disconnect():
    """Connect và disconnect đăng ký đúng tenant"""
    manager = MonitorConnectionManager()
    ws = MagicMock()
    ws.accept = AsyncMock()
    await manager.connect(ws, "tenant-1")
    assert "tenant-1" in manager._connections
    assert ws in manager._connections["tenant-1"]
    await manager.disconnect(ws, "tenant-1")
    assert "tenant-1" not in manager._connections or ws not in manager._connections.get("tenant-1", set())


@pytest.mark.asyncio
async def test_ws_manager_broadcast_handover():
    """broadcast_handover gửi payload đúng format"""
    manager = MonitorConnectionManager()
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    await manager.connect(ws, "tenant-1")
    await manager.broadcast_handover("tenant-1", "session-123", "handover")
    ws.send_json.assert_called_once()
    call_arg = ws.send_json.call_args[0][0]
    assert call_arg["event"] == "handover"
    assert call_arg["session_id"] == "session-123"
    assert call_arg["lifecycle_state"] == "handover"
    assert "Nhân viên" in call_arg["message"]


@pytest.mark.asyncio
async def test_ws_manager_broadcast_no_connections():
    """broadcast khi không có connection không crash"""
    manager = MonitorConnectionManager()
    await manager.broadcast_handover("tenant-unknown", "sess-1", "handover")
