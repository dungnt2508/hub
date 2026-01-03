"""
Admin Config Types - Pydantic schemas for config domains
"""
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# ==================== Base Types ====================

class ConfigBase(BaseModel):
    """Base config with common fields"""
    tenant_id: Optional[UUID] = None
    rule_name: str
    enabled: bool = True
    description: Optional[str] = None
    scope: Literal["global", "per_bot", "per_user_group"] = "global"
    scope_filter: Optional[Dict[str, Any]] = None


# ==================== Routing Rules ====================

class RoutingRuleCreate(ConfigBase):
    """Create routing rule request"""
    intent_pattern: Dict[str, Any] = Field(..., description="Intent matching pattern")
    target_domain: Optional[str] = None
    target_agent: Optional[str] = None
    target_workflow: Optional[Dict[str, Any]] = None
    priority: int = Field(0, ge=0, le=100)
    fallback_chain: Optional[List[Dict[str, Any]]] = None


class RoutingRuleUpdate(BaseModel):
    """Update routing rule request"""
    rule_name: Optional[str] = None
    enabled: Optional[bool] = None
    intent_pattern: Optional[Dict[str, Any]] = None
    target_domain: Optional[str] = None
    target_agent: Optional[str] = None
    target_workflow: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    fallback_chain: Optional[List[Dict[str, Any]]] = None
    scope: Optional[Literal["global", "per_bot", "per_user_group"]] = None
    scope_filter: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class RoutingRuleResponse(ConfigBase):
    """Routing rule response"""
    id: UUID
    target_domain: Optional[str]
    target_agent: Optional[str]
    target_workflow: Optional[Dict[str, Any]]
    priority: int
    fallback_chain: Optional[List[Dict[str, Any]]]
    intent_pattern: Dict[str, Any]
    version: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Pattern Rules ====================

class PatternRuleCreate(ConfigBase):
    """Create pattern rule request"""
    pattern_regex: str = Field(..., description="Regex pattern")
    pattern_flags: str = Field("IGNORECASE", description="Regex flags")
    target_domain: str
    target_intent: Optional[str] = None
    intent_type: Optional[Literal["OPERATION", "KNOWLEDGE"]] = None
    slots_extraction: Optional[Dict[str, str]] = None
    priority: int = Field(0, ge=0, le=100)


class PatternRuleUpdate(BaseModel):
    """Update pattern rule request"""
    rule_name: Optional[str] = None
    enabled: Optional[bool] = None
    pattern_regex: Optional[str] = None
    pattern_flags: Optional[str] = None
    target_domain: Optional[str] = None
    target_intent: Optional[str] = None
    intent_type: Optional[Literal["OPERATION", "KNOWLEDGE"]] = None
    slots_extraction: Optional[Dict[str, str]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    scope: Optional[Literal["global", "per_bot", "per_user_group"]] = None
    scope_filter: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class PatternRuleResponse(ConfigBase):
    """Pattern rule response"""
    id: UUID
    pattern_regex: str
    pattern_flags: str
    target_domain: str
    target_intent: Optional[str]
    intent_type: Optional[str]
    slots_extraction: Optional[Dict[str, str]]
    priority: int
    version: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Keyword Hints ====================

class KeywordHintCreate(ConfigBase):
    """Create keyword hint request"""
    domain: str
    keywords: Dict[str, float] = Field(..., description="Keyword -> weight mapping")


class KeywordHintUpdate(BaseModel):
    """Update keyword hint request"""
    rule_name: Optional[str] = None
    enabled: Optional[bool] = None
    domain: Optional[str] = None
    keywords: Optional[Dict[str, float]] = None
    scope: Optional[Literal["global", "per_bot", "per_user_group"]] = None
    scope_filter: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class KeywordHintResponse(ConfigBase):
    """Keyword hint response"""
    id: UUID
    domain: str
    keywords: Dict[str, float]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Prompt Templates ====================

class PromptTemplateCreate(ConfigBase):
    """Create prompt template request"""
    template_name: str
    template_type: Literal["system", "agent", "tool", "rag"]
    domain: Optional[str] = None
    agent: Optional[str] = None
    template_text: str = Field(..., description="Jinja2 template text")
    variables: Optional[Dict[str, Any]] = None


class PromptTemplateUpdate(BaseModel):
    """Update prompt template request"""
    template_name: Optional[str] = None
    enabled: Optional[bool] = None
    template_text: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class PromptTemplateResponse(ConfigBase):
    """Prompt template response"""
    id: UUID
    template_name: str
    template_type: str
    domain: Optional[str]
    agent: Optional[str]
    template_text: str
    variables: Optional[Dict[str, Any]]
    version: int
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptTemplateVersion(BaseModel):
    """Prompt template version"""
    version: int
    template_text: str
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID]


# ==================== Tool Permissions ====================

class ToolPermissionCreate(BaseModel):
    """Create tool permission request"""
    tenant_id: Optional[UUID] = None
    agent_name: str
    tool_name: str
    enabled: bool = True
    allowed_contexts: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    required_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ToolPermissionUpdate(BaseModel):
    """Update tool permission request"""
    enabled: Optional[bool] = None
    allowed_contexts: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    required_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ToolPermissionResponse(BaseModel):
    """Tool permission response"""
    id: UUID
    tenant_id: Optional[UUID]
    agent_name: str
    tool_name: str
    enabled: bool
    allowed_contexts: Optional[List[str]]
    rate_limit: Optional[int]
    required_params: Optional[Dict[str, Any]]
    description: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Guardrails ====================

class GuardrailCreate(ConfigBase):
    """Create guardrail request"""
    rule_type: Literal["hard", "soft"]
    trigger_condition: Dict[str, Any] = Field(..., description="Condition to trigger rule")
    action: Literal["block", "redirect", "flag", "require_confirmation"]
    action_params: Optional[Dict[str, Any]] = None
    priority: int = Field(0, ge=0, le=100)


class GuardrailUpdate(BaseModel):
    """Update guardrail request"""
    rule_name: Optional[str] = None
    enabled: Optional[bool] = None
    rule_type: Optional[Literal["hard", "soft"]] = None
    trigger_condition: Optional[Dict[str, Any]] = None
    action: Optional[Literal["block", "redirect", "flag", "require_confirmation"]] = None
    action_params: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    scope: Optional[Literal["global", "per_bot", "per_user_group"]] = None
    scope_filter: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class GuardrailResponse(ConfigBase):
    """Guardrail response"""
    id: UUID
    rule_type: str
    trigger_condition: Dict[str, Any]
    action: str
    action_params: Optional[Dict[str, Any]]
    priority: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Audit Logs ====================

class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: UUID
    tenant_id: Optional[UUID]
    config_type: str
    config_id: UUID
    config_name: Optional[str]
    changed_by: UUID
    changed_by_email: Optional[str]
    action: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    diff: Optional[Dict[str, Any]]
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True


# ==================== Test Sandbox ====================

class TestSandboxRequest(BaseModel):
    """Test sandbox request"""
    message: str
    tenant_id: Optional[UUID] = None
    user_context: Optional[Dict[str, Any]] = None


class TestSandboxResponse(BaseModel):
    """Test sandbox response"""
    routing_result: Dict[str, Any]
    trace: Dict[str, Any]
    configs_used: List[Dict[str, Any]]


# ==================== Admin Users ====================

class AdminUserCreate(BaseModel):
    """Create admin user request"""
    email: str
    password: str
    role: Literal["admin", "operator", "viewer"]
    tenant_id: Optional[UUID] = None
    permissions: Optional[Dict[str, Any]] = None


class AdminUserResponse(BaseModel):
    """Admin user response"""
    id: UUID
    email: str
    role: str
    tenant_id: Optional[UUID]
    permissions: Dict[str, Any]
    active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

