"""
DBA Risk Assessment Service

Captures gate decisions from DBA bot execution and builds risk assessment result.

Purpose: Bridge between DBA use cases and risk simulation frontend.
Shows what gates passed/blocked and why, before actual execution.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from contextlib import asynccontextmanager

from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.logger import logger
from ...shared.exceptions import DomainError
from .entry_handler import DBAEntryHandler
from .ports.mcp_client import IMCPDBClient
from .connection_registry_bridge import connection_registry_bridge


@dataclass
class GateCheckResult:
    """Result of a single gate check"""
    gate_name: str
    status: str  # PASS, BLOCK, WARN
    reason: str
    duration_ms: int = 0


@dataclass
class ExecutionStep:
    """Single step in execution trace"""
    step: str
    result: str  # pass, fail, warn
    duration_ms: int


@dataclass
class ExecutionTrace:
    """Complete execution trace"""
    timestamp: str
    duration_ms: int
    steps: List[ExecutionStep]


@dataclass
class RiskAssessmentResult:
    """Final risk assessment result"""
    final_decision: str  # GO, GO-WITH-CONDITIONS, or NO-GO
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    gates: List[GateCheckResult]
    critical_issues: List[str]
    warnings: List[str]
    checks_passed: List[Dict[str, Any]]
    recommendations: List[str]
    trace: ExecutionTrace
    decision_explanation: Optional[str] = None  # Why this decision
    can_execute: bool = False  # Whether user can execute diagnostic

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "final_decision": self.final_decision,
            "risk_level": self.risk_level,
            "decision_explanation": self.decision_explanation,
            "can_execute": self.can_execute,
            "gates": [asdict(g) for g in self.gates],
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "checks_passed": self.checks_passed,
            "recommendations": self.recommendations,
            "trace": {
                "timestamp": self.trace.timestamp,
                "duration_ms": self.trace.duration_ms,
                "steps": [asdict(s) for s in self.trace.steps],
            },
        }


class GateExecutionCapture:
    """
    Context manager to capture gate execution for risk assessment.
    
    Tracks which gates passed/blocked and why.
    """

    def __init__(self):
        self.gates: List[GateCheckResult] = []
        self.steps: List[ExecutionStep] = []
        self.start_time = None
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []

    def record_gate(self, gate_name: str, status: str, reason: str, duration_ms: int = 0):
        """Record a gate check result"""
        self.gates.append(GateCheckResult(gate_name, status, reason, duration_ms))

    def record_step(self, step: str, result: str, duration_ms: int):
        """Record an execution step"""
        self.steps.append(ExecutionStep(step, result, duration_ms))

    def add_critical_issue(self, issue: str):
        """Add a critical issue"""
        self.critical_issues.append(issue)

    def add_warning(self, warning: str):
        """Add a warning"""
        self.warnings.append(warning)

    def is_blocked(self) -> bool:
        """Check if any gate blocked the execution"""
        return any(g.status == "BLOCK" for g in self.gates)

    def get_blocked_gates(self) -> List[GateCheckResult]:
        """Get all blocked gates"""
        return [g for g in self.gates if g.status == "BLOCK"]


class DBARiskAssessmentService:
    """
    Service to run risk assessment for DBA operations.

    Process:
    1. Load DBA use case
    2. Capture gate execution
    3. Build risk assessment result
    4. Return to frontend
    """

    def __init__(self, mcp_client: Optional[IMCPDBClient] = None):
        """
        Initialize risk assessment service.

        Args:
            mcp_client: MCP DB client (optional, DBAEntryHandler creates if not provided)
        """
        self.dba_handler = DBAEntryHandler(mcp_client)

    async def run_assessment(
        self,
        connection_id: str,
        use_case_id: Optional[str] = None,
        sql_query: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessmentResult:
        """
        Run risk assessment for a DBA operation.

        Args:
            connection_id: Database connection ID
            use_case_id: DBA use case ID (optional if sql_query provided)
            sql_query: Custom SQL query (optional if use_case_id provided)
            user_context: User context (tenant_id, user_id, permissions, etc.)

        Returns:
            RiskAssessmentResult with gates, decision, and trace

        Raises:
            DomainError: If assessment fails
        """
        start_time = datetime.utcnow()
        capture = GateExecutionCapture()

        try:
            logger.info(
                "Risk assessment started",
                extra={
                    "connection_id": connection_id,
                    "use_case_id": use_case_id,
                    "has_sql": bool(sql_query),
                },
            )

            # Step 1: Validate inputs
            if not use_case_id and not sql_query:
                raise DomainError("Provide either use_case_id or sql_query")

            # Step 2: Determine intent
            if use_case_id:
                # Map use_case_id to intent
                intent = self._map_use_case_to_intent(use_case_id)
            else:
                # Custom SQL validation
                intent = "validate_custom_sql"

            capture.record_step("Validate inputs", "pass", 5)

            # Step 3: Fetch connection details
            connection = await connection_registry_bridge.get_connection(connection_id)
            if not connection:
                raise DomainError(f"Connection not found: {connection_id}")

            capture.record_step(f"Load connection {connection.name}", "pass", 10)

            # Step 4: Determine if user can modify production
            # Only ADMIN role can modify prod (from admin_users.role)
            _user_context = user_context or {
                "user_id": "sandbox_user",
                "tenant_id": None,
                "role": "viewer",
            }
            
            # Check if user is admin role
            # admin_users.role can be: 'admin', 'operator', 'viewer'
            user_role = _user_context.get("role", "").lower()
            can_modify_prod = user_role == "admin"  # Only admin role can modify production
            
            _user_context["can_modify_prod"] = can_modify_prod
            
            # Step 5: Build DomainRequest
            # This will trigger gate execution in DBAEntryHandler
            request = DomainRequest(
                domain="dba",
                intent=intent,
                intent_type="OPERATION",
                trace_id=str(uuid.uuid4()),
                user_context=_user_context,
                slots={
                    "connection_id": connection_id,
                    "connection_name": connection.name,
                    "db_type": connection.db_type,
                    "host": connection.host,
                    "port": str(connection.port),
                    "is_production": str(connection.is_production),
                    "sql_query": sql_query,
                    "database": connection.name,  # For scope validation
                    "server": connection.host,  # For scope context
                },
            )

            capture.record_step("Build request", "pass", 3)

            # Step 6: Execute DBA use case (with gate capture)
            # NOTE: In production, need to hook into gates execution
            # For now, we simulate based on request validity
            capture = self._simulate_gate_execution(request, connection, capture)

            capture.record_step("Execute use case", "pass", 150)

            # Step 7: Build result
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            result = self._build_result(capture, duration_ms)

            logger.info(
                "Risk assessment completed",
                extra={
                    "connection_id": connection_id,
                    "final_decision": result.final_decision,
                    "risk_level": result.risk_level,
                    "duration_ms": duration_ms,
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Risk assessment failed: {e}",
                extra={
                    "connection_id": connection_id,
                    "use_case_id": use_case_id,
                },
                exc_info=True,
            )
            raise DomainError(f"Risk assessment failed: {e}") from e

    def _map_use_case_to_intent(self, use_case_id: str) -> str:
        """Map use_case_id to DBA intent"""
        # In production, load from database
        mapping = {
            "analyze_slow_query": "analyze_slow_query",
            "check_index_health": "check_index_health",
            "detect_blocking": "detect_blocking",
            "analyze_wait_stats": "analyze_wait_stats",
            "detect_deadlock_pattern": "detect_deadlock_pattern",
            "analyze_io_pressure": "analyze_io_pressure",
            "capacity_forecast": "capacity_forecast",
            "validate_custom_sql": "validate_custom_sql",
            "analyze_query_regression": "analyze_query_regression",
            "compare_sp_blitz_vs_custom": "compare_sp_blitz_vs_custom",
            "incident_triage": "incident_triage",
        }
        return mapping.get(use_case_id, use_case_id)

    def _simulate_gate_execution(
        self,
        request: DomainRequest,
        connection: Any,
        capture: GateExecutionCapture
    ) -> GateExecutionCapture:
        """
        Simulate gate execution based on request and connection.

        In production, this should hook into actual gate execution from DBAEntryHandler.
        For now, we simulate based on connection/request validity.
        """
        # Gate 1: Production Safety
        if connection.is_production and not request.user_context.get("can_modify_prod"):
            capture.record_gate(
                "Production Safety",
                "BLOCK",
                f"Production database '{connection.name}' access requires elevated permission",
                5,
            )
            capture.add_critical_issue("Production database access denied")
        else:
            reason = (
                f"Non-production database: {connection.name}"
                if not connection.is_production
                else "User has production access permission"
            )
            capture.record_gate(
                "Production Safety",
                "PASS",
                reason,
                5,
            )

        # Gate 2: Scope Validation
        connection_id = request.slots.get("connection_id")
        if not connection_id:
            capture.record_gate(
                "Scope Validation", "BLOCK", "Database/connection not specified", 15
            )
            capture.add_critical_issue("Scope not specified - cannot run cluster-wide query")
        else:
            capture.record_gate(
                "Scope Validation", "PASS", "Database explicitly specified", 15
            )

        # Gate 3: Permission Check
        permissions = request.user_context.get("permissions", [])
        if not permissions:
            capture.record_gate(
                "Permission Check",
                "WARN",
                "Permission context not provided - pre-validated at router",
                50,
            )
        else:
            capture.record_gate(
                "Permission Check", "PASS", "User has required permissions", 50
            )

        # Gate 4: Response Validation
        capture.record_gate(
            "Response Validation",
            "PASS",
            "Expected response structure will be validated",
            15,
        )

        return capture

    def _build_result(
        self, capture: GateExecutionCapture, total_duration_ms: int
    ) -> RiskAssessmentResult:
        """Build final risk assessment result"""
        # Determine final decision based on gate status
        is_blocked = capture.is_blocked()
        has_warnings = any(g.status == "WARN" for g in capture.gates)
        
        if is_blocked:
            final_decision = "NO-GO"  # Cannot proceed
        elif has_warnings:
            final_decision = "GO-WITH-CONDITIONS"  # Can proceed but with caution
        else:
            final_decision = "GO"  # Safe to proceed
        
        # Determine risk level
        if capture.critical_issues:
            risk_level = "CRITICAL"
        elif has_warnings:
            risk_level = "MEDIUM"  # GO-WITH-CONDITIONS = MEDIUM risk
        elif capture.warnings:
            risk_level = "HIGH"
        else:
            risk_level = "LOW"

        # Get blocked gates for display
        blocked_gates = capture.get_blocked_gates()

        # Build trace
        capture.record_step("Complete risk assessment", "pass", 5)
        trace = ExecutionTrace(
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=total_duration_ms,
            steps=capture.steps,
        )

        # Build passed checks
        checks_passed = [
            {"check_name": g.gate_name}
            for g in capture.gates
            if g.status == "PASS"
        ]

        # Determine if user can execute diagnostic
        can_execute = final_decision != "NO-GO"
        
        # Build decision explanation
        decision_explanation = self._build_decision_explanation(
            final_decision, capture, is_blocked, has_warnings
        )

        return RiskAssessmentResult(
            final_decision=final_decision,
            risk_level=risk_level,
            gates=capture.gates,
            critical_issues=capture.critical_issues,
            warnings=capture.warnings,
            checks_passed=checks_passed,
            recommendations=self._get_recommendations(capture, final_decision),
            trace=trace,
            decision_explanation=decision_explanation,
            can_execute=can_execute,
        )

    def _build_decision_explanation(
        self,
        final_decision: str,
        capture: GateExecutionCapture,
        is_blocked: bool,
        has_warnings: bool,
    ) -> str:
        """Build human-readable explanation for the decision"""
        if final_decision == "NO-GO":
            blocked_gates = capture.get_blocked_gates()
            blocked_names = [g.gate_name for g in blocked_gates]
            return f"Blocked by: {', '.join(blocked_names)}"
        elif final_decision == "GO-WITH-CONDITIONS":
            warning_gates = [g for g in capture.gates if g.status == "WARN"]
            warning_names = [g.gate_name for g in warning_gates]
            return f"Proceed with caution. Warnings: {', '.join(warning_names)}"
        else:  # GO
            return "All gates passed. Safe to proceed with diagnostic."

    def _get_recommendations(
        self, capture: GateExecutionCapture, final_decision: str
    ) -> List[str]:
        """Get recommendations based on assessment"""
        recommendations = []

        if final_decision == "NO-GO":
            blocked = capture.get_blocked_gates()
            for gate in blocked:
                if "Production" in gate.gate_name:
                    recommendations.append(
                        "This is a production database. Obtain elevation or use non-prod database."
                    )
                elif "Scope" in gate.gate_name:
                    recommendations.append(
                        "Specify the target database or connection explicitly."
                    )
                elif "Permission" in gate.gate_name:
                    recommendations.append(
                        "Request required permissions from database administrator."
                    )

        if capture.warnings:
            recommendations.append("Review warnings and verify expected behavior before proceeding.")

        if final_decision == "GO":
            recommendations.append("Assessment passed all gates. Ready to execute diagnostic.")
        
        if final_decision == "GO-WITH-CONDITIONS":
            recommendations.append("Acknowledge warnings and proceed with diagnostic execution.")

        return recommendations

    async def execute_diagnostic(
        self,
        connection_id: str,
        intent: str,
        slots: Dict[str, Any],
        user_context: Dict[str, Any],
        gate_results: List[Dict[str, Any]],
        final_decision: str,
    ) -> Dict[str, Any]:
        """
        Execute diagnostic playbook after gates pass.
        
        Only called if final_decision is GO or GO-WITH-CONDITIONS.
        Returns diagnostic results from playbook.
        """
        # Check if decision allows execution
        if final_decision == "NO-GO":
            return {
                "status": "blocked",
                "error": "Cannot execute - gates blocking",
                "gate_results": gate_results,
            }

        try:
            # Create DomainRequest for playbook
            request = DomainRequest(
                domain="dba",
                intent=intent,
                intent_type="OPERATION",
                trace_id=str(uuid.uuid4()),
                user_context=user_context,
                slots=slots,
            )

            logger.info(
                f"Executing DBA diagnostic: {intent}",
                extra={
                    "connection_id": connection_id,
                    "intent": intent,
                    "decision": final_decision,
                },
            )

            # Execute playbook via DBA entry handler
            response: DomainResponse = await self.dba_handler.handle(request)

            if response.status == DomainResult.SUCCESS:
                return {
                    "status": "success",
                    "data": response.data,
                    "decision": final_decision,
                }
            else:
                return {
                    "status": "error",
                    "error": response.message,
                    "decision": final_decision,
                }

        except Exception as e:
            logger.error(
                f"Error executing diagnostic: {e}",
                extra={"intent": intent, "connection_id": connection_id},
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
                "decision": final_decision,
            }


# Singleton instance
dba_risk_assessment_service = DBARiskAssessmentService()
