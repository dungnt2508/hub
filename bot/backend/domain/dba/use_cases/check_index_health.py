"""
Check Index Health Use Case
"""
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.index_health import IndexHealth


class CheckIndexHealthUseCase(BaseUseCase):
    """Use case for checking index health"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        if mcp_client is None:
            raise ValueError("MCP client is required for CheckIndexHealthUseCase")
        self.mcp_client = mcp_client
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute check index health.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - connection_string: Database connection string (optional)
                - schema: Schema name (optional)
                
        Returns:
            Domain response with index health analysis
            
        Raises:
            InvalidInputError: If db_type is invalid
            DomainError: If check fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "postgresql")
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            schema = request.slots.get("schema")
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Checking index health for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "schema": schema,
                }
            )
            
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
            
            logger.info(
                f"Index health check completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "total_indexes": total_indexes,
                    "unhealthy_count": unhealthy_count,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "indexes": [idx.to_dict() for idx in indexes],
                    "unhealthy_indexes": [idx.to_dict() for idx in unhealthy_indexes],
                    "total_indexes": total_indexes,
                    "unhealthy_count": unhealthy_count,
                    "db_type": db_type.value,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error checking index health: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to check index health: {e}") from e

