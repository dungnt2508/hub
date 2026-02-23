"""
WebSocket API - Monitor real-time updates (Handover notifications)

Client kết nối để nhận thông báo khi session chuyển sang handover.
Browser WebSocket API không gửi được custom headers → dùng token trong query.
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.infrastructure.websocket import get_monitor_ws_manager
from app.core.services.auth_service import AuthService
from app.infrastructure.database.engine import get_session_maker

logger = logging.getLogger(__name__)

ws_router = APIRouter(tags=["websocket"])


@ws_router.websocket("/ws/monitor")
async def monitor_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token (browser WS không gửi được header)"),
):
    """
    WebSocket cho Monitor page. Nhận thông báo real-time khi Handover.
    Query: ?token=<jwt> (lấy từ localStorage sau khi login)
    """
    # Validate token và lấy tenant_id
    tenant_id = None
    try:
        session_maker = get_session_maker()
        async with session_maker() as db:
            user = await AuthService.get_user_from_token(db, token)
            if user:
                tenant_id = user.tenant_id
    except Exception as e:
        logger.warning(f"Monitor WS auth failed: {e}")

    if not tenant_id:
        await websocket.close(code=4001)
        return

    manager = get_monitor_ws_manager()
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, tenant_id)
