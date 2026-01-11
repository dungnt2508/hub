"""
DBA API Routes - Endpoints for DBA dashboard and operations
"""
from fastapi import APIRouter, Query, Depends, HTTPException, Body, Request
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from ...domain.dba.services.alerting_service import dba_alerting_service, AlertStatus
from ...domain.dba.services.metrics_history_service import dba_metrics_history_service
from ...domain.dba.risk_assessment_service import dba_risk_assessment_service
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
    """
    use_cases = [
        {
            "id": "analyze_slow_query",
            "name": "📊 Analyze Slow Queries",
            "description": "Find slow running queries on database",
            "intent": "analyze_slow_query",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id", "limit", "min_duration_ms"],
            "source_allowed": ["OPERATION"],
            "icon": "📊",
        },
        {
            "id": "check_index_health",
            "name": "🔍 Check Index Health",
            "description": "Check database index health and fragmentation",
            "intent": "check_index_health",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id", "schema"],
            "source_allowed": ["OPERATION"],
            "icon": "🔍",
        },
        {
            "id": "detect_blocking",
            "name": "🚫 Detect Blocking",
            "description": "Find blocking and locked transactions",
            "intent": "detect_blocking",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "🚫",
        },
        {
            "id": "analyze_wait_stats",
            "name": "⏳ Analyze Wait Statistics",
            "description": "Analyze database wait events and bottlenecks",
            "intent": "analyze_wait_stats",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "⏳",
        },
        {
            "id": "detect_deadlock_pattern",
            "name": "💀 Detect Deadlocks",
            "description": "Detect deadlock patterns in transaction logs",
            "intent": "detect_deadlock_pattern",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id", "time_window_hours"],
            "source_allowed": ["OPERATION"],
            "icon": "💀",
        },
        {
            "id": "analyze_io_pressure",
            "name": "📈 Analyze I/O Pressure",
            "description": "Analyze disk I/O utilization and bottlenecks",
            "intent": "analyze_io_pressure",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "📈",
        },
        {
            "id": "capacity_forecast",
            "name": "📉 Capacity Forecast",
            "description": "Forecast database capacity and growth",
            "intent": "capacity_forecast",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id", "forecast_days"],
            "source_allowed": ["OPERATION"],
            "icon": "📉",
        },
        {
            "id": "validate_custom_sql",
            "name": "✅ Validate Custom SQL",
            "description": "Validate custom SQL for syntax and safety",
            "intent": "validate_custom_sql",
            "required_slots": ["db_type", "sql_query"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "✅",
        },
        {
            "id": "analyze_query_regression",
            "name": "📊 Detect Query Regression",
            "description": "Detect queries with performance degradation",
            "intent": "analyze_query_regression",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id", "baseline_period_days", "regression_threshold_percent"],
            "source_allowed": ["OPERATION"],
            "icon": "📊",
        },
        {
            "id": "compare_sp_blitz_vs_custom",
            "name": "⚖️ sp_Blitz vs Custom",
            "description": "Compare sp_Blitz findings with custom analysis",
            "intent": "compare_sp_blitz_vs_custom",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "⚖️",
        },
        {
            "id": "incident_triage",
            "name": "🚨 Incident Triage",
            "description": "Triage and analyze database incidents",
            "intent": "incident_triage",
            "required_slots": ["db_type"],
            "optional_slots": ["connection_id"],
            "source_allowed": ["OPERATION"],
            "icon": "🚨",
        },
    ]

    return {
        "status": "success",
        "total": len(use_cases),
        "use_cases": use_cases,
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
        # In sandbox mode, default to admin if not provided
        user_role = "admin"  # Default for sandbox - can modify prod
        user_id = "sandbox_user"
        
        # Try to extract from request headers if available
        if request and hasattr(request, 'headers'):
            # Check for X-User-Role header (for testing)
            user_role = request.headers.get('X-User-Role', 'admin').lower()
            user_id = request.headers.get('X-User-ID', 'sandbox_user')
        
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
                "role": user_role,  # IMPORTANT: Set role so production gate works
            },
        )
        
        return {
            "status": "success",
            **result.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running risk assessment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Risk assessment failed")


@router.post("/execute-playbook")
async def execute_playbook(
    connection_id: str = Query(...),
    use_case: str = Query(...),
    request: Request = None,
):
    """
    Execute full DBA playbook pipeline.
    
    Pipeline stages:
    1. Risk Assessment (input from previous call)
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
    """
    try:
        from ...domain.dba.pipeline_orchestrator import DBAExecutionPipeline
        from ...domain.dba.adapters.mcp_db_client import MCPDBClient
        from ...domain.dba.risk_assessment_service import dba_risk_assessment_service
        
        # Extract user context
        user_role = "admin"  # Default for sandbox
        user_id = "sandbox_user"
        if request and hasattr(request, 'headers'):
            user_role = request.headers.get('X-User-Role', 'admin').lower()
            user_id = request.headers.get('X-User-ID', 'sandbox_user')
        
        logger.info(
            "Execute playbook requested",
            extra={
                "connection_id": connection_id,
                "use_case": use_case,
                "user_role": user_role,
            }
        )
        
        # STEP 1: Run risk assessment first
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
        
        # If NO-GO, return early
        if risk_assessment.final_decision == "NO-GO":
            return {
                "status": "blocked",
                "reason": "Risk assessment failed",
                "risk_assessment": risk_assessment.to_dict(),
            }
        
        # STEP 2-4: Execute pipeline
        mcp_client = MCPDBClient()
        pipeline = DBAExecutionPipeline(mcp_client)
        
        # Map use_case to playbook name
        playbook_map = {
            "analyze_slow_query": "QUERY_PERFORMANCE",
            "check_index_health": "INDEX_HEALTH",
            "detect_blocking": "BLOCKING_ANALYSIS",
            "analyze_wait_stats": "WAIT_STATISTICS",
            "detect_deadlock_pattern": "DEADLOCK_DETECTION",
            "analyze_io_pressure": "IO_PRESSURE",
            "capacity_forecast": "CAPACITY_PLANNING",
        }
        
        playbook_name = playbook_map.get(use_case, use_case.upper())
        
        # Get db_type from risk assessment
        db_type = risk_assessment.checks_passed[0].get("db_type", "sqlserver") if risk_assessment.checks_passed else "sqlserver"
        
        pipeline_result = await pipeline.execute(
            risk_assessment=risk_assessment,
            use_case_id=use_case,
            connection_id=connection_id,
            db_type=db_type,
            playbook_name=playbook_name,
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
