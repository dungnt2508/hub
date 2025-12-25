"""
HR Domain Engine - Entry Handler
"""
from typing import Dict, Any

from backend.schemas import DomainRequest, DomainResponse, DomainResult
from backend.shared.exceptions import DomainError, InvalidInputError
from backend.shared.logger import logger
from backend.domain.hr.use_cases import (
    CreateLeaveRequestUseCase,
    QueryLeaveBalanceUseCase,
    ApproveLeaveUseCase,
)


class HREntryHandler:
    """
    Entry point for HR domain engine.
    
    Maps intents to use cases and executes them.
    """
    
    def __init__(self):
        """Initialize HR entry handler with use cases"""
        self.use_cases = {
            "create_leave_request": CreateLeaveRequestUseCase(),
            "query_leave_balance": QueryLeaveBalanceUseCase(),
            "approve_leave": ApproveLeaveUseCase(),
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
                "HR domain request received",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "user_id": request.user_context.get("user_id"),
                }
            )
            
            # Validate intent exists
            if request.intent not in self.use_cases:
                raise InvalidInputError(
                    f"Unknown HR intent: {request.intent}"
                )
            
            # Get use case
            use_case = self.use_cases[request.intent]
            
            # Execute use case
            result = await use_case.execute(request)
            
            logger.info(
                "HR domain request completed",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "status": result.status.value,
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"HR domain error: {e}",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                },
                exc_info=True
            )
            raise DomainError(f"HR domain handling failed: {e}") from e

