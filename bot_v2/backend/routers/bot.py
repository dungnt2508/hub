"""Bot API router - public endpoints for chatbot"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.bot_service import BotService
from backend.schemas.bot import QueryRequest, QueryResponse

router = APIRouter(prefix="/bot", tags=["bot"])


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> UUID:
    """Extract tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="Missing X-Tenant-ID header")
    
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Process user query.
    
    This is the main endpoint for chatbot queries.
    """
    bot_service = BotService(db)
    
    channel_id = None
    if request.channel_id:
        try:
            channel_id = UUID(request.channel_id)
        except ValueError:
            pass
    
    result = await bot_service.process_query(
        tenant_id=tenant_id,
        channel_id=channel_id,
        query_text=request.query
    )
    
    return QueryResponse(
        success=result.get("success", False),
        message=result.get("message"),
        intent=result.get("intent"),
        domain=result.get("domain"),
        answer=result.get("action", {}).get("answer"),
        disclaimers=result.get("disclaimers")
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
