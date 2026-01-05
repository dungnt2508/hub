"""
Query Leave Balance Use Case
"""
from datetime import datetime
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import DomainError, InvalidInputError, AuthorizationError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..entities import Employee
from ..ports.repository import IHRRepository
from ..middleware.rbac import RBACMiddleware


class QueryLeaveBalanceUseCase(BaseUseCase):
    """Use case for querying employee leave balance"""
    
    def __init__(self, repository: IHRRepository, rbac_middleware: Optional[RBACMiddleware] = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (required, injected)
            rbac_middleware: RBAC middleware (optional, will be created if not provided)
        """
        if repository is None:
            raise ValueError("Repository is required for QueryLeaveBalanceUseCase")
        self.repository = repository
        self.rbac = rbac_middleware or RBACMiddleware(repository)
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute query leave balance.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response with leave balance
            
        Raises:
            InvalidInputError: If user_id is missing
            DomainError: If employee not found
        """
        user_id = request.user_context.get("user_id")
        
        if not user_id:
            raise InvalidInputError("user_id is required in user_context")
        
        # Check if user is querying their own balance or has permission to query others
        # Extract target_user_id from slots if provided (for manager/admin querying others)
        target_user_id = request.slots.get("target_user_id") or request.user_context.get("target_user_id")
        
        # Enforce RBAC: Check permission to query employee info
        try:
            await self.rbac.enforce_query_employee_permission(
                requester_user_id=user_id,
                target_user_id=target_user_id
            )
        except AuthorizationError as e:
            logger.warning(
                f"Permission denied for query leave balance: {e}",
                extra={
                    "requester_user_id": user_id,
                    "target_user_id": target_user_id,
                    "trace_id": request.trace_id
                }
            )
            raise
        
        # Use target_user_id if provided, otherwise use requester's user_id
        query_user_id = target_user_id or user_id
        
        # Get employee from repository
        employee = await self.repository.get_employee(query_user_id)
        
        if not employee:
            logger.warning(
                f"Employee not found for user_id: {user_id}",
                extra={"user_id": user_id, "trace_id": request.trace_id}
            )
            raise DomainError(f"Không tìm thấy thông tin nhân viên với user_id: {user_id}")
        
        leave_balance = employee.leave_balance
        
        logger.info(
            f"Query leave balance successful: {leave_balance} days",
            extra={
                "user_id": user_id,
                "employee_id": employee.employee_id,
                "leave_balance": leave_balance,
                "trace_id": request.trace_id
            }
        )
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_balance": leave_balance,
                "user_id": user_id,
                "employee_name": employee.name,
            },
            message=f"Bạn còn {leave_balance} ngày phép",
            audit={
                "policy_checked": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

