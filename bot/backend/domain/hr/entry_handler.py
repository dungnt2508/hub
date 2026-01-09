"""
HR Domain Engine - Entry Handler
"""
from typing import Dict, Any, Optional

from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.exceptions import DomainError, InvalidInputError
from ...shared.logger import logger
from .ports.repository import IHRRepository
from .adapters.postgresql_repository import PostgreSQLHRRepository
from .middleware.rbac import RBACMiddleware
from .use_cases import (
    CreateLeaveRequestUseCase,
    QueryLeaveBalanceUseCase,
    ApproveLeaveUseCase,
    QueryLeaveRequestsUseCase,
    RejectLeaveUseCase,
)


class HREntryHandler:
    """
    Entry point for HR domain engine.
    
    Maps intents to use cases and executes them.
    """
    
    def __init__(self, repository: Optional[IHRRepository] = None, rbac_middleware: Optional[RBACMiddleware] = None):
        """
        Initialize HR entry handler with use cases.
        
        Args:
            repository: HR repository (defaults to PostgreSQLHRRepository)
            rbac_middleware: RBAC middleware (optional, will be created if not provided)
        """
        # Initialize repository if not provided
        if repository is None:
            repository = PostgreSQLHRRepository()
        
        # Initialize RBAC middleware if not provided
        if rbac_middleware is None:
            rbac_middleware = RBACMiddleware(repository)
        
        # Initialize use cases with repository and RBAC injection
        self.use_cases = {
            "create_leave_request": CreateLeaveRequestUseCase(repository, rbac_middleware),
            "query_leave_balance": QueryLeaveBalanceUseCase(repository, rbac_middleware),
            "query_leave_requests": QueryLeaveRequestsUseCase(repository, rbac_middleware),
            "approve_leave": ApproveLeaveUseCase(repository, rbac_middleware),
            "reject_leave": RejectLeaveUseCase(repository, rbac_middleware),
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

