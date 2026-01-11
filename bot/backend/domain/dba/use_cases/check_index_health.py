"""
Check Index Health Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.index_health import IndexHealth


class CheckIndexHealthUseCase(BaseUseCase):
    """Use case for checking index health"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for CheckIndexHealthUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute check index health (implementation).
        
        Args:
            request: Domain request with slots:
                - connection_string: Database connection string (optional)
                - schema: Schema name (optional)
            db_type: Validated database type
                
        Returns:
            Dict with data and message
            
        Raises:
            DomainError: If check fails
        """
        try:
            # Extract slots
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            schema = request.slots.get("schema")
            
            # Get index stats via MCP
            index_stats_data = await self.mcp_client.get_index_stats(
                db_type=db_type,
                connection_string=connection_string,
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id,
                schema=schema
            )
            
            # Create entities
            indexes = [
                IndexHealth.from_dict(idx) for idx in index_stats_data
            ]
            
            # Analyze health
            unhealthy_indexes = [idx for idx in indexes if idx.is_unhealthy()]
            total_indexes = len(indexes)
            unhealthy_count = len(unhealthy_indexes)
            
            message = (
                f"Phát hiện {unhealthy_count}/{total_indexes} index không khỏe mạnh trong {db_type.value}"
                if unhealthy_count > 0
                else f"Tất cả {total_indexes} index đều khỏe mạnh trong {db_type.value}"
            )
            
            return {
                "data": {
                    "indexes": [idx.to_dict() for idx in indexes],
                    "unhealthy_indexes": [idx.to_dict() for idx in unhealthy_indexes],
                    "total_indexes": total_indexes,
                    "unhealthy_count": unhealthy_count,
                    "db_type": db_type.value,
                },
                "message": message,
            }
            
        except Exception as e:
            logger.error(
                f"Error checking index health: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to check index health: {e}") from e

