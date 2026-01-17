"""Bot API schemas"""
from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    channel_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model"""
    success: bool
    message: Optional[str] = None
    intent: Optional[str] = None
    domain: Optional[str] = None
    answer: Optional[dict] = None
    disclaimers: Optional[list] = None
