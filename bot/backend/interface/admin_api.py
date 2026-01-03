"""
Admin API - FastAPI endpoints for admin dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
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
)
from ..domain.admin.admin_config_service import admin_config_service
from ..shared.logger import logger
from ..shared.exceptions import NotFoundError, ValidationError


# Create router
router = APIRouter(prefix="/api/admin/v1", tags=["admin"])


# ==================== Authentication Dependency ====================
# TODO: Implement proper RBAC authentication
async def get_current_admin_user() -> dict:
    """
    Get current admin user from JWT token.
    Placeholder - implement proper authentication.
    """
    # For now, return a mock admin user
    return {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "email": "admin@example.com",
        "role": "admin",
        "tenant_id": None,
    }


# ==================== Pattern Rules ====================

@router.get("/pattern-rules", response_model=dict)
async def list_pattern_rules(
    tenant_id: Optional[UUID] = Query(None),
    enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete pattern rule"""
    try:
        await admin_config_service.delete_pattern_rule(rule_id)
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
        result = await admin_config_service.enable_pattern_rule(rule_id)
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
        result = await admin_config_service.disable_pattern_rule(rule_id)
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete keyword hint"""
    try:
        await admin_config_service.delete_keyword_hint(hint_id)
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
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
    current_user: dict = Depends(get_current_admin_user),
):
    """Delete routing rule"""
    try:
        await admin_config_service.delete_routing_rule(rule_id)
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
        await admin_config_service.delete_prompt_template(template_id)
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
        await admin_config_service.delete_tool_permission(permission_id)
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
        await admin_config_service.delete_guardrail(guardrail_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting guardrail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

