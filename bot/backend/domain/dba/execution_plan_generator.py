"""
Execution Plan Generator - Creates structured execution plans for DBA playbooks

Purpose:
- Takes risk assessment result (GO or GO-WITH-CONDITIONS)
- Generates a structured JSON execution plan with sequential steps
- NO free-form text, only structured objects
- Playbook determines the SQL queries and step order
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json

from ...schemas import DomainRequest
from ...shared.logger import logger
from ...infrastructure.dba_query_template_repository import dba_query_template_repository
from .ports.mcp_client import DatabaseType


@dataclass
class ExecutionStep:
    """Single step in execution plan"""
    step: int
    type: str  # "sql", "diagnostic", "validation"
    purpose: str
    engine: str  # "sqlserver", "postgresql", "mysql", etc.
    read_only: bool
    query: str
    timeout_seconds: int = 300
    depends_on: Optional[List[int]] = None  # Step IDs this depends on


@dataclass
class ExecutionPlan:
    """Structured execution plan for DBA playbook"""
    playbook: str  # e.g., "QUERY_PERFORMANCE", "INDEX_HEALTH"
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    version: str = "1.0"
    generated_at: str = ""
    execution_order: str = "SEQUENTIAL"  # Always sequential, never parallel
    execution_plan: List[ExecutionStep] = field(default_factory=list)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "playbook": self.playbook,
            "risk_level": self.risk_level,
            "version": self.version,
            "generated_at": self.generated_at,
            "execution_order": self.execution_order,
            "execution_plan": [asdict(step) for step in self.execution_plan],
        }

    def add_step(self, step: ExecutionStep):
        """Add a step to the execution plan"""
        self.execution_plan.append(step)


class ExecutionPlanGenerator:
    """
    Generates execution plans based on DBA playbooks and risk assessment.

    Each playbook has a predefined sequence of read-only SQL queries
    that will be executed in order.
    """

    def __init__(self):
        """Initialize with playbook metadata (queries loaded from database)"""
        # Playbook metadata (purpose, risk_factors) - not queries, so kept in code
        self.playbook_metadata = {
            "QUERY_PERFORMANCE": {
                "purpose": "Analyze slow running queries",
                "risk_factors": ["slow_queries"],
            },
            "INDEX_HEALTH": {
                "purpose": "Check index fragmentation and missing indexes",
                "risk_factors": ["index_fragmentation"],
            },
            "BLOCKING_ANALYSIS": {
                "purpose": "Analyze blocking sessions and locks",
                "risk_factors": ["blocking_detected"],
            },
            "WAIT_STATISTICS": {
                "purpose": "Analyze wait events and bottlenecks",
                "risk_factors": ["high_wait_time"],
            },
            "DEADLOCK_DETECTION": {
                "purpose": "Detect deadlock patterns",
                "risk_factors": ["deadlock_detected"],
            },
            "IO_PRESSURE": {
                "purpose": "Analyze disk I/O pressure",
                "risk_factors": ["high_io_pressure"],
            },
            "CAPACITY_PLANNING": {
                "purpose": "Forecast database capacity",
                "risk_factors": ["capacity_warning"],
            },
        }

    async def generate(
        self,
        playbook_name: str,
        use_case_id: str,
        risk_level: str,
        db_type: str,
        request: Optional[DomainRequest] = None,
        query_overrides: Optional[Dict[str, str]] = None,
    ) -> ExecutionPlan:
        """
        Generate execution plan for a playbook.

        Args:
            playbook_name: Name of the playbook (e.g., "QUERY_PERFORMANCE")
            use_case_id: DBA use case ID
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            db_type: Database type (sqlserver, postgresql, mysql)
            request: Optional domain request

        Returns:
            ExecutionPlan: Structured execution plan

        Raises:
            ValueError: If playbook not found
        """
        if playbook_name not in self.playbook_metadata:
            raise ValueError(f"Unknown playbook: {playbook_name}")

        # Build execution plan
        plan = ExecutionPlan(playbook=playbook_name, risk_level=risk_level)

        # Load query templates from database
        try:
            templates = await dba_query_template_repository.get_templates_by_playbook(
                playbook_name=playbook_name,
                db_type=db_type,
                active_only=True
            )
            
            if not templates:
                logger.warning(
                    f"No query templates found in database for {playbook_name} on {db_type}",
                    extra={"use_case": use_case_id, "playbook": playbook_name, "db_type": db_type}
                )
                # Return empty plan if no templates found
                return plan
            
            # Build execution steps from database templates
            for template in templates:
                query_text = template.get('query_text', '')
                
                # Validate query is valid UTF-8
                if isinstance(query_text, bytes):
                    try:
                        query_text = query_text.decode('utf-8')
                    except UnicodeDecodeError as e:
                        logger.error(
                            f"Query encoding error - skipping step",
                            extra={
                                "step": template['step_number'],
                                "playbook": playbook_name,
                                "error": str(e)
                            }
                        )
                        continue
                elif not isinstance(query_text, str):
                    query_text = str(query_text)
                
                step = ExecutionStep(
                    step=template['step_number'],
                    type="sql",
                    purpose=template['purpose'],
                    engine=db_type,
                    read_only=template['read_only'],
                    query=query_text,
                )
                plan.add_step(step)
                
        except Exception as e:
            logger.error(
                f"Error loading query templates from database: {e}",
                extra={"playbook": playbook_name, "db_type": db_type},
                exc_info=True
            )
            # Return empty plan on error
            return plan

        logger.info(
            f"Generated execution plan",
            extra={
                "playbook": playbook_name,
                "use_case": use_case_id,
                "db_type": db_type,
                "step_count": len(plan.execution_plan),
                "risk_level": risk_level,
            }
        )

        return plan


# Singleton instance
execution_plan_generator = ExecutionPlanGenerator()

__all__ = ["ExecutionPlanGenerator", "ExecutionPlan", "ExecutionStep", "execution_plan_generator"]
