"""Admin API request schemas"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# Tenant Requests
class TenantCreateRequest(BaseModel):
    """Create tenant request"""
    name: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="active", pattern="^(active|inactive|suspended)$")
    plan: Optional[str] = None


class TenantUpdateRequest(BaseModel):
    """Update tenant request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    plan: Optional[str] = None


# Channel Requests
class ChannelCreateRequest(BaseModel):
    """Create channel request"""
    type: str = Field(..., min_length=1, max_length=100)
    enabled: bool = Field(default=True)
    config_json: Optional[Dict[str, Any]] = None


class ChannelUpdateRequest(BaseModel):
    """Update channel request"""
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    enabled: Optional[bool] = None
    config_json: Optional[Dict[str, Any]] = None


# Product Requests
class ProductCreateRequest(BaseModel):
    """Create product request"""
    sku: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")


class ProductUpdateRequest(BaseModel):
    """Update product request"""
    sku: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|archived)$")


class ProductAttributeCreateRequest(BaseModel):
    """Create product attribute request"""
    attributes_key: str = Field(..., min_length=1, max_length=255)
    attributes_value: str
    attributes_value_type: str = Field(default="string", pattern="^(string|number|boolean|json)$")


class ProductAttributeUpdateRequest(BaseModel):
    """Update product attribute request"""
    attributes_key: Optional[str] = Field(None, min_length=1, max_length=255)
    attributes_value: Optional[str] = None
    attributes_value_type: Optional[str] = Field(None, pattern="^(string|number|boolean|json)$")


class UseCaseCreateRequest(BaseModel):
    """Create use case request"""
    type: str = Field(..., pattern="^(allowed|disallowed|unknown)$")
    description: str = Field(..., min_length=1)


class UseCaseUpdateRequest(BaseModel):
    """Update use case request"""
    type: Optional[str] = Field(None, pattern="^(allowed|disallowed|unknown)$")
    description: Optional[str] = Field(None, min_length=1)


class FAQCreateRequest(BaseModel):
    """Create FAQ request"""
    scope: str = Field(..., pattern="^(global|product)$")
    product_id: Optional[UUID] = None
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class FAQUpdateRequest(BaseModel):
    """Update FAQ request"""
    scope: Optional[str] = Field(None, pattern="^(global|product)$")
    product_id: Optional[UUID] = None
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)


# Intent Requests
class IntentCreateRequest(BaseModel):
    """Create intent request"""
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(default=0, ge=0)


class IntentUpdateRequest(BaseModel):
    """Update intent request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, min_length=1, max_length=100)
    priority: Optional[int] = Field(None, ge=0)


class IntentPatternCreateRequest(BaseModel):
    """Create intent pattern request"""
    type: str = Field(..., pattern="^(keyword|phrase|regex)$")
    pattern: str = Field(..., min_length=1)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class IntentPatternUpdateRequest(BaseModel):
    """Update intent pattern request"""
    type: Optional[str] = Field(None, pattern="^(keyword|phrase|regex)$")
    pattern: Optional[str] = Field(None, min_length=1)
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)


class IntentHintCreateRequest(BaseModel):
    """Create intent hint request"""
    hint_text: str = Field(..., min_length=1)


class IntentHintUpdateRequest(BaseModel):
    """Update intent hint request"""
    hint_text: Optional[str] = Field(None, min_length=1)


class IntentActionCreateRequest(BaseModel):
    """Create intent action request"""
    action_type: str = Field(..., pattern="^(query_db|handoff|refuse|rag)$")
    config_json: Optional[Dict[str, Any]] = None
    priority: int = Field(default=0, ge=0)


class IntentActionUpdateRequest(BaseModel):
    """Update intent action request"""
    action_type: Optional[str] = Field(None, pattern="^(query_db|handoff|refuse|rag)$")
    config_json: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0)
