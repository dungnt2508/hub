"""
Admin API - FastAPI endpoints for admin dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from ..schemas.admin_config_types import (
    PatternRuleCreate,
    PatternRuleUpdate,
    PatternRuleResponse,
    KeywordHintCreate,
    KeywordHintUpdate,
    KeywordHintResponse,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    RoutingRuleResponse,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateVersion,
    ToolPermissionCreate,
    ToolPermissionUpdate,
    ToolPermissionResponse,
    GuardrailCreate,
    GuardrailUpdate,
    GuardrailResponse,
    TestSandboxRequest,
    TestSandboxResponse,
    AuditLogResponse,
)
from ..domain.admin.admin_config_service import admin_config_service
from ..domain.admin.admin_user_service import admin_user_service
from ..domain.admin.admin_auth_service import admin_auth_service
from ..interface.middleware.admin_auth import (
    get_current_admin_user,
    require_admin,
    require_admin_or_operator,
    require_any_role,
)
from ..shared.logger import logger
from ..shared.exceptions import NotFoundError, ValidationError


# Create router
router = APIRouter(prefix="/api/admin/v1", tags=["admin"])


# ==================== Pattern Rules ====================

@router.get("/pattern-rules", response_model=dict)
async def list_pattern_rules(
    tenant_id: Optional[UUID] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_any_role),
):
    """List pattern rules"""
    try:
        result = await admin_config_service.list_pattern_rules(
            tenant_id=tenant_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing pattern rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pattern-rules", response_model=PatternRuleResponse, status_code=201)
async def create_pattern_rule(
    rule: PatternRuleCreate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Create pattern rule"""
    try:
        result = await admin_config_service.create_pattern_rule(
            rule=rule,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pattern-rules/{rule_id}", response_model=PatternRuleResponse)
async def get_pattern_rule(
    rule_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Get pattern rule by ID"""
    try:
        result = await admin_config_service.get_pattern_rule(rule_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/pattern-rules/{rule_id}", response_model=PatternRuleResponse)
async def update_pattern_rule(
    rule_id: UUID,
    rule: PatternRuleUpdate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Update pattern rule"""
    try:
        result = await admin_config_service.update_pattern_rule(
            rule_id=rule_id,
            rule=rule,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pattern-rules/{rule_id}", status_code=204)
async def delete_pattern_rule(
    rule_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """Delete pattern rule"""
    try:
        await admin_config_service.delete_pattern_rule(rule_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/pattern-rules/{rule_id}/enable", response_model=PatternRuleResponse)
async def enable_pattern_rule(
    rule_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Enable pattern rule"""
    try:
        result = await admin_config_service.enable_pattern_rule(rule_id, changed_by=current_user["id"])
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error enabling pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/pattern-rules/{rule_id}/disable", response_model=PatternRuleResponse)
async def disable_pattern_rule(
    rule_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Disable pattern rule"""
    try:
        result = await admin_config_service.disable_pattern_rule(rule_id, changed_by=current_user["id"])
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error disabling pattern rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Keyword Hints ====================

@router.get("/keyword-hints", response_model=dict)
async def list_keyword_hints(
    tenant_id: Optional[UUID] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_any_role),
):
    """List keyword hints"""
    try:
        result = await admin_config_service.list_keyword_hints(
            tenant_id=tenant_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing keyword hints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keyword-hints", response_model=KeywordHintResponse, status_code=201)
async def create_keyword_hint(
    hint: KeywordHintCreate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Create keyword hint"""
    try:
        result = await admin_config_service.create_keyword_hint(
            hint=hint,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating keyword hint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keyword-hints/{hint_id}", response_model=KeywordHintResponse)
async def get_keyword_hint(
    hint_id: UUID,
    current_user: dict = Depends(require_any_role),
):
    """Get keyword hint by ID"""
    try:
        result = await admin_config_service.get_keyword_hint(hint_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting keyword hint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/keyword-hints/{hint_id}", response_model=KeywordHintResponse)
async def update_keyword_hint(
    hint_id: UUID,
    hint: KeywordHintUpdate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Update keyword hint"""
    try:
        result = await admin_config_service.update_keyword_hint(
            hint_id=hint_id,
            hint=hint,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating keyword hint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keyword-hints/{hint_id}", status_code=204)
async def delete_keyword_hint(
    hint_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """Delete keyword hint"""
    try:
        await admin_config_service.delete_keyword_hint(hint_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting keyword hint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Test Sandbox ====================

@router.post("/test-sandbox", response_model=TestSandboxResponse)
async def test_sandbox(
    request: TestSandboxRequest,
    current_user: dict = Depends(require_any_role),
):
    """Test routing with trace"""
    try:
        from ..router.orchestrator import RouterOrchestrator
        from ..schemas.router_types import RouterRequest
        
        # Create router request
        router_request = RouterRequest(
            raw_message=request.message,
            user_id=str(current_user["id"]),  # Use admin user ID
            session_id=None,
            metadata={
                "tenant_id": str(request.tenant_id) if request.tenant_id else None,
                **(request.user_context or {}),
            },
        )
        
        # Run router
        orchestrator = RouterOrchestrator()
        router_response = await orchestrator.route(router_request)
        
        # Get configs used (from trace)
        configs_used = []
        if router_response.trace:
            for span in router_response.trace.spans:
                if span.get("decision_source"):
                    configs_used.append({
                        "step": span.get("step"),
                        "source": span.get("decision_source"),
                        "score": span.get("score"),
                    })
        
        return TestSandboxResponse(
            routing_result={
                "domain": router_response.domain,
                "intent": router_response.intent,
                "intent_type": router_response.intent_type,
                "confidence": router_response.confidence,
                "source": router_response.source,
                "status": router_response.status,
            },
            trace={
                "trace_id": router_response.trace_id,
                "spans": [
                    {
                        "step": span.get("step"),
                        "input": span.get("input"),
                        "output": span.get("output"),
                        "duration_ms": span.get("duration_ms"),
                        "score": span.get("score"),
                        "decision_source": span.get("decision_source"),
                    }
                    for span in (router_response.trace.spans if router_response.trace else [])
                ],
            },
            configs_used=configs_used,
        )
    except Exception as e:
        logger.error(f"Error in test sandbox: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Routing Rules ====================

@router.get("/routing-rules", response_model=dict)
async def list_routing_rules(
    tenant_id: Optional[UUID] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_any_role),
):
    """List routing rules"""
    try:
        result = await admin_config_service.list_routing_rules(
            tenant_id=tenant_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing routing rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing-rules", response_model=RoutingRuleResponse, status_code=201)
async def create_routing_rule(
    rule: RoutingRuleCreate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Create routing rule"""
    try:
        result = await admin_config_service.create_routing_rule(
            rule=rule,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing-rules/{rule_id}", response_model=RoutingRuleResponse)
async def get_routing_rule(
    rule_id: UUID,
    current_user: dict = Depends(require_any_role),
):
    """Get routing rule by ID"""
    try:
        result = await admin_config_service.get_routing_rule(rule_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/routing-rules/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: UUID,
    rule: RoutingRuleUpdate,
    current_user: dict = Depends(require_admin_or_operator),
):
    """Update routing rule"""
    try:
        result = await admin_config_service.update_routing_rule(
            rule_id=rule_id,
            rule=rule,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/routing-rules/{rule_id}", status_code=204)
async def delete_routing_rule(
    rule_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """Delete routing rule"""
    try:
        await admin_config_service.delete_routing_rule(rule_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Prompt Templates ====================

@router.get("/prompt-templates", response_model=dict)
async def list_prompt_templates(
    tenant_id: Optional[UUID] = Query(None),
    template_type: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin_user),
):
    """List prompt templates"""
    try:
        result = await admin_config_service.list_prompt_templates(
            tenant_id=tenant_id,
            template_type=template_type,
            domain=domain,
            agent=agent,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing prompt templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt-templates", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    template: PromptTemplateCreate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Create prompt template"""
    try:
        result = await admin_config_service.create_prompt_template(
            template=template,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating prompt template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Get prompt template by ID"""
    try:
        result = await admin_config_service.get_prompt_template(template_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting prompt template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: UUID,
    template: PromptTemplateUpdate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Update prompt template (creates new version)"""
    try:
        result = await admin_config_service.update_prompt_template(
            template_id=template_id,
            template=template,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating prompt template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompt-templates/{template_id}/versions", response_model=List[PromptTemplateVersion])
async def list_template_versions(
    template_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """List all versions of a template"""
    try:
        result = await admin_config_service.list_template_versions(template_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing template versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt-templates/{template_id}/rollback", response_model=PromptTemplateResponse)
async def rollback_template_version(
    template_id: UUID,
    target_version: int = Query(..., description="Version number to rollback to"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Rollback template to a previous version"""
    try:
        result = await admin_config_service.rollback_template_version(
            template_id=template_id,
            target_version=target_version,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rolling back template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompt-templates/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete prompt template (all versions)"""
    try:
        await admin_config_service.delete_prompt_template(template_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting prompt template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Tool Permissions ====================

@router.get("/tool-permissions", response_model=dict)
async def list_tool_permissions(
    tenant_id: Optional[UUID] = Query(None),
    agent_name: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin_user),
):
    """List tool permissions"""
    try:
        result = await admin_config_service.list_tool_permissions(
            tenant_id=tenant_id,
            agent_name=agent_name,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing tool permissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tool-permissions", response_model=ToolPermissionResponse, status_code=201)
async def create_tool_permission(
    permission: ToolPermissionCreate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Create tool permission"""
    try:
        result = await admin_config_service.create_tool_permission(
            permission=permission,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tool permission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tool-permissions/{permission_id}", response_model=ToolPermissionResponse)
async def get_tool_permission(
    permission_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Get tool permission by ID"""
    try:
        result = await admin_config_service.get_tool_permission(permission_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tool permission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tool-permissions/{permission_id}", response_model=ToolPermissionResponse)
async def update_tool_permission(
    permission_id: UUID,
    permission: ToolPermissionUpdate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Update tool permission"""
    try:
        result = await admin_config_service.update_tool_permission(
            permission_id=permission_id,
            permission=permission,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tool permission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tool-permissions/{permission_id}", status_code=204)
async def delete_tool_permission(
    permission_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete tool permission"""
    try:
        await admin_config_service.delete_tool_permission(permission_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tool permission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Guardrails ====================

@router.get("/guardrails", response_model=dict)
async def list_guardrails(
    tenant_id: Optional[UUID] = Query(None),
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin_user),
):
    """List guardrails"""
    try:
        result = await admin_config_service.list_guardrails(
            tenant_id=tenant_id,
            rule_type=rule_type,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing guardrails: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardrails", response_model=GuardrailResponse, status_code=201)
async def create_guardrail(
    guardrail: GuardrailCreate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Create guardrail"""
    try:
        result = await admin_config_service.create_guardrail(
            guardrail=guardrail,
            created_by=current_user["id"],
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating guardrail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/{guardrail_id}", response_model=GuardrailResponse)
async def get_guardrail(
    guardrail_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Get guardrail by ID"""
    try:
        result = await admin_config_service.get_guardrail(guardrail_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting guardrail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/guardrails/{guardrail_id}", response_model=GuardrailResponse)
async def update_guardrail(
    guardrail_id: UUID,
    guardrail: GuardrailUpdate,
    current_user: dict = Depends(get_current_admin_user),
):
    """Update guardrail"""
    try:
        result = await admin_config_service.update_guardrail(
            guardrail_id=guardrail_id,
            guardrail=guardrail,
            updated_by=current_user["id"],
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating guardrail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/guardrails/{guardrail_id}", status_code=204)
async def delete_guardrail(
    guardrail_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete guardrail"""
    try:
        await admin_config_service.delete_guardrail(guardrail_id, changed_by=current_user["id"])
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting guardrail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Authentication ====================

class LoginRequest(BaseModel):
    """Login request"""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    user: Dict[str, Any]
    token: str
    expires_in: int


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get JWT token"""
    try:
        result = await admin_auth_service.login(request.email, request.password)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in login: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.get("/auth/me", response_model=dict)
async def get_current_user(
    current_user: dict = Depends(get_current_admin_user),
):
    """Get current authenticated user"""
    return current_user


# ==================== Admin Users ====================

class AdminUserCreate(BaseModel):
    """Create admin user request"""
    email: str
    password: str
    role: str  # 'admin' | 'operator' | 'viewer'
    tenant_id: Optional[UUID] = None
    permissions: Optional[Dict[str, Any]] = None


class AdminUserUpdate(BaseModel):
    """Update admin user request"""
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


@router.get("/admin-users", response_model=dict)
async def list_admin_users(
    tenant_id: Optional[UUID] = Query(None),
    role: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin),
):
    """List admin users (admin only)"""
    try:
        result = await admin_user_service.list_admin_users(
            tenant_id=tenant_id,
            role=role,
            active=active,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing admin users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin-users", response_model=dict, status_code=201)
async def create_admin_user(
    user: AdminUserCreate,
    current_user: dict = Depends(require_admin),
):
    """Create admin user (admin only)"""
    try:
        result = await admin_user_service.create_admin_user(
            email=user.email,
            password=user.password,
            role=user.role,
            tenant_id=user.tenant_id,
            permissions=user.permissions,
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating admin user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin-users/{user_id}", response_model=dict)
async def get_admin_user(
    user_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """Get admin user by ID (admin only)"""
    try:
        result = await admin_user_service.get_admin_user(user_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting admin user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin-users/{user_id}", response_model=dict)
async def update_admin_user(
    user_id: UUID,
    user: AdminUserUpdate,
    current_user: dict = Depends(require_admin),
):
    """Update admin user (admin only)"""
    try:
        result = await admin_user_service.update_admin_user(
            user_id=user_id,
            email=user.email,
            password=user.password,
            role=user.role,
            permissions=user.permissions,
            active=user.active,
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating admin user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin-users/{user_id}", status_code=204)
async def delete_admin_user(
    user_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """Delete admin user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        await admin_user_service.delete_admin_user(user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting admin user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Audit Logs ====================

@router.get("/audit-logs", response_model=dict)
async def list_audit_logs(
    tenant_id: Optional[UUID] = Query(None),
    config_type: Optional[str] = Query(None),
    config_id: Optional[UUID] = Query(None),
    changed_by: Optional[UUID] = Query(None),
    start_date: Optional[str] = Query(None, description="ISO format datetime"),
    end_date: Optional[str] = Query(None, description="ISO format datetime"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin_user),
):
    """List audit logs"""
    try:
        from datetime import datetime
        
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
        
        from ..domain.admin.audit_log_service import audit_log_service
        
        result = await audit_log_service.list_audit_logs(
            tenant_id=tenant_id,
            config_type=config_type,
            config_id=config_id,
            changed_by=changed_by,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Use Cases Discovery ====================

@router.get("/use-cases", response_model=dict)
async def list_use_cases(
    domain: Optional[str] = Query(None, description="Filter by domain name"),
    current_user: dict = Depends(get_current_admin_user),
):
    """
    List available use cases (intents) across all domains.
    
    This helps frontend show available intents when creating routing rules,
    pattern rules, or keyword hints.
    """
    try:
        from ..domain.use_case_registry import use_case_registry
        
        if domain:
            # Get specific domain
            domain_data = use_case_registry.get_domain(domain)
            if not domain_data:
                raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")
            
            return {
                "domain": domain_data,
                "intents": domain_data.get("intents", []),
            }
        else:
            # Get all domains and intents
            domains = use_case_registry.get_all_domains()
            all_intents = use_case_registry.get_all_intents()
            
            return {
                "domains": domains,
                "intents": all_intents,
                "total_domains": len(domains),
                "total_intents": len(all_intents),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing use cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing-rules/suggestions", response_model=dict)
async def get_routing_rule_suggestions(
    current_user: dict = Depends(get_current_admin_user),
):
    """
    Get suggestions for routing rule names based on existing routing rules.
    
    This helps frontend suggest rule names when creating pattern rules or keyword hints.
    """
    try:
        # Get all routing rules
        routing_rules = await admin_config_service.list_routing_rules(
            limit=100,
            offset=0,
        )
        
        # Extract rule names and intents
        suggestions = []
        for rule in routing_rules.get("items", []):
            intent_pattern = rule.get("intent_pattern", {})
            intent = intent_pattern.get("intent")
            
            if intent:
                suggestions.append({
                    "rule_name": rule.get("rule_name"),
                    "intent": intent,
                    "target_domain": rule.get("target_domain"),
                    "id": str(rule.get("id")),
                })
        
        return {
            "suggestions": suggestions,
            "total": len(suggestions),
        }
    except Exception as e:
        logger.error(f"Error getting routing rule suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
