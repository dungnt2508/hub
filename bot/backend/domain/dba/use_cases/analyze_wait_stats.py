"""
Analyze Wait Stats Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.wait_stat import WaitStat


class AnalyzeWaitStatsUseCase(BaseUseCase):
    """Use case for analyzing wait statistics"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for AnalyzeWaitStatsUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute analyze wait stats (implementation).
        
        Args:
            request: Domain request
            db_type: Validated database type
                
        Returns:
            Dict with data and message
        """
        try:
            # Extract slots
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            
            # Get wait stats via MCP
            wait_stats_data = await self.mcp_client.get_wait_stats(
                db_type=db_type,
                connection_string=connection_string,
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id
            )
            
            # Parse wait stats data
            # Handle both list and dict responses
            wait_stats_list = []
            if isinstance(wait_stats_data, dict):
                # If it's a dict, check for a list inside
                if "wait_stats" in wait_stats_data:
                    wait_stats_list = wait_stats_data.get("wait_stats", [])
                    if not isinstance(wait_stats_list, list):
                        wait_stats_list = [wait_stats_data]
                else:
                    wait_stats_list = [wait_stats_data]
            elif isinstance(wait_stats_data, list):
                wait_stats_list = wait_stats_data
            
            # Create entities
            wait_stats = [
                WaitStat.from_dict(w) for w in wait_stats_list if isinstance(w, dict)
            ]
            
            # Identify top wait events
            sorted_by_total = sorted(
                wait_stats,
                key=lambda x: x.total_wait_time_ms or 0,
                reverse=True
            )[:5]
            
            stats_count = len(wait_stats)
            message = (
                f"Phân tích wait stats cho {db_type.value}: "
                f"Tìm thấy {stats_count} loại wait event"
                if stats_count > 0
                else f"Không tìm thấy wait stats cho {db_type.value}"
            )
            
            return {
                "data": {
                    "wait_stats": [w.to_dict() for w in wait_stats],
                    "top_wait_events": [w.to_dict() for w in sorted_by_total],
                    "stats_count": stats_count,
                    "db_type": db_type.value,
                },
                "message": message,
            }
            
        except Exception as e:
            logger.error(
                f"Error analyzing wait stats: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to analyze wait stats: {e}") from e
