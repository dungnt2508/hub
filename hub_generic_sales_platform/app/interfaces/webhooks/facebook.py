from fastapi import APIRouter, Request, BackgroundTasks, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.engine import get_session
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator

fb_router = APIRouter(prefix="/webhooks/facebook", tags=["webhooks"])

@fb_router.get("/message")
async def verify_fb_webhook(request: Request):
    """Facebook Webhook verification (GET challenge)"""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Check if mode and token are correct
    if mode == "subscribe" and token == "your_verify_token":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=challenge)
    return {"status": "error", "message": "Verification failed"}

@fb_router.post("/message")
async def handle_fb_message(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Facebook Messenger Webhook Handler
    """
    data = await request.json()
    
    # 1. Parse FB Payload
    if data.get("object") != "page":
        return {"status": "not a page"}
    
    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if messaging_event.get("message"):
                sender_id = messaging_event["sender"]["id"]
                message_text = messaging_event["message"].get("text")
                
                if not message_text:
                    continue

                # 2. Resolve Bot and Config
                bot_id = request.headers.get("X-Bot-ID")
                tenant_id = request.headers.get("X-Tenant-ID", "default_tenant")
                
                from app.infrastructure.database.repositories.bot_repo import BotRepository, BotVersionRepository, ChannelConfigurationRepository
                from app.infrastructure.external.facebook_service import FacebookService
                
                bot_repo = BotRepository(db)
                bv_repo = BotVersionRepository(db)
                config_repo = ChannelConfigurationRepository(db)
                
                if not bot_id:
                    # Fallback logic for MVP
                    active_bots = await bot_repo.get_active_bots(tenant_id)
                    if active_bots:
                        bot_id = active_bots[0].id
                    else:
                        continue # Cannot process without bot

                # Get Active Version
                bot_version = await bv_repo.get_active_version(bot_id, tenant_id)
                if not bot_version:
                    continue
                    
                # Get FB Config
                channel_config = await config_repo.get_by_bot_version_and_channel(bot_version.id, "FACEBOOK")

                # 3. Call Hybrid Orchestrator
                orchestrator = HybridOrchestrator(db)
                result = await orchestrator.handle_message(
                    tenant_id=tenant_id,
                    bot_id=bot_id,
                    message=message_text,
                    session_id=f"fb_{sender_id}",
                    background_tasks=background_tasks
                )
                
                # 4. Send Response via FB Service
                if channel_config and channel_config.config:
                    page_access_token = channel_config.config.get("page_access_token")
                    if page_access_token:
                        fb_service = FacebookService()
                        response_text = result.get("response", "")
                        
                        if response_text:
                            await fb_service.send_message(page_access_token, sender_id, response_text)
                
    return {"status": "success"}
