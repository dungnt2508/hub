"""Admin API schemas"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TenantResponse(BaseModel):
    """Tenant response"""
    id: UUID
    name: str
    status: str
    plan: Optional[str] = None
    settings_version: int
    created_at: datetime
    updated_at: datetime


class ChannelResponse(BaseModel):
    """Channel response"""
    id: UUID
    tenant_id: UUID
    type: str
    enabled: bool
    config_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class ProductResponse(BaseModel):
    """Product response"""
    id: UUID
    tenant_id: UUID
    sku: str
    slug: str
    name: str
    category: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ProductAttributeResponse(BaseModel):
    """Product attribute response"""
    id: UUID
    attributes_key: str
    attributes_value: str
    attributes_value_type: str


class UseCaseResponse(BaseModel):
    """Use case response"""
    id: UUID
    type: str
    description: str


class FAQResponse(BaseModel):
    """FAQ response"""
    id: UUID
    scope: str
    product_id: Optional[UUID] = None
    question: str
    answer: str


class ProductDetailResponse(BaseModel):
    """Product detail response"""
    product: ProductResponse
    attributes: List[ProductAttributeResponse]
    use_cases: List[UseCaseResponse]
    faqs: List[FAQResponse]


class IntentResponse(BaseModel):
    """Intent response"""
    id: UUID
    tenant_id: UUID
    name: str
    domain: str
    priority: int
    created_at: datetime
    updated_at: datetime


class IntentPatternResponse(BaseModel):
    """Intent pattern response"""
    id: UUID
    type: str
    pattern: str
    weight: float


class IntentHintResponse(BaseModel):
    """Intent hint response"""
    id: UUID
    hint_text: str


class IntentActionResponse(BaseModel):
    """Intent action response"""
    id: UUID
    action_type: str
    config_json: Optional[dict] = None
    priority: int


class IntentDetailResponse(BaseModel):
    """Intent detail response"""
    intent: IntentResponse
    patterns: List[IntentPatternResponse]
    hints: List[IntentHintResponse]
    actions: List[IntentActionResponse]


class MigrationJobResponse(BaseModel):
    """Migration job response"""
    id: UUID
    tenant_id: UUID
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class ConversationLogResponse(BaseModel):
    """Conversation log response"""
    id: UUID
    tenant_id: UUID
    channel_id: Optional[UUID] = None
    intent: Optional[str] = None
    domain: Optional[str] = None
    success: bool
    created_at: datetime


class FailedQueryResponse(BaseModel):
    """Failed query response"""
    id: UUID
    tenant_id: UUID
    query: str
    reason: Optional[str] = None
    created_at: datetime
