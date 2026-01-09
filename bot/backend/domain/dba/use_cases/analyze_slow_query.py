"""
Analyze Slow Query Use Case
"""
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.query_analysis import QueryAnalysis


class AnalyzeSlowQueryUseCase(BaseUseCase):
    """Use case for analyzing slow queries"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        if mcp_client is None:
            raise ValueError("MCP client is required for AnalyzeSlowQueryUseCase")
        self.mcp_client = mcp_client
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute analyze slow query.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - connection_string: Database connection string (optional)
                - limit: Maximum number of queries to return (default: 10)
                - min_duration_ms: Minimum duration in ms to consider as slow (default: 1000)
                
        Returns:
            Domain response with slow queries analysis
            
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
            limit = int(request.slots.get("limit", 10))
            min_duration_ms = int(request.slots.get("min_duration_ms", 1000))
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Analyzing slow queries for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "limit": limit,
                    "min_duration_ms": min_duration_ms,
                }
            )
            
            # Get slow queries via MCP
            slow_queries_data = await self.mcp_client.get_slow_queries(
                db_type=db_type,
                connection_string=connection_string,
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id,
                limit=limit,
                min_duration_ms=min_duration_ms
            )
            
            # Create entities
            analyses = [
                QueryAnalysis.from_dict(q) for q in slow_queries_data
            ]
            
            # Build response
            slow_count = len(analyses)
            message = (
                f"Tìm thấy {slow_count} query chạy chậm trong {db_type.value}"
                if slow_count > 0
                else f"Không tìm thấy query chạy chậm trong {db_type.value}"
            )
            
            logger.info(
                f"Slow query analysis completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "slow_query_count": slow_count,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "slow_queries": [a.to_dict() for a in analyses],
                    "count": slow_count,
                    "db_type": db_type.value,
                    "min_duration_ms": min_duration_ms,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error analyzing slow queries: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to analyze slow queries: {e}") from e

