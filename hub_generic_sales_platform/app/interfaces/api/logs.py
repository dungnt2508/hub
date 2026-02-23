"""
Logs & Conversation History API (Read-only + Handover)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from typing import Optional, List

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import SessionRepository, ConversationTurnRepository, ContextSlotRepository
from app.infrastructure.database.models.runtime import RuntimeSession
from app.interfaces.api.dependencies import get_current_tenant_id
from app.infrastructure.websocket import get_monitor_ws_manager

logs_router = APIRouter(tags=["logs"])


@logs_router.get("/sessions")
async def list_sessions(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    bot_id: Optional[str] = Query(None),
    channel_code: Optional[str] = Query(None),
    active_only: bool = Query(False, description="Only return non-CLOSED sessions (for monitor)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List conversation sessions for logs/monitor (read-only). Tenant isolation enforced.
    """
    repo = SessionRepository(db)
    sessions = await repo.list_for_logs(
        tenant_id=tenant_id,
        bot_id=bot_id,
        channel_code=channel_code,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    return [
        {
            "id": s.id,
            "tenant_id": s.tenant_id,
            "bot_id": s.bot_id,
            "bot_version_id": s.bot_version_id,
            "channel_code": s.channel_code,
            "lifecycle_state": s.lifecycle_state,
            "ext_metadata": getattr(s, "ext_metadata", None),  # zalo_user_id, display_name, etc.
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@logs_router.get("/sessions/{session_id}/state")
async def get_session_state(
    session_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
):
    """
    Get session lifecycle state and context slots for Studio/Monitor UI.
    Tenant isolation enforced.
    """
    session_repo = SessionRepository(db)
    slot_repo = ContextSlotRepository(db)

    session = await session_repo.get(session_id, tenant_id=tenant_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    slots = await slot_repo.get_by_session(session_id, tenant_id)
    slots_data = [
        {
            "key": s.key,
            "value": s.value,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
        }
        for s in slots
    ]

    return {
        "session_id": session_id,
        "lifecycle_state": getattr(session, "lifecycle_state", "idle") or "idle",
        "slots": slots_data,
    }


@logs_router.get("/sessions/{session_id}/turns")
async def get_session_turns(
    session_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get conversation turns for a session (read-only). Tenant isolation enforced.
    """
    session_repo = SessionRepository(db)
    turn_repo = ConversationTurnRepository(db)

    # Verify session exists and belongs to tenant
    session = await session_repo.get(session_id, tenant_id=tenant_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turns = await turn_repo.get_by_session(
        session_id=session_id,
        tenant_id=tenant_id,
        limit=limit
    )
    return {
        "session_id": session_id,
        "turns": [
            {
                "id": t.id,
                "speaker": (spk := (t.speaker.value if hasattr(t.speaker, "value") else str(t.speaker))),
                "role": "assistant" if spk == "bot" else spk,
                "message": t.message,
                "content": t.message,
                "ui_metadata": t.ui_metadata,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in turns
        ]
    }


@logs_router.post("/sessions/{session_id}/handover")
async def handover_session(
    session_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Human agent takes over the conversation. Session state -> HANDOVER.
    After handover, messages sent via /chat/message are logged as human replies (no LLM).
    """
    session_repo = SessionRepository(db)
    session = await session_repo.get(session_id, tenant_id=tenant_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Gửi thông báo khách (Zalo/Web) trước khi cập nhật DB
    await _notify_customer_handover(db, session, tenant_id)

    stmt = (
        sa_update(RuntimeSession)
        .where(RuntimeSession.id == session_id, RuntimeSession.tenant_id == tenant_id)
        .values(
            lifecycle_state="handover",
            flow_context={"handover_at": datetime.now(timezone.utc).isoformat(), "human_controlled": True},
            state_updated_at=datetime.now(timezone.utc),
        )
    )
    await db.execute(stmt)
    await db.commit()

    # Gửi thông báo WebSocket cho Monitor (client cập nhật UI real-time)
    try:
        manager = get_monitor_ws_manager()
        await manager.broadcast_handover(tenant_id, session_id, lifecycle_state="handover")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"WebSocket broadcast failed: {e}")

    return {"message": "Handover successful", "session_id": session_id, "lifecycle_state": "handover"}


async def _notify_customer_handover(db, session, tenant_id: str) -> None:
    """Gửi thông báo 'Nhân viên đang hỗ trợ bạn' tới khách qua kênh tương ứng (Zalo, v.v.)."""
    channel = getattr(session, "channel_code", None) or ""
    ext = getattr(session, "ext_metadata", None) or {}

    if channel.lower() == "zalo":
        zalo_user_id = ext.get("zalo_user_id")
        if not zalo_user_id:
            return
        try:
            from app.infrastructure.database.repositories.bot_repo import ChannelConfigurationRepository
            from app.infrastructure.external.zalo_service import ZaloService

            config_repo = ChannelConfigurationRepository(db)
            channel_config = await config_repo.get_by_bot_version_and_channel(
                session.bot_version_id, "ZALO"
            )
            if channel_config and channel_config.config:
                token = channel_config.config.get("access_token")
                if token:
                    zalo = ZaloService()
                    msg = "Nhân viên đang hỗ trợ bạn. Vui lòng chờ trong giây lát."
                    await zalo.send_message(token, zalo_user_id, msg)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Zalo handover notify failed: {e}")
