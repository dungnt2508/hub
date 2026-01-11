"""
Analyze IO Pressure Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..config import DBAConfig


class AnalyzeIOPressureUseCase(BaseUseCase):
    """Use case for analyzing I/O pressure"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for AnalyzeIOPressureUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute analyze I/O pressure.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with I/O pressure analysis
            
        Raises:
            InvalidInputError: If db_type is invalid
            DomainError: If analysis fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "postgresql")
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Analyzing I/O pressure for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                }
            )
            
            # Get I/O pressure metrics via MCP
            io_query = self._get_io_pressure_query(db_type)
            
            io_data = await self.mcp_client.execute_query(
                db_type=db_type,
                query=io_query,
                connection_string=connection_string
            )
            
            # Analyze I/O pressure
            io_metrics = self._analyze_io_metrics(io_data)
            
            # Determine status
            status = "high" if io_metrics.get("pressure_level") == "high" else \
                     "medium" if io_metrics.get("pressure_level") == "medium" else "low"
            
            message = (
                f"I/O Pressure Analysis cho {db_type.value}: "
                f"Status = {status.upper()}, "
                f"Read Rate: {io_metrics.get('read_rate_mbps', 0):.2f} MB/s, "
                f"Write Rate: {io_metrics.get('write_rate_mbps', 0):.2f} MB/s"
            )
            
            logger.info(
                f"I/O pressure analysis completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "pressure_level": status,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "io_metrics": io_metrics,
                    "pressure_level": status,
                    "db_type": db_type.value,
                    "recommendations": self._get_recommendations(status, io_metrics),
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error analyzing I/O pressure: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to analyze I/O pressure: {e}") from e
    
    @staticmethod
    def _get_io_pressure_query(db_type: DatabaseType) -> str:
        """Get I/O pressure analysis query for database type"""
        if db_type == DatabaseType.POSTGRESQL:
            return """
                SELECT 
                    schemaname, tablename,
                    heap_blks_read, heap_blks_hit,
                    idx_blks_read, idx_blks_hit
                FROM pg_statio_user_tables
                ORDER BY heap_blks_read DESC
                LIMIT 20
            """
        elif db_type == DatabaseType.MYSQL:
            return """
                SELECT 
                    OBJECT_SCHEMA, OBJECT_NAME,
                    COUNT_READ, COUNT_WRITE,
                    COUNT_INSERT, COUNT_UPDATE, COUNT_DELETE
                FROM performance_schema.table_io_waits_summary_by_table
                ORDER BY COUNT_READ DESC
                LIMIT 20
            """
        elif db_type == DatabaseType.SQLSERVER:
            return """
                SELECT TOP 20
                    OBJECT_NAME(s.object_id) as table_name,
                    s.user_seeks, s.user_scans, s.user_lookups,
                    s.user_updates, s.last_user_seek
                FROM sys.dm_db_index_usage_stats s
                ORDER BY s.user_seeks DESC
            """
        else:
            return "SELECT 1"
    
    @staticmethod
    def _analyze_io_metrics(io_data: list) -> dict:
        """
        Analyze I/O metrics from query results.
        
        Uses DBAConfig thresholds for deterministic pressure level calculation.
        """
        if not io_data:
            return {
                "pressure_level": "low",
                "read_rate_mbps": 0,
                "write_rate_mbps": 0,
                "total_reads": 0,
                "total_writes": 0,
                "high_threshold": DBAConfig.IO_PRESSURE_HIGH_READS_PER_SEC,
                "medium_threshold": DBAConfig.IO_PRESSURE_MEDIUM_READS_PER_SEC,
            }
        
        total_reads = sum(row.get("count_read", row.get("heap_blks_read", 0)) for row in io_data)
        total_writes = sum(row.get("count_write", row.get("user_updates", 0)) for row in io_data)
        
        # Use centralized thresholds from DBAConfig
        pressure_level = DBAConfig.get_io_pressure_level(total_reads)
        
        return {
            "pressure_level": pressure_level,
            "read_rate_mbps": total_reads / 100,  # Simplified
            "write_rate_mbps": total_writes / 100,  # Simplified
            "total_reads": total_reads,
            "total_writes": total_writes,
            "high_threshold": DBAConfig.IO_PRESSURE_HIGH_READS_PER_SEC,
            "medium_threshold": DBAConfig.IO_PRESSURE_MEDIUM_READS_PER_SEC,
            "top_tables": [
                {
                    "table": row.get("tablename", row.get("table_name", row.get("OBJECT_NAME", "unknown"))),
                    "reads": row.get("count_read", row.get("heap_blks_read", 0)),
                    "writes": row.get("count_write", row.get("user_updates", 0)),
                }
                for row in io_data[:5]
            ]
        }
    
    @staticmethod
    def _get_recommendations(pressure_level: str, metrics: dict) -> list:
        """Get I/O optimization recommendations"""
        recommendations = []
        
        if pressure_level == "high":
            recommendations.extend([
                "Xem xét thêm I/O subsystem resources",
                "Kiểm tra xem có slow queries đang gây high I/O pressure",
                "Xem xét caching strategy hoặc thêm memory",
                "Kiểm tra disk configuration, có thể cần SSD upgrade",
            ])
        elif pressure_level == "medium":
            recommendations.extend([
                "Monitor I/O metrics tiếp tục",
                "Optimize slow queries để giảm disk I/O",
                "Xem xét thêm indexes trên frequently scanned tables",
            ])
        else:
            recommendations.append("I/O performance đang tốt, tiếp tục monitor")
        
        return recommendations
