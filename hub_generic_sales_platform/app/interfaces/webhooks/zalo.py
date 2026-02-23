from fastapi import APIRouter, Request, BackgroundTasks, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.engine import get_session
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator

zalo_router = APIRouter(prefix="/webhooks/zalo", tags=["webhooks"])


def _extract_tenant_bot_from_path(request: Request) -> tuple:
    """Extract tenant_id, bot_id from path /webhooks/zalo/{tenant_id}/{bot_id}/message"""
    parts = request.url.path.rstrip("/").split("/")
    if len(parts) >= 7 and parts[1] == "webhooks" and parts[2] == "zalo":
        return parts[4], parts[5]  # tenant_id, bot_id
    return None, None


@zalo_router.get("/message")
async def verify_zalo_webhook(request: Request):
    """
    Zalo Webhook Verification (GET).
    Zalo gửi GET request khi đăng ký webhook. Trả về challenge nếu có.
    """
    data = request.query_params.get("data") or request.query_params.get("challenge")
    if data:
        return PlainTextResponse(content=data)
    return {"status": "ok"}


@zalo_router.get("/{tenant_id}/{bot_id}/message")
async def verify_zalo_webhook_path(request: Request):
    """Zalo verification for path-based webhook"""
    data = request.query_params.get("data") or request.query_params.get("challenge")
    if data:
        return PlainTextResponse(content=data)
    return {"status": "ok"}


@zalo_router.post("/{tenant_id}/{bot_id}/message")
async def handle_zalo_message_path(
    tenant_id: str,
    bot_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Zalo Webhook Handler (path-based: tenant_id + bot_id trong URL).
    Dùng URL này khi cấu hình webhook tại Zalo Developer.
    """
    return await _handle_zalo_payload(request, background_tasks, db, tenant_id, bot_id)


@zalo_router.post("/message")
async def handle_zalo_message(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Zalo Webhook Handler (legacy: dùng header X-Tenant-ID, X-Bot-ID).
    Hoặc fallback lấy bot đầu tiên của tenant.
    """
    tenant_id, bot_id = _extract_tenant_bot_from_path(request)
    tenant_id = tenant_id or request.headers.get("X-Tenant-ID")
    bot_id = bot_id or request.headers.get("X-Bot-ID")
    return await _handle_zalo_payload(request, background_tasks, db, tenant_id, bot_id)


async def _handle_zalo_payload(
    request: Request,
    background_tasks: BackgroundTasks,
    db,
    tenant_id: str,
    bot_id: str
):
    """Shared handler for Zalo webhook payload"""
    data = await request.json()
    
    event_name = data.get("event_name")
    if event_name != "user_send_text":
        return {"status": "ignored"}
    
    sender_id = data.get("sender", {}).get("id")
    message_text = data.get("message", {}).get("text")
    
    if not tenant_id:
        return {"status": "error", "message": "Missing tenant_id. Use path: /webhooks/zalo/{tenant_id}/{bot_id}/message"}

    from app.infrastructure.database.repositories.bot_repo import BotRepository, BotVersionRepository, ChannelConfigurationRepository
    from app.infrastructure.external.zalo_service import ZaloService
    
    bot_repo = BotRepository(db)
    bv_repo = BotVersionRepository(db)
    config_repo = ChannelConfigurationRepository(db)
    
    if not bot_id:
        # Fallback: List active bots and pick first (for MVP/Dev)
        # In Prod, we should map OA_ID -> Bot_ID
        active_bots = await bot_repo.get_active_bots(tenant_id)
        if active_bots:
            bot_id = active_bots[0].id
        else:
            return {"status": "error", "message": "No active bot found"}

    # Get Active Version
    bot_version = await bv_repo.get_active_version(bot_id, tenant_id)
    if not bot_version:
        return {"status": "error", "message": "No active bot version"}
        
    # Get Zalo Config
    channel_config = await config_repo.get_by_bot_version_and_channel(bot_version.id, "ZALO")
    
    # 3. Map Zalo user → runtime_session (session_id + ext_metadata for Monitor & reverse lookup)
    session_id = f"zalo_{sender_id}"
    ext_metadata = {
        "zalo_user_id": str(sender_id),
        "channel": "zalo",
    }
    # Optional: Zalo sender info from webhook
    sender_info = data.get("sender", {})
    if sender_info.get("name"):
        ext_metadata["display_name"] = sender_info.get("name")

    orchestrator = HybridOrchestrator(db)
    result = await orchestrator.handle_message(
        tenant_id=tenant_id,
        bot_id=bot_id,
        message=message_text,
        session_id=session_id,
        background_tasks=background_tasks,
        channel_code="zalo",
        ext_metadata=ext_metadata
    )
    
    # 4. Send Response via Zalo Service
    response_text = result.get("response", "")
    access_token = None
    if channel_config and channel_config.config:
        access_token = channel_config.config.get("access_token")

    if access_token and response_text:
        zalo_service = ZaloService()
        send_result = await zalo_service.send_message(access_token, sender_id, response_text)
        if not send_result.get("success"):
            return {"status": "error", "message": "Zalo send failed", "detail": str(send_result.get("error", ""))}

    return {"status": "success", "processed_by": result.get("metadata", {}).get("tier")}
