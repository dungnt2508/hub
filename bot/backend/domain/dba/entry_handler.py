"""
DBA Domain Engine - Entry Handler
"""
from typing import Dict, Any, Optional

from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.exceptions import DomainError, InvalidInputError
from ...shared.logger import logger
from .ports.mcp_client import IMCPDBClient
from .adapters.mcp_db_client import MCPDBClient
from .use_cases import (
    AnalyzeSlowQueryUseCase,
    CheckIndexHealthUseCase,
    DetectBlockingUseCase,
)


class DBAEntryHandler:
    """
    Entry point for DBA domain engine.
    
    Maps intents to use cases and executes them.
    """
    
    def __init__(
        self,
        mcp_client: Optional[IMCPDBClient] = None
    ):
        """
        Initialize DBA entry handler with use cases.
        
        Args:
            mcp_client: MCP DB client (defaults to MCPDBClient)
        """
        # Initialize MCP client if not provided
        if mcp_client is None:
            mcp_client = MCPDBClient()
        
        # Initialize use cases with MCP client injection
        self.use_cases = {
            "analyze_slow_query": AnalyzeSlowQueryUseCase(mcp_client),
            "check_index_health": CheckIndexHealthUseCase(mcp_client),
            "detect_blocking": DetectBlockingUseCase(mcp_client),
            # TODO: Add remaining use cases in Phase 2
            # "analyze_query_regression": AnalyzeQueryRegressionUseCase(mcp_client),
            # "detect_deadlock_pattern": DetectDeadlockPatternUseCase(mcp_client),
            # "analyze_wait_stats": AnalyzeWaitStatsUseCase(mcp_client),
            # "analyze_io_pressure": AnalyzeIOPressureUseCase(mcp_client),
            # "capacity_forecast": CapacityForecastUseCase(mcp_client),
            # "validate_custom_sql": ValidateCustomSQLUseCase(mcp_client),
            # "compare_sp_blitz_vs_custom": CompareSPBlitzVsCustomUseCase(mcp_client),
            # "incident_triage": IncidentTriageUseCase(mcp_client),
        }
    
    async def handle(self, request: DomainRequest) -> DomainResponse:
        """
        Handle domain request.
        
        Args:
            request: Domain request with intent and slots
            
        Returns:
            Domain response with result
            
        Raises:
            DomainError: If handling fails
        """
        try:
            logger.info(
                "DBA domain request received",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "user_id": request.user_context.get("user_id"),
                }
            )
            
            # Validate intent exists
            if request.intent not in self.use_cases:
                raise InvalidInputError(
                    f"Unknown DBA intent: {request.intent}. "
                    f"Available intents: {list(self.use_cases.keys())}"
                )
            
            # Get use case
            use_case = self.use_cases[request.intent]
            
            # Execute use case
            result = await use_case.execute(request)
            
            logger.info(
                "DBA domain request completed",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "status": result.status.value,
                }
            )
            
            return result
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"DBA domain error: {e}",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                },
                exc_info=True
            )
            raise DomainError(f"DBA domain handling failed: {e}") from e

