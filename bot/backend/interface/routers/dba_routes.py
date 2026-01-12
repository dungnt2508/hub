"""
DBA API Routes - Endpoints for DBA dashboard and operations
"""
from fastapi import APIRouter, Query, Depends, HTTPException, Body, Request
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

import os
from ...domain.dba.services.alerting_service import dba_alerting_service, AlertStatus
from ...domain.dba.services.metrics_history_service import dba_metrics_history_service
from ...domain.dba.risk_assessment_service import dba_risk_assessment_service
from ...domain.dba.services.risk_cache_service import risk_cache_service
from ...domain.dba.use_case_metadata import dba_use_case_metadata_registry
# Import definitions to ensure metadata is registered on module load
from ...domain.dba import use_case_metadata_definitions  # noqa: F401
from ...shared.logger import logger

router = APIRouter(prefix="/api/dba", tags=["dba"])


# ============================================================
# DBA USE CASES ENDPOINT
# ============================================================

@router.get("/use-cases")
async def get_dba_use_cases():
    """
    Get available DBA use cases for sandbox selection.
    
    Returns list of playbooks user can select.
    Uses metadata registry as single source of truth.
    """
    # Load from metadata registry
    all_metadata = dba_use_case_metadata_registry.get_all()
    logger.info(f"📋 Fetching DBA use cases. Found {len(all_metadata)} registered use cases")
    use_cases = [metadata.to_dict() for metadata in all_metadata]

    return {
        "status": "success",
        "total": len(use_cases),
        "use_cases": use_cases,
    }


@router.get("/use-cases/{use_case_id}")
async def get_dba_use_case_detail(use_case_id: str):
    """
    Get detailed metadata for a specific use case.
    
    Returns full metadata including schemas for frontend rendering.
    """
    metadata = dba_use_case_metadata_registry.get(use_case_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Use case not found: {use_case_id}")
    
    # Get query templates for this use case (if playbook exists)
    query_templates_info = None
    if metadata.playbook_name:
        try:
            from ...infrastructure.dba_query_template_repository import dba_query_template_repository
            
            # Get templates for all supported DB types
            db_types = ["sqlserver", "postgresql", "mysql"]
            templates_by_db = {}
            
            for db_type in db_types:
                templates = await dba_query_template_repository.get_templates_by_playbook(
                    playbook_name=metadata.playbook_name,
                    db_type=db_type,
                    active_only=True
                )
                if templates:
                    templates_by_db[db_type] = [
                        {
                            "step_number": t["step_number"],
                            "purpose": t["purpose"],
                            "read_only": t["read_only"],
                            "description": t.get("description"),
                        }
                        for t in templates
                    ]
            
            if templates_by_db:
                # Always include query_text for review (user needs to see SQL)
                for db_type in db_types:
                    templates = await dba_query_template_repository.get_templates_by_playbook(
                        playbook_name=metadata.playbook_name,
                        db_type=db_type,
                        active_only=True
                    )
                    if templates and db_type in templates_by_db:
                        # Merge query_text into templates
                        for idx, template_info in enumerate(templates_by_db[db_type]):
                            matching_template = next(
                                (t for t in templates if str(t["step_number"]) == str(template_info["step_number"])),
                                None
                            )
                            if matching_template:
                                templates_by_db[db_type][idx]["query_text"] = matching_template["query_text"]
                
                query_templates_info = {
                    "playbook_name": metadata.playbook_name,
                    "templates_by_db": templates_by_db,
                }
        except Exception as e:
            logger.warning(f"Error loading query templates for use case {use_case_id}: {e}")
    
    result = metadata.to_dict()
    if query_templates_info:
        result["query_templates"] = query_templates_info
    
    return {
        "status": "success",
        "use_case": result,
    }





# ============================================================
# SCHEMAS FOR RISK SIMULATION
# ============================================================
class GateCheck(BaseModel):
    gate_name: str
    status: str  # PASS, BLOCK, WARN
    reason: str


class ExecutionStep(BaseModel):
    step: str
    result: str  # pass, fail, warn
    duration_ms: int


class ExecutionTrace(BaseModel):
    timestamp: str
    duration_ms: int
    steps: List[ExecutionStep]


class RiskAssessmentResult(BaseModel):
    """Risk assessment result from DBA bot"""
    final_decision: str  # GO or NO-GO
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    gates: List[GateCheck]
    critical_issues: List[str] = []
    warnings: List[str] = []
    checks_passed: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    trace: ExecutionTrace


@router.get("/alerts")
async def get_alerts(
    connection_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
):
    """
    Get DBA alerts.
    
    Query Parameters:
    - connection_id: Optional UUID to filter by connection
    - limit: Maximum number of alerts (1-1000, default 100)
    - status: Filter by status (ACTIVE, ACKNOWLEDGED, RESOLVED)
    """
    try:
        conn_id = None
        if connection_id:
            try:
                conn_id = UUID(connection_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid connection_id format")
        
        alerts = await dba_alerting_service.get_active_alerts(
            connection_id=conn_id,
            limit=limit
        )
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "connection_filter": connection_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/metrics")
async def get_metrics(
    connection_id: Optional[str] = Query(None),
    metric_type: str = Query("query_performance"),
    limit: int = Query(100, ge=1, le=1000),
    days: int = Query(7, ge=1, le=90),
):
    """
    Get DBA metrics.
    
    Query Parameters:
    - connection_id: Optional UUID to filter by connection
    - metric_type: Type of metric (query_performance, wait_statistics, etc.)
    - limit: Maximum number of metrics (1-1000, default 100)
    - days: Look back period in days (1-90, default 7)
    """
    try:
        if not connection_id:
            raise HTTPException(status_code=400, detail="connection_id is required")
        
        try:
            conn_id = UUID(connection_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid connection_id format")
        
        metrics = await dba_metrics_history_service.get_recent_metrics(
            connection_id=conn_id,
            metric_type=metric_type,
            limit=limit,
            days=days,
        )
        
        return {
            "metrics": metrics,
            "count": len(metrics),
            "metric_type": metric_type,
            "period_days": days,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: Optional[str] = Query(None),
    note: Optional[str] = Query(None),
):
    """
    Acknowledge an alert.
    
    Path Parameters:
    - alert_id: UUID of the alert
    
    Query Parameters:
    - acknowledged_by: User who acknowledged (optional)
    - note: Acknowledgment note (optional)
    """
    try:
        try:
            aid = UUID(alert_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert_id format")
        
        success = await dba_alerting_service.acknowledge_alert(
            alert_id=aid,
            acknowledged_by=acknowledged_by,
            note=note,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to acknowledge alert")
        
        return {"status": "acknowledged", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.post("/risk-assessment")
async def run_risk_assessment(
    connection_id: str = Query(...),
    use_case: Optional[str] = Query(None),
    sql_query: Optional[str] = Query(None),
    request: Request = None,  # FastAPI request object for auth context
):
    """
    Run DBA risk simulation for a use case or custom SQL.
    
    This endpoint returns whether the bot will GO or NO-GO, and why.
    
    Shows all 4 hard gates (Production, Scope, Permission, Validation)
    and decision-blocking reasons if applicable.
    
    Query Parameters:
    - connection_id: Database connection ID (required)
    - use_case: DBA use case ID (optional if sql_query provided)
    - sql_query: Custom SQL to validate (optional if use_case provided)
    """
    try:
        # Validate at least one input
        if not use_case and not sql_query:
            raise HTTPException(
                status_code=400,
                detail="Provide either use_case or sql_query"
            )
        
        # Extract user context from request headers/auth
        # In sandbox mode, enforce viewer role for safety
        user_id = "sandbox_user"
        if request and hasattr(request, 'headers'):
            user_id = request.headers.get('X-User-ID', 'sandbox_user')
        
        # Sandbox mode: enforce viewer role (read-only)
        if os.getenv("SANDBOX_MODE", "false").lower() == "true":
            user_role = "viewer"
        else:
            # Production mode: get from headers or default to viewer
            if request and hasattr(request, 'headers'):
                user_role = request.headers.get('X-User-Role', 'viewer').lower()
            else:
                user_role = "viewer"
        
        logger.info(
            "Risk assessment requested",
            extra={
                "connection_id": connection_id,
                "use_case": use_case,
                "has_sql": bool(sql_query),
                "user_role": user_role,
                "user_id": user_id,
            }
        )
        
        # Run actual DBA risk assessment
        result = await dba_risk_assessment_service.run_assessment(
            connection_id=connection_id,
            use_case_id=use_case,
            sql_query=sql_query,
            user_context={
                "user_id": user_id,
                "tenant_id": None,
                "role": user_role,
            },
        )
        
        # Store in cache and return risk_id
        risk_id = risk_cache_service.store(result)
        
        return {
            "status": "success",
            "risk_id": risk_id,
            **result.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running risk assessment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Risk assessment failed")


class ExecutePlaybookRequest(BaseModel):
    """Request body for execute-playbook endpoint"""
    params: Optional[Dict[str, Any]] = None
    query_overrides: Optional[Dict[str, str]] = None  # step_number -> query_text


@router.post("/execute-playbook")
async def execute_playbook(
    connection_id: str = Query(...),
    use_case: str = Query(...),
    risk_id: Optional[str] = Query(None, description="Risk assessment ID from /risk-assessment endpoint"),
    force_rerun: bool = Query(False, description="Force rerun risk assessment even if risk_id provided"),
    body: Optional[ExecutePlaybookRequest] = Body(None),
    request: Request = None,
):
    """
    Execute full DBA playbook pipeline.
    
    Pipeline stages:
    1. Risk Assessment (from cache if risk_id provided, otherwise run new)
    2. Execution Plan Generation (structured JSON)
    3. Database Execution (raw results)
    4. Interpretation (LLM analysis)
    
    Returns all 3 tabs of data:
    - Risk Assessment
    - Execution Results (raw table)
    - Interpretation (findings + recommendations)
    
    Query Parameters:
    - connection_id: Database connection ID (required)
    - use_case: DBA use case ID (required)
    - risk_id: Risk assessment ID from /risk-assessment endpoint (optional)
    - force_rerun: Force rerun risk assessment even if risk_id provided (default: false)
    """
    try:
        from ...domain.dba.pipeline_orchestrator import DBAExecutionPipeline
        from ...domain.dba.adapters.mcp_db_client import MCPDBClient
        from ...domain.dba.risk_assessment_service import dba_risk_assessment_service
        
        # Extract user context
        user_id = "sandbox_user"
        if request and hasattr(request, 'headers'):
            user_id = request.headers.get('X-User-ID', 'sandbox_user')
        
        # Sandbox mode: enforce viewer role (read-only)
        if os.getenv("SANDBOX_MODE", "false").lower() == "true":
            user_role = "viewer"
        else:
            if request and hasattr(request, 'headers'):
                user_role = request.headers.get('X-User-Role', 'viewer').lower()
            else:
                user_role = "viewer"
        
        logger.info(
            "Execute playbook requested",
            extra={
                "connection_id": connection_id,
                "use_case": use_case,
                "risk_id": risk_id,
                "force_rerun": force_rerun,
                "user_role": user_role,
            }
        )
        
        # STEP 1: Get risk assessment from cache or run new
        risk_assessment = None
        
        if risk_id and not force_rerun:
            # Try to load from cache
            risk_assessment = risk_cache_service.get(risk_id)
            if risk_assessment:
                logger.info(f"Loaded risk assessment from cache", extra={"risk_id": risk_id})
            else:
                logger.warning(f"Risk assessment not found in cache, will run new", extra={"risk_id": risk_id})
        
        if not risk_assessment:
            # Run new risk assessment
            if force_rerun and risk_id:
                logger.warning(
                    "Force rerun requested for risk assessment",
                    extra={"risk_id": risk_id, "user_id": user_id}
                )
            
            risk_assessment = await dba_risk_assessment_service.run_assessment(
                connection_id=connection_id,
                use_case_id=use_case,
                sql_query=None,
                user_context={
                    "user_id": user_id,
                    "tenant_id": None,
                    "role": user_role,
                },
            )
        
        # Check risk assessment decision
        if risk_assessment.final_decision == "NO-GO":
            return {
                "status": "blocked",
                "reason": "Risk assessment failed",
                "risk_assessment": risk_assessment.to_dict(),
            }
        elif risk_assessment.final_decision == "GO-WITH-CONDITIONS":
            # Log warning for conditions
            logger.warning(
                "Executing playbook with conditions",
                extra={
                    "connection_id": connection_id,
                    "use_case": use_case,
                    "conditions": risk_assessment.warnings,
                    "user_id": user_id,
                }
            )
            # Continue execution but conditions are logged
        
        # STEP 2-4: Execute pipeline
        mcp_client = MCPDBClient()
        pipeline = DBAExecutionPipeline(mcp_client)
        
        # Get playbook name from metadata registry
        playbook_name = dba_use_case_metadata_registry.get_playbook_name(use_case)
        if not playbook_name:
            # Fallback: use uppercase use_case if no playbook defined
            playbook_name = use_case.upper()
            logger.warning(
                f"No playbook_name defined for use case: {use_case}, using fallback: {playbook_name}",
                extra={"use_case": use_case}
            )
        
        # Get db_type from risk assessment
        db_type = risk_assessment.checks_passed[0].get("db_type", "sqlserver") if risk_assessment.checks_passed else "sqlserver"
        
        # Extract query_overrides from body (convert step_1 -> "1")
        query_overrides = {}
        if body and body.query_overrides:
            for key, value in body.query_overrides.items():
                # Convert "step_1" -> "1" or keep "1" as is
                step_num = key.replace("step_", "") if key.startswith("step_") else key
                query_overrides[step_num] = value
        
        pipeline_result = await pipeline.execute(
            risk_assessment=risk_assessment,
            use_case_id=use_case,
            connection_id=connection_id,
            db_type=db_type,
            playbook_name=playbook_name,
            params=body.params if body else None,
            query_overrides=query_overrides if query_overrides else None,
        )
        
        return {
            "status": "success",
            "pipeline": pipeline_result.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing playbook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Playbook execution failed: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: Optional[str] = Query(None),
    resolution: Optional[str] = Query(None),
):
    """
    Resolve an alert.
    
    Path Parameters:
    - alert_id: UUID of the alert
    
    Query Parameters:
    - resolved_by: User who resolved (optional)
    - resolution: Resolution details (optional)
    """
    try:
        try:
            aid = UUID(alert_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert_id format")
        
        success = await dba_alerting_service.resolve_alert(
            alert_id=aid,
            resolved_by=resolved_by,
            resolution=resolution,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to resolve alert")
        
        return {"status": "resolved", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve alert")
