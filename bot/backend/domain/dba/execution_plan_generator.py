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
from .query_templates import QueryTemplates
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
        """Initialize with playbook definitions"""
        self.playbooks = self._init_playbooks()

    def _init_playbooks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize playbook definitions.
        
        Each playbook defines:
        - purpose: What this playbook analyzes
        - risk_factors: What risk conditions trigger it
        - steps: Sequential SQL queries for each database type
        """
        return {
            "QUERY_PERFORMANCE": {
                "purpose": "Analyze slow running queries",
                "risk_factors": ["slow_queries"],
                "steps": self._query_performance_steps(),
            },
            "INDEX_HEALTH": {
                "purpose": "Check index fragmentation and missing indexes",
                "risk_factors": ["index_fragmentation"],
                "steps": self._index_health_steps(),
            },
            "BLOCKING_ANALYSIS": {
                "purpose": "Analyze blocking sessions and locks",
                "risk_factors": ["blocking_detected"],
                "steps": self._blocking_analysis_steps(),
            },
            "WAIT_STATISTICS": {
                "purpose": "Analyze wait events and bottlenecks",
                "risk_factors": ["high_wait_time"],
                "steps": self._wait_statistics_steps(),
            },
            "DEADLOCK_DETECTION": {
                "purpose": "Detect deadlock patterns",
                "risk_factors": ["deadlock_detected"],
                "steps": self._deadlock_detection_steps(),
            },
            "IO_PRESSURE": {
                "purpose": "Analyze disk I/O pressure",
                "risk_factors": ["high_io_pressure"],
                "steps": self._io_pressure_steps(),
            },
            "CAPACITY_PLANNING": {
                "purpose": "Forecast database capacity",
                "risk_factors": ["capacity_warning"],
                "steps": self._capacity_planning_steps(),
            },
        }

    def _query_performance_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for query performance analysis"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get top slow queries",
                    "query": """
                        SELECT TOP 10
                            s.sql_handle,
                            qs.creation_time,
                            qs.last_execution_time,
                            qs.execution_count,
                            qs.total_elapsed_time / 1000000.0 as total_time_ms,
                            qs.total_elapsed_time / 1000000.0 / qs.execution_count as avg_time_ms,
                            qs.total_logical_reads,
                            qs.total_physical_reads,
                            st.text
                        FROM sys.dm_exec_query_stats qs
                        CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
                        ORDER BY qs.total_elapsed_time DESC
                    """,
                    "read_only": True,
                },
                {
                    "step": 2,
                    "purpose": "Get execution plan for slowest query",
                    "query": """
                        SELECT TOP 1
                            qp.query_plan
                        FROM sys.dm_exec_query_stats qs
                        CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
                        ORDER BY qs.total_elapsed_time DESC
                    """,
                    "read_only": True,
                },
                {
                    "step": 3,
                    "purpose": "Get missing indexes",
                    "query": """
                        SELECT TOP 20
                            migs.avg_total_user_cost,
                            migs.avg_user_impact,
                            migs.user_seeks,
                            migs.user_scans,
                            mid.equality_columns,
                            mid.inequality_columns,
                            mid.included_columns,
                            mid.statement as table_name
                        FROM sys.dm_db_missing_index_groups mig
                        INNER JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_id = migs.group_id
                        INNER JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
                        ORDER BY migs.avg_user_impact * migs.user_seeks DESC
                    """,
                    "read_only": True,
                },
            ],
            "postgresql": [
                {
                    "step": 1,
                    "purpose": "Get top slow queries",
                    "query": """
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            max_exec_time,
                            min_exec_time,
                            rows
                        FROM pg_stat_statements
                        ORDER BY mean_exec_time DESC
                        LIMIT 10
                    """,
                    "read_only": True,
                },
                {
                    "step": 2,
                    "purpose": "Get query plans",
                    "query": """
                        SELECT
                            query,
                            calls,
                            total_exec_time
                        FROM pg_stat_statements
                        ORDER BY total_exec_time DESC
                        LIMIT 5
                    """,
                    "read_only": True,
                },
            ],
        }

    def _index_health_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for index health analysis"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get fragmented indexes",
                    "query": """
                        SELECT TOP 20
                            OBJECT_NAME(ips.object_id) as table_name,
                            i.name as index_name,
                            ips.index_type_desc,
                            ips.avg_fragmentation_in_percent,
                            ips.page_count
                        FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
                        INNER JOIN sys.indexes i ON ips.object_id = i.object_id
                            AND ips.index_id = i.index_id
                        WHERE ips.avg_fragmentation_in_percent > 10
                        ORDER BY ips.avg_fragmentation_in_percent DESC
                    """,
                    "read_only": True,
                },
                {
                    "step": 2,
                    "purpose": "Get unused indexes",
                    "query": """
                        SELECT TOP 20
                            OBJECT_NAME(i.object_id) as table_name,
                            i.name as index_name,
                            ISNULL(s.user_updates, 0) as user_updates,
                            ISNULL(s.user_seeks, 0) as user_seeks,
                            ISNULL(s.user_scans, 0) as user_scans,
                            ISNULL(s.user_lookups, 0) as user_lookups
                        FROM sys.indexes i
                        LEFT JOIN sys.dm_db_index_usage_stats s ON i.object_id = s.object_id
                            AND i.index_id = s.index_id
                        WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
                            AND i.index_id > 0
                            AND (ISNULL(s.user_seeks, 0) + ISNULL(s.user_scans, 0) + ISNULL(s.user_lookups, 0) = 0)
                        ORDER BY OBJECT_NAME(i.object_id), i.name
                    """,
                    "read_only": True,
                },
            ],
        }

    def _blocking_analysis_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for blocking analysis"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get current blocking sessions",
                    "query": """
                        SELECT
                            er.session_id,
                            er.status,
                            er.wait_type,
                            er.wait_time_ms,
                            er.blocking_session_id,
                            t.text as last_query
                        FROM sys.dm_exec_requests er
                        CROSS APPLY sys.dm_exec_sql_text(er.sql_handle) t
                        WHERE er.blocking_session_id > 0
                    """,
                    "read_only": True,
                },
                {
                    "step": 2,
                    "purpose": "Get lock information",
                    "query": """
                        SELECT
                            resource_type,
                            request_mode,
                            request_status,
                            COUNT(*) as count
                        FROM sys.dm_tran_locks
                        GROUP BY resource_type, request_mode, request_status
                    """,
                    "read_only": True,
                },
            ],
        }

    def _wait_statistics_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for wait statistics analysis"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get top wait statistics",
                    "query": """
                        SELECT TOP 20
                            wait_type,
                            wait_time_ms,
                            signal_wait_time_ms,
                            waiting_tasks_count,
                            100.0 * wait_time_ms / SUM(wait_time_ms) OVER() as percentage
                        FROM sys.dm_os_wait_stats
                        WHERE wait_type NOT IN (
                            'SLEEP_TASK', 'LAZYWRITER_SLEEP', 'SQLTRACE_BUFFER_FLUSH',
                            'CLR_SEMAPHORE', 'CLR_AUTO_EVENT'
                        )
                        ORDER BY wait_time_ms DESC
                    """,
                    "read_only": True,
                },
            ],
        }

    def _deadlock_detection_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for deadlock detection"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get deadlock graph",
                    "query": """
                        SELECT
                            database_id,
                            name
                        FROM sys.databases
                        WHERE is_read_only = 0
                    """,
                    "read_only": True,
                },
            ],
        }

    def _io_pressure_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for I/O pressure analysis"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get I/O statistics",
                    "query": """
                        SELECT TOP 20
                            OBJECT_NAME(ips.object_id) as table_name,
                            i.name as index_name,
                            ips.page_io_latch_wait_count,
                            ips.page_io_latch_wait_in_ms,
                            ips.tree_page_latch_wait_count,
                            ips.tree_page_latch_wait_in_ms
                        FROM sys.dm_db_index_operational_stats(DB_ID(), NULL, NULL, NULL) ips
                        INNER JOIN sys.indexes i ON ips.object_id = i.object_id
                            AND ips.index_id = i.index_id
                        WHERE ips.page_io_latch_wait_count > 0
                        ORDER BY ips.page_io_latch_wait_in_ms DESC
                    """,
                    "read_only": True,
                },
            ],
        }

    def _capacity_planning_steps(self) -> Dict[str, List[Dict]]:
        """SQL Server steps for capacity planning"""
        return {
            "sqlserver": [
                {
                    "step": 1,
                    "purpose": "Get database size",
                    "query": """
                        SELECT
                            name as database_name,
                            CAST(SUM(size) * 8 / 1024 AS DECIMAL(10,2)) as size_mb
                        FROM sys.master_files
                        WHERE database_id = DB_ID()
                        GROUP BY name
                    """,
                    "read_only": True,
                },
            ],
        }

    async def generate(
        self,
        playbook_name: str,
        use_case_id: str,
        risk_level: str,
        db_type: str,
        request: Optional[DomainRequest] = None,
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
        if playbook_name not in self.playbooks:
            raise ValueError(f"Unknown playbook: {playbook_name}")

        playbook_def = self.playbooks[playbook_name]
        steps_by_engine = playbook_def["steps"]

        if db_type not in steps_by_engine:
            logger.warning(
                f"No steps defined for {playbook_name} on {db_type}",
                extra={"use_case": use_case_id}
            )
            # Return empty plan for unsupported database type
            return ExecutionPlan(
                playbook=playbook_name,
                risk_level=risk_level,
                execution_plan=[]
            )

        # Build execution plan
        plan = ExecutionPlan(playbook=playbook_name, risk_level=risk_level)

        steps_config = steps_by_engine[db_type]
        for step_config in steps_config:
            step = ExecutionStep(
                step=step_config["step"],
                type="sql",
                purpose=step_config["purpose"],
                engine=db_type,
                read_only=step_config["read_only"],
                query=step_config["query"],
            )
            plan.add_step(step)

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
