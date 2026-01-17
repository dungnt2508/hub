"""Pydantic schemas for API request/response"""
from backend.schemas.bot import QueryRequest, QueryResponse
from backend.schemas.admin import (
    TenantResponse,
    ChannelResponse,
    ProductResponse,
    ProductDetailResponse,
    IntentResponse,
    IntentDetailResponse,
    MigrationJobResponse,
    ConversationLogResponse,
    FailedQueryResponse,
)

__all__ = [
    "QueryRequest",
    "QueryResponse",
    "TenantResponse",
    "ChannelResponse",
    "ProductResponse",
    "ProductDetailResponse",
    "IntentResponse",
    "IntentDetailResponse",
    "MigrationJobResponse",
    "ConversationLogResponse",
    "FailedQueryResponse",
]
