"""
WebSocket Connection Manager - Monitor & Handover notifications

Quản lý kết nối WebSocket cho trang Monitor. Khi nhân viên bấm "Tiếp quản",
broadcast event tới các client đang xem session để cập nhật real-time.
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MonitorConnectionManager:
    """
    Connection manager cho Monitor page.
    Mỗi tenant có một set connections. Khi handover xảy ra, broadcast tới tenant đó.
    """

    def __init__(self):
        # tenant_id -> set of WebSocket
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
    ) -> None:
        """Chấp nhận connection và đăng ký theo tenant_id."""
        await websocket.accept()
        async with self._lock:
            if tenant_id not in self._connections:
                self._connections[tenant_id] = set()
            self._connections[tenant_id].add(websocket)
        logger.info(f"Monitor WS connected: tenant={tenant_id}, total={len(self._connections.get(tenant_id, []))}")

    async def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        """Ngắt connection."""
        async with self._lock:
            if tenant_id in self._connections:
                self._connections[tenant_id].discard(websocket)
                if not self._connections[tenant_id]:
                    del self._connections[tenant_id]
        logger.debug(f"Monitor WS disconnected: tenant={tenant_id}")

    async def broadcast_handover(
        self,
        tenant_id: str,
        session_id: str,
        lifecycle_state: str = "handover",
    ) -> None:
        """
        Gửi thông báo handover tới tất cả client Monitor của tenant.
        Client nhận được để cập nhật UI (badge "Nhân viên hỗ trợ", refresh list).
        """
        payload = {
            "event": "handover",
            "session_id": session_id,
            "lifecycle_state": lifecycle_state,
            "message": "Nhân viên đã tiếp quản hội thoại. Khách sẽ nhận thông báo.",
        }
        await self._broadcast(tenant_id, payload)

    async def _broadcast(self, tenant_id: str, payload: dict) -> None:
        """Gửi payload JSON tới tất cả connections của tenant."""
        dead = set()
        async with self._lock:
            conns = list(self._connections.get(tenant_id, set()))

        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.warning(f"Monitor WS send error: {e}")
                dead.add(ws)

        if dead:
            async with self._lock:
                if tenant_id in self._connections:
                    self._connections[tenant_id] -= dead


# Singleton
_manager: Optional[MonitorConnectionManager] = None


def get_monitor_ws_manager() -> MonitorConnectionManager:
    global _manager
    if _manager is None:
        _manager = MonitorConnectionManager()
    return _manager
