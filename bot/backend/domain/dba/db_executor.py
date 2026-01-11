"""
Database Executor - Executes structured execution plans sequentially

CRITICAL CONSTRAINTS:
1. Execute steps in EXACT order (no reordering)
2. No skipping (stop on first failure if required)
3. No LLM SQL generation - use predefined queries only
4. Output RAW results from database (no processing)
5. Each step has timeout and execution time tracking
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import time
import asyncio

from ...schemas import DomainRequest
from ...shared.logger import logger
from ...shared.exceptions import DomainError
from .execution_plan_generator import ExecutionPlan, ExecutionStep
from .ports.mcp_client import IMCPDBClient
from .connection_registry_bridge import connection_registry_bridge


@dataclass
class StepExecutionResult:
    """Result of executing a single step"""
    step: int
    status: str = "pending"  # "success", "failure", "timeout", "skipped", "pending"
    duration_ms: int = 0
    rows: int = 0
    columns: List[str] = field(default_factory=list)
    data: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "step": self.step,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "rows": self.rows,
            "columns": self.columns,
            "data": self.data,
            "error": self.error,
        }


@dataclass
class ExecutionResult:
    """Complete execution result for all steps"""
    playbook: str
    connection_id: str
    started_at: str = ""
    completed_at: str = ""
    total_duration_ms: int = 0
    status: str = "pending"  # "success", "partial_failure", "failure"
    step_results: List[StepExecutionResult] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "playbook": self.playbook,
            "connection_id": self.connection_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status,
            "step_results": [r.to_dict() for r in self.step_results],
            "error": self.error,
        }


class DatabaseExecutor:
    """
    Executes database queries from an execution plan.

    Guarantees:
    - Steps executed in exact order
    - No SQL generation by LLM
    - Raw database results returned
    - All errors logged
    - Timeout handling per step
    """

    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize database executor.

        Args:
            mcp_client: MCP database client for executing queries
        """
        if mcp_client is None:
            raise ValueError("MCP client is required for DatabaseExecutor")
        self.mcp_client = mcp_client

    async def execute(
        self,
        plan: ExecutionPlan,
        connection_id: str,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        stop_on_error: bool = False,
    ) -> ExecutionResult:
        """
        Execute the execution plan sequentially.

        Args:
            plan: ExecutionPlan with steps to execute
            connection_id: Database connection ID
            connection_string: Optional connection string
            connection_name: Optional connection name
            stop_on_error: Stop execution on first error (default: False, continue)

        Returns:
            ExecutionResult: Results of all executed steps

        Raises:
            DomainError: If execution fails critically
        """
        result = ExecutionResult(
            playbook=plan.playbook,
            connection_id=connection_id,
        )

        if not plan.execution_plan:
            logger.warning(
                f"Empty execution plan",
                extra={"playbook": plan.playbook, "connection_id": connection_id}
            )
            result.status = "success"
            result.completed_at = datetime.utcnow().isoformat()
            result.total_duration_ms = 0
            return result

        start_time = time.time()

        # Resolve connection string if not provided
        resolved_connection_string = connection_string
        if not resolved_connection_string:
            try:
                conn_info = await connection_registry_bridge.get_connection(connection_id)
                # For now, just use connection ID
                # In production, build proper connection string from host/port/creds
                logger.debug(
                    f"Resolved connection info",
                    extra={"connection_id": connection_id, "db_type": conn_info.db_type}
                )
            except Exception as e:
                logger.warning(
                    f"Failed to resolve connection, will pass connection_id to MCP: {e}",
                    extra={"connection_id": connection_id}
                )

        try:
            # Execute each step in exact order
            for step in plan.execution_plan:
                logger.info(
                    f"Executing step {step.step}",
                    extra={
                        "playbook": plan.playbook,
                        "purpose": step.purpose,
                        "step": step.step,
                    }
                )

                step_result = await self._execute_step(
                    step=step,
                    connection_id=connection_id,
                    connection_string=connection_string,
                    connection_name=connection_name,
                )

                result.step_results.append(step_result)

                # Check if we should stop on error
                if stop_on_error and step_result.status == "failure":
                    logger.warning(
                        f"Step {step.step} failed, stopping execution",
                        extra={"playbook": plan.playbook}
                    )
                    result.status = "partial_failure"
                    break

            # Determine overall status
            if result.status != "partial_failure":
                failed_steps = [r for r in result.step_results if r.status == "failure"]
                if failed_steps:
                    result.status = "partial_failure"
                else:
                    result.status = "success"

        except Exception as e:
            logger.error(
                f"Execution failed: {e}",
                extra={"playbook": plan.playbook},
                exc_info=True
            )
            result.status = "failure"
            result.error = str(e)

        finally:
            # Finalize result
            elapsed = time.time() - start_time
            result.total_duration_ms = int(elapsed * 1000)
            result.completed_at = datetime.utcnow().isoformat()

        return result

    async def _execute_step(
        self,
        step: ExecutionStep,
        connection_id: str,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
    ) -> StepExecutionResult:
        """
        Execute a single step.

        Args:
            step: ExecutionStep to execute
            connection_id: Database connection ID
            connection_string: Optional connection string
            connection_name: Optional connection name

        Returns:
            StepExecutionResult: Result of executing the step
        """
        result = StepExecutionResult(
            step=step.step,
            status="pending",
            duration_ms=0
        )
        start_time = time.time()

        try:
            # Validate step type
            if step.type != "sql":
                result.status = "skipped"
                result.error = f"Unsupported step type: {step.type}"
                return result

            # Query is predefined in the plan - NO generation
            query = step.query.strip()
            if not query:
                result.status = "failure"
                result.error = "No query defined for step"
                return result

            logger.debug(
                f"Executing query",
                extra={
                    "step": step.step,
                    "purpose": step.purpose,
                    "engine": step.engine,
                    "query_length": len(query),
                }
            )

            # Execute query with timeout
            try:
                # Call MCP client to execute query
                # The MCP client handles the actual database connection
                rows_data = await asyncio.wait_for(
                    self.mcp_client.execute_query(
                        query=query,
                        connection_id=str(connection_id) if connection_id else None,
                        connection_string=connection_string,
                        connection_name=connection_name,
                        db_type=step.engine,
                        timeout_seconds=step.timeout_seconds,
                    ),
                    timeout=step.timeout_seconds + 5,  # Add buffer
                )

                # Parse results
                if isinstance(rows_data, list) and len(rows_data) > 0:
                    # Extract columns from first row
                    if isinstance(rows_data[0], dict):
                        result.columns = list(rows_data[0].keys())
                    result.data = rows_data
                    result.rows = len(rows_data)
                else:
                    result.rows = 0
                    result.data = []

                result.status = "success"

            except asyncio.TimeoutError:
                result.status = "timeout"
                result.error = f"Query timeout after {step.timeout_seconds} seconds"
                logger.warning(
                    f"Query timeout",
                    extra={"step": step.step, "timeout": step.timeout_seconds}
                )

        except Exception as e:
            result.status = "failure"
            result.error = str(e)
            logger.error(
                f"Step execution failed: {e}",
                extra={"step": step.step, "purpose": step.purpose},
                exc_info=True
            )

        finally:
            # Calculate duration
            elapsed = time.time() - start_time
            result.duration_ms = int(elapsed * 1000)

        return result

    def validate_step_order(self, plan: ExecutionPlan) -> bool:
        """
        Validate that execution plan steps are in correct order.

        Args:
            plan: ExecutionPlan to validate

        Returns:
            bool: True if steps are in valid order
        """
        if not plan.execution_plan:
            return True

        for i, step in enumerate(plan.execution_plan):
            if step.step != i + 1:
                logger.warning(
                    f"Invalid step order: expected {i+1}, got {step.step}"
                )
                return False

        return True
