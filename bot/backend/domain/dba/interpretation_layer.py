"""
Interpretation Layer - Analyzes raw database results using LLM

CRITICAL: 
- ONLY called AFTER raw DB results are available
- Input: ExecutionPlan + ExecutionResult + Playbook Rules
- Output: STRUCTURED findings and recommendations
- LLM does NOT: generate SQL, modify queries, suggest DDL, exceed read-only scope

Flow:
1. Receive ExecutionPlan (structure)
2. Receive ExecutionResult (raw data from DB)
3. Receive Playbook Rules (analysis rules)
4. Call LLM with structured prompt
5. Parse LLM response into structured result
6. Validate result structure
7. Return to frontend
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json

from ...schemas import DomainRequest
from ...shared.logger import logger
from ...shared.exceptions import DomainError
from .execution_plan_generator import ExecutionPlan
from .db_executor import ExecutionResult, StepExecutionResult


@dataclass
class Finding:
    """Single finding from interpretation"""
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    title: str
    description: str
    affected_objects: Optional[List[str]] = None


@dataclass
class Recommendation:
    """Single recommendation for action"""
    type: str  # "safe", "risky", "blocked"
    description: str
    priority: str  # "HIGH", "MEDIUM", "LOW"
    estimated_impact: Optional[str] = None


@dataclass
class InterpretationResult:
    """Final interpretation result from LLM analysis"""
    playbook: str
    connection_id: str
    generated_at: str = ""
    summary: str = ""
    findings: List[Finding] = field(default_factory=list)
    risk_observations: List[str] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    next_steps: Optional[str] = None
    llm_model: str = "claude"
    processing_time_ms: int = 0

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "playbook": self.playbook,
            "connection_id": self.connection_id,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "findings": [asdict(f) for f in self.findings],
            "risk_observations": self.risk_observations,
            "recommendations": [asdict(r) for r in self.recommendations],
            "next_steps": self.next_steps,
            "llm_model": self.llm_model,
            "processing_time_ms": self.processing_time_ms,
        }


class InterpretationLayer:
    """
    Interprets raw database execution results using LLM.

    Input:
    - ExecutionPlan (what we ran)
    - ExecutionResult (what we got)
    - Playbook Rules (analysis rules)

    Output:
    - InterpretationResult (structured findings + recommendations)

    CONSTRAINTS:
    - NO SQL generation
    - NO query modification
    - NO DDL suggestions
    - Read-only scope only
    - Structured output only
    """

    def __init__(self, llm_client=None):
        """
        Initialize interpretation layer.

        Args:
            llm_client: Optional LLM client (for future use)
        """
        self.llm_client = llm_client
        self.playbook_rules = self._init_playbook_rules()

    def _init_playbook_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize interpretation rules for each playbook.

        These rules guide LLM analysis without generating SQL.
        """
        return {
            "QUERY_PERFORMANCE": {
                "severity_thresholds": {
                    "avg_time_ms": {
                        "critical": 5000,
                        "high": 2000,
                        "medium": 500,
                    },
                    "execution_count": {
                        "critical": 10000,
                        "high": 5000,
                    },
                },
                "analysis_focus": [
                    "Identify slowest queries by average execution time",
                    "Find queries with high execution counts but poor plan",
                    "Detect missing indexes in execution plans",
                    "Flag queries with high IO usage",
                ],
                "recommendation_rules": [
                    {
                        "condition": "avg_time_ms > 5000",
                        "action": "Review execution plan and consider query rewrite",
                        "type": "safe",
                    },
                    {
                        "condition": "avg_time_ms > 2000 and execution_count > 1000",
                        "action": "Analyze query pattern - high volume slow query",
                        "type": "safe",
                    },
                ],
            },
            "INDEX_HEALTH": {
                "severity_thresholds": {
                    "fragmentation_percent": {
                        "critical": 30,
                        "high": 15,
                        "medium": 10,
                    },
                },
                "analysis_focus": [
                    "Identify highly fragmented indexes (>30%)",
                    "Find unused indexes consuming space",
                    "Detect missing indexes on frequently scanned tables",
                ],
                "recommendation_rules": [
                    {
                        "condition": "fragmentation > 30%",
                        "action": "Rebuild index (offline during maintenance window)",
                        "type": "safe",
                    },
                    {
                        "condition": "fragmentation 10-30%",
                        "action": "Reorganize index online",
                        "type": "safe",
                    },
                ],
            },
            "BLOCKING_ANALYSIS": {
                "analysis_focus": [
                    "Identify blocked vs blocking sessions",
                    "Detect long-running transactions",
                    "Find lock escalation patterns",
                ],
                "recommendation_rules": [
                    {
                        "condition": "blocking_time > 60000ms",
                        "action": "Investigate blocking process - may need to kill session",
                        "type": "safe",
                    },
                ],
            },
            "WAIT_STATISTICS": {
                "analysis_focus": [
                    "Identify top wait types by percentage",
                    "Detect IO waits (PAGEIOLATCH_*)",
                    "Find CPU saturation (SOS_SCHEDULER_YIELD)",
                    "Analyze lock waits (LCK_*)",
                ],
                "recommendation_rules": [
                    {
                        "condition": "PAGEIOLATCH wait > 50%",
                        "action": "High IO wait - review disk performance and queries",
                        "type": "safe",
                    },
                ],
            },
        }

    async def interpret(
        self,
        execution_plan: ExecutionPlan,
        execution_result: ExecutionResult,
        playbook_name: str,
        connection_id: str,
    ) -> InterpretationResult:
        """
        Interpret execution results using LLM.

        Args:
            execution_plan: The plan that was executed
            execution_result: Raw results from database execution
            playbook_name: Name of the playbook
            connection_id: Database connection ID

        Returns:
            InterpretationResult: Structured analysis and recommendations

        Raises:
            DomainError: If interpretation fails
        """
        import time
        start_time = time.time()

        try:
            result = InterpretationResult(
                playbook=playbook_name,
                connection_id=connection_id,
            )

            # Check if execution was successful
            if execution_result.status == "failure":
                result.summary = f"Execution failed: {execution_result.error}"
                result.findings.append(
                    Finding(
                        severity="CRITICAL",
                        title="Execution Failed",
                        description=execution_result.error or "Unknown error",
                    )
                )
                return result

            # Check if we have execution results
            if not execution_result.step_results:
                result.summary = "No execution results available"
                return result

            # Get playbook rules
            rules = self.playbook_rules.get(playbook_name, {})

            # Prepare context for LLM
            context = self._build_interpretation_context(
                execution_plan=execution_plan,
                execution_result=execution_result,
                playbook_name=playbook_name,
                rules=rules,
            )

            logger.debug(
                f"Interpretation context prepared",
                extra={
                    "playbook": playbook_name,
                    "step_count": len(execution_result.step_results),
                }
            )

            # Call LLM for analysis
            llm_response = await self._call_llm_for_analysis(context)

            # Parse LLM response into structured result
            if llm_response:
                result = self._parse_llm_response(
                    llm_response,
                    playbook_name,
                    connection_id,
                )

                # Validate result structure
                if not result.summary:
                    result.summary = "Analysis completed"

            else:
                # Fallback analysis without LLM
                result = self._generate_fallback_analysis(
                    execution_result,
                    playbook_name,
                    connection_id,
                    rules,
                )

            logger.info(
                f"Interpretation complete",
                extra={
                    "playbook": playbook_name,
                    "findings": len(result.findings),
                    "recommendations": len(result.recommendations),
                }
            )

            return result

        except Exception as e:
            logger.error(
                f"Interpretation failed: {e}",
                extra={"playbook": playbook_name},
                exc_info=True
            )
            raise DomainError(f"Failed to interpret results: {e}") from e

        finally:
            elapsed = time.time() - start_time
            result.processing_time_ms = int(elapsed * 1000)

    def _build_interpretation_context(
        self,
        execution_plan: ExecutionPlan,
        execution_result: ExecutionResult,
        playbook_name: str,
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build context for LLM interpretation.

        Returns context that guides LLM without allowing SQL generation.
        """
        context = {
            "playbook": playbook_name,
            "execution_plan": execution_plan.to_dict(),
            "execution_results": execution_result.to_dict(),
            "analysis_rules": rules,
            "constraints": [
                "MUST NOT generate SQL queries",
                "MUST NOT modify or propose query changes",
                "MUST NOT suggest DDL operations",
                "MUST NOT exceed read-only scope",
                "MUST provide structured findings only",
                "MUST categorize findings by severity",
            ],
        }
        return context

    async def _call_llm_for_analysis(
        self, context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Call LLM for analysis.

        Args:
            context: Interpretation context

        Returns:
            LLM response or None if LLM not available
        """
        # TODO: Integrate with actual LLM service
        # For now, return None to use fallback analysis
        logger.debug("LLM analysis placeholder - using fallback")
        return None

    def _parse_llm_response(
        self,
        llm_response: str,
        playbook_name: str,
        connection_id: str,
    ) -> InterpretationResult:
        """
        Parse LLM response into structured result.

        Args:
            llm_response: Raw LLM response
            playbook_name: Playbook name
            connection_id: Connection ID

        Returns:
            InterpretationResult with parsed data
        """
        result = InterpretationResult(
            playbook=playbook_name,
            connection_id=connection_id,
        )

        try:
            # Try to parse as JSON
            parsed = json.loads(llm_response)

            if "summary" in parsed:
                result.summary = parsed["summary"]

            if "findings" in parsed and isinstance(parsed["findings"], list):
                for f in parsed["findings"]:
                    result.findings.append(
                        Finding(
                            severity=f.get("severity", "INFO"),
                            title=f.get("title", ""),
                            description=f.get("description", ""),
                            affected_objects=f.get("affected_objects"),
                        )
                    )

            if "recommendations" in parsed and isinstance(parsed["recommendations"], list):
                for r in parsed["recommendations"]:
                    result.recommendations.append(
                        Recommendation(
                            type=r.get("type", "safe"),
                            description=r.get("description", ""),
                            priority=r.get("priority", "MEDIUM"),
                            estimated_impact=r.get("estimated_impact"),
                        )
                    )

            if "risk_observations" in parsed and isinstance(parsed["risk_observations"], list):
                result.risk_observations = parsed["risk_observations"]

        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            result.summary = llm_response

        return result

    def _generate_fallback_analysis(
        self,
        execution_result: ExecutionResult,
        playbook_name: str,
        connection_id: str,
        rules: Dict[str, Any],
    ) -> InterpretationResult:
        """
        Generate basic analysis without LLM.

        Args:
            execution_result: Execution results
            playbook_name: Playbook name
            connection_id: Connection ID
            rules: Playbook analysis rules

        Returns:
            InterpretationResult with basic analysis
        """
        result = InterpretationResult(
            playbook=playbook_name,
            connection_id=connection_id,
            summary=f"Database analysis for {playbook_name} completed",
        )

        # Analyze successful vs failed steps
        successful_steps = [r for r in execution_result.step_results if r.status == "success"]
        failed_steps = [r for r in execution_result.step_results if r.status == "failure"]

        if failed_steps:
            for step in failed_steps:
                result.findings.append(
                    Finding(
                        severity="MEDIUM",
                        title=f"Step {step.step} Failed",
                        description=step.error or "Unknown error",
                    )
                )

        # Count data points
        total_rows = sum(r.rows for r in successful_steps)
        result.risk_observations.append(f"Analyzed {total_rows} data points across {len(successful_steps)} steps")

        # Add generic recommendation
        if successful_steps:
            result.recommendations.append(
                Recommendation(
                    type="safe",
                    description="Review analysis results above and take appropriate action",
                    priority="MEDIUM",
                )
            )

        return result
