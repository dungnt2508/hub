"""
Detect Deadlock Pattern Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType


class DetectDeadlockPatternUseCase(BaseUseCase):
    """Use case for detecting deadlock patterns"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for DetectDeadlockPatternUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute detect deadlock pattern.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - time_window_hours: Time window to check (default: 24)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with deadlock patterns
            
        Raises:
            InvalidInputError: If db_type is invalid
            DomainError: If detection fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "postgresql")
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            time_window_hours = int(request.slots.get("time_window_hours", 24))
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Detecting deadlock patterns for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "time_window_hours": time_window_hours,
                }
            )
            
            # Execute deadlock detection query via MCP
            # This would be database-specific query that detects deadlock patterns
            deadlock_query = self._get_deadlock_detection_query(db_type)
            
            deadlock_data = await self.mcp_client.execute_query(
                db_type=db_type,
                query=deadlock_query,
                connection_string=connection_string,
                params={"time_window_hours": time_window_hours}
            )
            
            # Analyze patterns
            deadlock_count = len(deadlock_data) if deadlock_data else 0
            
            # Identify patterns (simplified)
            patterns = self._analyze_deadlock_patterns(deadlock_data)
            
            message = (
                f"Phát hiện {deadlock_count} deadlock trong {time_window_hours} giờ trước "
                f"trong {db_type.value}"
                if deadlock_count > 0
                else f"Không phát hiện deadlock trong {time_window_hours} giờ trước "
                     f"trong {db_type.value}"
            )
            
            logger.info(
                f"Deadlock pattern detection completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "deadlock_count": deadlock_count,
                    "pattern_count": len(patterns),
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "deadlocks": deadlock_data,
                    "deadlock_count": deadlock_count,
                    "patterns": patterns,
                    "db_type": db_type.value,
                    "time_window_hours": time_window_hours,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error detecting deadlock patterns: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to detect deadlock patterns: {e}") from e
    
    @staticmethod
    def _get_deadlock_detection_query(db_type: DatabaseType) -> str:
        """
        Get deadlock detection query for database type.
        
        NOTE: Deadlock detection is complex and engine-specific.
        These are best-effort queries. Some may return empty if:
        - PostgreSQL: Need external logging configuration
        - MySQL: Need performance_schema enabled
        - SQL Server: Need proper DMV permissions
        
        Raises InvalidInputError if detection not available.
        """
        if db_type == DatabaseType.POSTGRESQL:
            # PostgreSQL deadlock detection requires:
            # 1. log_min_duration_statement = 0 (or < deadlock query duration)
            # 2. log_lock_waits = on
            # Alternative: Query pg_stat_statements if available
            return """
            SELECT 
                query_start,
                usename,
                query,
                state,
                'deadlock_candidate' as detection_type
            FROM pg_stat_activity
            WHERE state = 'active' 
              AND wait_event_type = 'Lock'
              AND wait_event LIKE '%Deadlock%'
            ORDER BY query_start DESC
            LIMIT 100
            """
        elif db_type == DatabaseType.MYSQL:
            # MySQL deadlock detection via performance_schema
            # Requires: performance_schema enabled
            return """
            SELECT 
                OBJECT_SCHEMA as db_name,
                OBJECT_NAME as table_name,
                COUNT_STAR as conflict_count,
                SUM_TIMER_WAIT / 1000000000000 as total_wait_ms
            FROM performance_schema.table_io_waits_summary_by_table
            WHERE COUNT_STAR > 0
            ORDER BY SUM_TIMER_WAIT DESC
            LIMIT 100
            """
        elif db_type == DatabaseType.SQLSERVER:
            # SQL Server deadlock detection via DMVs
            # Requires: proper DMV access permissions
            return """
            SELECT TOP 100
                es.session_id,
                es.login_name,
                es.login_time,
                r.command,
                r.status,
                r.wait_type,
                r.wait_time_ms,
                t.text as last_query
            FROM sys.dm_exec_sessions es
            LEFT JOIN sys.dm_exec_requests r 
                ON es.session_id = r.session_id
            CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
            WHERE r.wait_type LIKE '%DEADLOCK%'
               OR r.blocking_session_id > 0
            ORDER BY r.wait_time_ms DESC
            """
        else:
            raise InvalidInputError(
                f"Deadlock detection not supported for {db_type.value}"
            )
    
    @staticmethod
    def _analyze_deadlock_patterns(deadlock_data: list) -> list:
        """Analyze deadlock patterns (simplified)"""
        if not deadlock_data:
            return []
        
        # Group by affected tables
        patterns = {}
        for deadlock in deadlock_data:
            table = deadlock.get("table", "unknown")
            if table not in patterns:
                patterns[table] = {"count": 0, "tables": set()}
            patterns[table]["count"] += 1
        
        return [
            {
                "table": table,
                "deadlock_count": info["count"],
                "severity": "high" if info["count"] > 5 else "medium"
            }
            for table, info in patterns.items()
        ]
