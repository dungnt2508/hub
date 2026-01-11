"""
Analyze Query Regression Use Case
"""
from typing import Optional, List, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.query_analysis import QueryAnalysis


class AnalyzeQueryRegressionUseCase(BaseUseCase):
    """Use case for detecting query performance regression"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for AnalyzeQueryRegressionUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute analyze query regression.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - baseline_period_days: Baseline period in days (default: 7)
                - regression_threshold_percent: Regression threshold % (default: 20)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with regressed queries
            
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
            baseline_period_days = int(request.slots.get("baseline_period_days", 7))
            regression_threshold_percent = float(request.slots.get("regression_threshold_percent", 20))
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Analyzing query regression for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "baseline_period_days": baseline_period_days,
                    "regression_threshold": regression_threshold_percent,
                }
            )
            
            # Get current queries
            current_queries_data = await self.mcp_client.get_slow_queries(
                db_type=db_type,
                connection_string=connection_string,
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id,
                limit=50,
                min_duration_ms=500
            )
            
            # Create entities
            current_queries = [
                QueryAnalysis.from_dict(q) for q in current_queries_data
            ]
            
            # Simulate baseline (in real implementation, would fetch from historical data)
            # For now, we'll mark queries with mean_time > 1000ms as potential regressions
            regressed_queries = [
                {
                    "query": q,
                    "regression_percent": self._estimate_regression(q),
                }
                for q in current_queries
                if q.mean_time_ms and q.mean_time_ms > 500
            ]
            
            # Filter by threshold
            significant_regressions = [
                r for r in regressed_queries
                if r["regression_percent"] >= regression_threshold_percent
            ]
            
            regression_count = len(significant_regressions)
            message = (
                f"Phát hiện {regression_count} query có performance regression "
                f"vượt quá {regression_threshold_percent}% trong {db_type.value}"
                if regression_count > 0
                else f"Không phát hiện performance regression trong {db_type.value}"
            )
            
            logger.info(
                f"Query regression analysis completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "regression_count": regression_count,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "regressed_queries": [
                        {
                            "query": r["query"].to_dict(),
                            "regression_percent": r["regression_percent"],
                        }
                        for r in significant_regressions
                    ],
                    "regression_count": regression_count,
                    "db_type": db_type.value,
                    "baseline_period_days": baseline_period_days,
                    "threshold_percent": regression_threshold_percent,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error analyzing query regression: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to analyze query regression: {e}") from e
    
    @staticmethod
    def _estimate_regression(query: QueryAnalysis) -> float:
        """
        Estimate regression percentage (simplified).
        In real implementation, would compare with baseline.
        """
        if query.mean_time_ms is None:
            return 0.0
        
        # Use a simple heuristic: assume baseline was half of current
        baseline = query.mean_time_ms / 1.5
        return ((query.mean_time_ms - baseline) / baseline) * 100
