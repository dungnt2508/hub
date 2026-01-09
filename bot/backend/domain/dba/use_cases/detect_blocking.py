"""
Detect Blocking Use Case
"""
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.blocking_session import BlockingSession


class DetectBlockingUseCase(BaseUseCase):
    """Use case for detecting blocking sessions"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        if mcp_client is None:
            raise ValueError("MCP client is required for DetectBlockingUseCase")
        self.mcp_client = mcp_client
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute detect blocking.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with blocking sessions
            
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
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Detecting blocking in {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                }
            )
            
            # Detect blocking via MCP
            blocking_data = await self.mcp_client.detect_blocking(
                db_type=db_type,
                connection_string=connection_string,
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id
            )
            
            # Create entities
            blocking_sessions = [
                BlockingSession.from_dict(block) for block in blocking_data
            ]
            
            # Analyze critical blocking
            critical_blocking = [
                block for block in blocking_sessions
                if block.is_critical(threshold_ms=5000.0)
            ]
            
            blocking_count = len(blocking_sessions)
            critical_count = len(critical_blocking)
            
            message = (
                f"Phát hiện {blocking_count} blocking session trong {db_type.value}"
                + (f", trong đó {critical_count} session bị block nghiêm trọng" if critical_count > 0 else "")
                if blocking_count > 0
                else f"Không phát hiện blocking session trong {db_type.value}"
            )
            
            logger.info(
                f"Blocking detection completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "blocking_count": blocking_count,
                    "critical_count": critical_count,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "blocking_sessions": [block.to_dict() for block in blocking_sessions],
                    "critical_blocking": [block.to_dict() for block in critical_blocking],
                    "blocking_count": blocking_count,
                    "critical_count": critical_count,
                    "db_type": db_type.value,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error detecting blocking: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to detect blocking: {e}") from e

