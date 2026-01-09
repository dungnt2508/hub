"""
Query Leave Requests Use Case
"""
from datetime import datetime
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import DomainError, InvalidInputError, AuthorizationError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.repository import IHRRepository
from ..middleware.rbac import RBACMiddleware


class QueryLeaveRequestsUseCase(BaseUseCase):
    """Use case for querying leave requests"""
    
    def __init__(self, repository: IHRRepository, rbac_middleware: Optional[RBACMiddleware] = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (required, injected)
            rbac_middleware: RBAC middleware (optional, will be created if not provided)
        """
        if repository is None:
            raise ValueError("Repository is required for QueryLeaveRequestsUseCase")
        self.repository = repository
        self.rbac = rbac_middleware or RBACMiddleware(repository)
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute query leave requests.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response with list of leave requests
            
        Raises:
            InvalidInputError: If user_id is missing
            DomainError: If employee not found
        """
        user_id = request.user_context.get("user_id")
        
        if not user_id:
            raise InvalidInputError("user_id is required in user_context")
        
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
                f"Permission denied for query leave requests: {e}",
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
                f"Employee not found for user_id: {query_user_id}",
                extra={"user_id": query_user_id, "trace_id": request.trace_id}
            )
            raise DomainError(f"Không tìm thấy thông tin nhân viên với user_id: {query_user_id}")
        
        # Get status filter if provided
        status_filter = request.slots.get("status")  # e.g., "pending", "approved", "rejected"
        
        # Get pagination parameters
        limit = request.slots.get("limit", 50)
        offset = request.slots.get("offset", 0)
        
        # Get leave requests from repository
        leave_requests = await self.repository.get_leave_requests(
            employee_id=employee.employee_id,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Query leave requests successful: {len(leave_requests)} requests found",
            extra={
                "user_id": user_id,
                "employee_id": employee.employee_id,
                "status_filter": status_filter,
                "count": len(leave_requests),
                "trace_id": request.trace_id
            }
        )
        
        # Format leave requests for response
        formatted_requests = [
            {
                "leave_request_id": lr.leave_request_id,
                "start_date": lr.start_date.isoformat() if lr.start_date else None,
                "end_date": lr.end_date.isoformat() if lr.end_date else None,
                "reason": lr.reason,
                "status": lr.status,
                "approved_by": lr.approved_by,
                "created_at": lr.created_at,
            }
            for lr in leave_requests
        ]
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_requests": formatted_requests,
                "total_count": len(leave_requests),
                "limit": limit,
                "offset": offset,
                "user_id": user_id,
                "employee_name": employee.name,
            },
            message=f"Tìm thấy {len(leave_requests)} đơn xin nghỉ phép",
            audit={
                "policy_checked": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

