"""
Runtime Chat API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, Field

from app.infrastructure.database.engine import get_session
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.interfaces.api.dependencies import get_current_tenant_id
from app.core.shared.exceptions import EntityNotFoundError

chat_router = APIRouter(tags=["chat"])

# ========== Schemas ==========

class ChatMessageRequest(BaseModel):
    message: str = Field(..., max_length=5000, min_length=1)
    bot_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class WidgetChatRequest(BaseModel):
    """Public widget chat - không cần JWT. Dùng cho embed trên website."""
    tenant_id: str = Field(..., min_length=1)
    bot_id: str = Field(..., min_length=1)
    message: str = Field(..., max_length=5000, min_length=1)
    session_id: Optional[str] = None

# ========== Endpoints ==========

@chat_router.post("/chat/message")
async def chat_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Xử lý tin nhắn chat từ user thông qua Hybrid Orchestrator.
    """
    try:
        orchestrator = HybridOrchestrator(db)
        result = await orchestrator.handle_message(
            tenant_id=tenant_id,
            bot_id=request.bot_id,
            message=request.message,
            session_id=request.session_id,
            background_tasks=background_tasks
        )
        return result
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/chat/widget-message")
async def widget_chat_message(
    request: WidgetChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Chat endpoint cho Web Widget (public, không cần JWT).
    Website embed gửi tenant_id + bot_id trong body.
    """
    try:
        orchestrator = HybridOrchestrator(db)
        result = await orchestrator.handle_message(
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            message=request.message,
            session_id=request.session_id,
            background_tasks=background_tasks,
            channel_code="webchat"
        )
        return result
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
