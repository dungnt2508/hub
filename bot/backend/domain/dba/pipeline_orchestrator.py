"""
Pipeline Orchestrator - Orchestrates the complete execution flow

Flow:
1. Risk Assessment (ALREADY DONE via risk_assessment_service.py)
   → Returns: NO-GO, GO, or GO-WITH-CONDITIONS

2. Execution Plan Generation (Execution Plan Generator)
   → Input: Risk assessment result
   → Output: Structured execution plan (JSON)

3. Database Execution (DB Executor)
   → Input: Execution plan
   → Output: Raw database results (no processing)

4. Interpretation (Interpretation Layer)
   → Input: Execution plan + Raw DB results
   → Output: Structured findings + recommendations (JSON)

GUARANTEE:
- Each step is distinct and isolated
- No step mixes concerns
- Frontend gets 3 separate tabs of data
- LLM only in interpretation phase
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import time

from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.logger import logger
from ...shared.exceptions import DomainError
from .risk_assessment_service import RiskAssessmentResult
from .execution_plan_generator import ExecutionPlan, execution_plan_generator
from .db_executor import ExecutionResult, DatabaseExecutor
from .interpretation_layer import InterpretationResult, InterpretationLayer
from .ports.mcp_client import IMCPDBClient


@dataclass
class PipelineStageResult:
    """Result of a single pipeline stage"""
    stage: str  # "risk_assessment", "execution_plan", "db_execution", "interpretation"
    status: str  # "success", "failure", "skipped"
    duration_ms: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class PipelineExecutionResult:
    """Complete pipeline execution result"""
    request_id: str
    playbook: str
    connection_id: str
    started_at: str = ""
    completed_at: str = ""
    total_duration_ms: int = 0
    pipeline_status: str = "pending"  # "success", "failed", "stopped"
    stages: List[PipelineStageResult] = field(default_factory=list)
    # Output from each stage
    risk_assessment: Optional[RiskAssessmentResult] = None
    execution_plan: Optional[ExecutionPlan] = None
    execution_results: Optional[ExecutionResult] = None
    interpretation: Optional[InterpretationResult] = None

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "request_id": self.request_id,
            "playbook": self.playbook,
            "connection_id": self.connection_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "pipeline_status": self.pipeline_status,
            "stages": [asdict(s) for s in self.stages],
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "execution_plan": self.execution_plan.to_dict() if self.execution_plan else None,
            "execution_results": self.execution_results.to_dict() if self.execution_results else None,
            "interpretation": self.interpretation.to_dict() if self.interpretation else None,
        }


class DBAExecutionPipeline:
    """
    Orchestrates DBA execution pipeline.

    PIPELINE:
    Risk Assessment → Execution Plan → DB Execution → Interpretation

    Each stage:
    1. Has clear input/output
    2. No dependencies outside its scope
    3. Produces structured output
    4. Can be tested independently
    """

    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize pipeline with required clients.

        Args:
            mcp_client: MCP database client
        """
        if mcp_client is None:
            raise ValueError("MCP client is required for DBAExecutionPipeline")
        self.mcp_client = mcp_client
        self.db_executor = DatabaseExecutor(mcp_client)
        self.interpretation_layer = InterpretationLayer()

    async def execute(
        self,
        risk_assessment: RiskAssessmentResult,
        use_case_id: str,
        connection_id: str,
        db_type: str,
        playbook_name: str,
        request: Optional[DomainRequest] = None,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
    ) -> PipelineExecutionResult:
        """
        Execute complete DBA pipeline.

        Args:
            risk_assessment: Result from risk assessment (ALREADY DONE)
            use_case_id: DBA use case ID
            connection_id: Database connection ID
            db_type: Database type (sqlserver, postgresql, mysql)
            playbook_name: Name of playbook to execute
            request: Optional domain request context
            connection_string: Optional connection string
            connection_name: Optional connection name

        Returns:
            PipelineExecutionResult: Complete pipeline result

        Raises:
            DomainError: If pipeline execution fails
        """
        import uuid
        request_id = str(uuid.uuid4())
        result = PipelineExecutionResult(
            request_id=request_id,
            playbook=playbook_name,
            connection_id=connection_id,
        )

        start_time = time.time()

        try:
            # STAGE 1: Risk Assessment (ALREADY COMPLETED)
            # We receive the risk_assessment result as input
            stage1_result = await self._stage_risk_assessment(risk_assessment)
            result.stages.append(stage1_result)
            result.risk_assessment = risk_assessment

            # Check if we can proceed
            if risk_assessment.final_decision == "NO-GO":
                logger.warning(
                    f"Pipeline stopped at risk assessment",
                    extra={"request_id": request_id, "playbook": playbook_name}
                )
                result.pipeline_status = "stopped"
                return self._finalize_result(result, start_time)

            # STAGE 2: Generate Execution Plan
            logger.info(
                f"Stage 2: Generating execution plan",
                extra={"request_id": request_id, "playbook": playbook_name}
            )
            stage2_result, execution_plan = await self._stage_execution_plan(
                playbook_name=playbook_name,
                use_case_id=use_case_id,
                db_type=db_type,
                risk_level=risk_assessment.risk_level,
            )
            result.stages.append(stage2_result)
            result.execution_plan = execution_plan

            if stage2_result.status == "failure":
                logger.error(
                    f"Execution plan generation failed",
                    extra={"request_id": request_id}
                )
                result.pipeline_status = "failed"
                return self._finalize_result(result, start_time)

            # STAGE 3: Execute Plan Against Database
            logger.info(
                f"Stage 3: Executing database queries",
                extra={"request_id": request_id, "playbook": playbook_name}
            )
            stage3_result, execution_results = await self._stage_db_execution(
                execution_plan=execution_plan,
                connection_id=connection_id,
                connection_string=connection_string,
                connection_name=connection_name,
            )
            result.stages.append(stage3_result)
            result.execution_results = execution_results

            # STAGE 4: Interpretation
            logger.info(
                f"Stage 4: Interpreting results",
                extra={"request_id": request_id, "playbook": playbook_name}
            )
            stage4_result, interpretation = await self._stage_interpretation(
                execution_plan=execution_plan,
                execution_result=execution_results,
                playbook_name=playbook_name,
                connection_id=connection_id,
            )
            result.stages.append(stage4_result)
            result.interpretation = interpretation

            # Determine overall status
            failed_stages = [s for s in result.stages if s.status == "failure"]
            if failed_stages:
                result.pipeline_status = "failed"
            else:
                result.pipeline_status = "success"

            logger.info(
                f"Pipeline complete",
                extra={
                    "request_id": request_id,
                    "status": result.pipeline_status,
                    "stages": len(result.stages),
                }
            )

            return self._finalize_result(result, start_time)

        except Exception as e:
            logger.error(
                f"Pipeline execution failed: {e}",
                extra={"request_id": request_id},
                exc_info=True
            )
            result.pipeline_status = "failed"
            if result.stages:
                result.stages[-1].error = str(e)
            else:
                result.stages.append(
                    PipelineStageResult(
                        stage="unknown",
                        status="failure",
                        duration_ms=0,
                        error=str(e),
                    )
                )
            return self._finalize_result(result, start_time)

    async def _stage_risk_assessment(
        self, risk_assessment: RiskAssessmentResult
    ) -> PipelineStageResult:
        """
        Stage 1: Risk Assessment (input, already completed).

        Returns:
            PipelineStageResult: Stage result
        """
        start_time = time.time()
        try:
            return PipelineStageResult(
                stage="risk_assessment",
                status="success",
                duration_ms=0,
                data=risk_assessment.to_dict(),
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return PipelineStageResult(
                stage="risk_assessment",
                status="failure",
                duration_ms=int(elapsed * 1000),
                error=str(e),
            )

    async def _stage_execution_plan(
        self,
        playbook_name: str,
        use_case_id: str,
        db_type: str,
        risk_level: str,
    ) -> tuple[PipelineStageResult, Optional[ExecutionPlan]]:
        """
        Stage 2: Generate Execution Plan.

        Returns:
            Tuple of (PipelineStageResult, ExecutionPlan or None)
        """
        start_time = time.time()
        try:
            execution_plan = await execution_plan_generator.generate(
                playbook_name=playbook_name,
                use_case_id=use_case_id,
                risk_level=risk_level,
                db_type=db_type,
            )

            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="execution_plan",
                    status="success",
                    duration_ms=int(elapsed * 1000),
                    data=execution_plan.to_dict(),
                ),
                execution_plan,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="execution_plan",
                    status="failure",
                    duration_ms=int(elapsed * 1000),
                    error=str(e),
                ),
                None,
            )

    async def _stage_db_execution(
        self,
        execution_plan: ExecutionPlan,
        connection_id: str,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
    ) -> tuple[PipelineStageResult, Optional[ExecutionResult]]:
        """
        Stage 3: Execute Plan Against Database.

        Returns:
            Tuple of (PipelineStageResult, ExecutionResult or None)
        """
        start_time = time.time()
        try:
            execution_results = await self.db_executor.execute(
                plan=execution_plan,
                connection_id=connection_id,
                connection_string=connection_string,
                connection_name=connection_name,
                stop_on_error=False,  # Continue even if steps fail
            )

            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="db_execution",
                    status="success",
                    duration_ms=int(elapsed * 1000),
                    data=execution_results.to_dict(),
                ),
                execution_results,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="db_execution",
                    status="failure",
                    duration_ms=int(elapsed * 1000),
                    error=str(e),
                ),
                None,
            )

    async def _stage_interpretation(
        self,
        execution_plan: ExecutionPlan,
        execution_result: ExecutionResult,
        playbook_name: str,
        connection_id: str,
    ) -> tuple[PipelineStageResult, Optional[InterpretationResult]]:
        """
        Stage 4: Interpret Results.

        Returns:
            Tuple of (PipelineStageResult, InterpretationResult or None)
        """
        start_time = time.time()
        try:
            interpretation = await self.interpretation_layer.interpret(
                execution_plan=execution_plan,
                execution_result=execution_result,
                playbook_name=playbook_name,
                connection_id=connection_id,
            )

            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="interpretation",
                    status="success",
                    duration_ms=int(elapsed * 1000),
                    data=interpretation.to_dict(),
                ),
                interpretation,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return (
                PipelineStageResult(
                    stage="interpretation",
                    status="failure",
                    duration_ms=int(elapsed * 1000),
                    error=str(e),
                ),
                None,
            )

    def _finalize_result(
        self, result: PipelineExecutionResult, start_time: float
    ) -> PipelineExecutionResult:
        """Finalize pipeline result with timing."""
        elapsed = time.time() - start_time
        result.total_duration_ms = int(elapsed * 1000)
        result.completed_at = datetime.utcnow().isoformat()
        return result
