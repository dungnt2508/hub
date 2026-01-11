"""
Analyze Slow Query Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.query_analysis import QueryAnalysis


class AnalyzeSlowQueryUseCase(BaseUseCase):
    """Use case for analyzing slow queries"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for AnalyzeSlowQueryUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute analyze slow query (implementation).
        
        Args:
            request: Domain request with slots:
                - connection_string: Database connection string (optional)
                - limit: Maximum number of queries to return (default: 10)
                - min_duration_ms: Minimum duration in ms to consider as slow (default: 1000)
            db_type: Validated database type
                
        Returns:
            Dict with data and message
            
        Raises:
            DomainError: If analysis fails
        """
        try:
            # Extract slots
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            limit = int(request.slots.get("limit", 10))
            min_duration_ms = int(request.slots.get("min_duration_ms", 1000))
            
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
            
            return {
                "data": {
                    "slow_queries": [a.to_dict() for a in analyses],
                    "count": slow_count,
                    "db_type": db_type.value,
                    "min_duration_ms": min_duration_ms,
                },
                "message": message,
            }
            
        except Exception as e:
            logger.error(
                f"Error analyzing slow queries: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to analyze slow queries: {e}") from e

