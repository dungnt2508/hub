"""
Detect Blocking Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.blocking_session import BlockingSession
from ..config import DBAConfig


class DetectBlockingUseCase(BaseUseCase):
    """Use case for detecting blocking sessions"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for DetectBlockingUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
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
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            
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
            
            # Analyze critical blocking using centralized threshold
            critical_blocking = [
                block for block in blocking_sessions
                if block.is_critical(threshold_ms=float(DBAConfig.BLOCKING_CRITICAL_THRESHOLD_MS))
            ]
            
            blocking_count = len(blocking_sessions)
            critical_count = len(critical_blocking)
            
            message = (
                f"Phát hiện {blocking_count} blocking session trong {db_type.value}"
                + (f", trong đó {critical_count} session bị block nghiêm trọng" if critical_count > 0 else "")
                if blocking_count > 0
                else f"Không phát hiện blocking session trong {db_type.value}"
            )
            
            return {
                "data": {
                    "blocking_sessions": [block.to_dict() for block in blocking_sessions],
                    "critical_blocking": [block.to_dict() for block in critical_blocking],
                    "blocking_count": blocking_count,
                    "critical_count": critical_count,
                    "critical_threshold_ms": DBAConfig.BLOCKING_CRITICAL_THRESHOLD_MS,
                    "db_type": db_type.value,
                },
                "message": message,
            }
            
        except Exception as e:
            logger.error(
                f"Error detecting blocking: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to detect blocking: {e}") from e

