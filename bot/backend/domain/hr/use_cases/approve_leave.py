"""
Approve Leave Use Case
"""
from datetime import datetime

from typing import Optional
from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import DomainError, InvalidInputError, AuthorizationError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.repository import IHRRepository
from ..middleware.rbac import RBACMiddleware


class ApproveLeaveUseCase(BaseUseCase):
    """Use case for approving leave request"""
    
    def __init__(self, repository: IHRRepository, rbac_middleware: Optional[RBACMiddleware] = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (required, injected)
            rbac_middleware: RBAC middleware (optional, will be created if not provided)
        """
        if repository is None:
            raise ValueError("Repository is required for ApproveLeaveUseCase")
        self.repository = repository
        self.rbac = rbac_middleware or RBACMiddleware(repository)
        self.required_slots = ["leave_request_id"]
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute approve leave.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response
            
        Raises:
            InvalidInputError: If required slots are missing
            DomainError: If leave request not found or already processed
            AuthorizationError: If user is not authorized (not manager/admin)
        """
        # Validate required slots
        missing_slots = self.validate_slots(request, self.required_slots)
        if missing_slots:
            return DomainResponse(
                status=DomainResult.NEED_MORE_INFO,
                missing_slots=missing_slots,
                message=f"Vui lòng cung cấp: {', '.join(missing_slots)}",
            )
        
        user_id = request.user_context.get("user_id")
        if not user_id:
            raise InvalidInputError("user_id is required in user_context")
        
        leave_request_id = request.slots.get("leave_request_id")
        
        # Enforce RBAC: Check permission to approve leave requests
        try:
            await self.rbac.enforce_approve_leave_permission(user_id)
        except AuthorizationError as e:
            logger.warning(
                f"Permission denied for approve leave: {e}",
                extra={
                    "user_id": user_id,
                    "leave_request_id": leave_request_id,
                    "trace_id": request.trace_id
                }
            )
            raise
        
        # Get approver (already verified to be manager/admin by RBAC)
        approver = await self.repository.get_employee(user_id)
        if not approver:
            raise DomainError(f"Không tìm thấy thông tin người duyệt với user_id: {user_id}")
        
        # Get leave request from repository
        leave_request = await self.repository.get_leave_request(leave_request_id)
        if not leave_request:
            raise DomainError(f"Không tìm thấy đơn nghỉ phép với ID: {leave_request_id}")
        
        # Check if already processed
        if leave_request.status != "pending":
            return DomainResponse(
                status=DomainResult.ERROR,
                message=f"Đơn nghỉ phép này đã được xử lý với trạng thái: {leave_request.status}",
                data={
                    "leave_request_id": leave_request_id,
                    "current_status": leave_request.status,
                }
            )
        
        # Update leave request status
        leave_request.status = "approved"
        leave_request.approved_by = approver.employee_id
        
        updated_request = await self.repository.update_leave_request(leave_request)
        
        logger.info(
            f"Approved leave request: {leave_request_id}",
            extra={
                "leave_request_id": leave_request_id,
                "approved_by": user_id,
                "approver_employee_id": approver.employee_id,
                "trace_id": request.trace_id
            }
        )
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_request_id": leave_request_id,
                "status": updated_request.status,
            },
            message="Đã duyệt đơn nghỉ phép thành công",
            audit={
                "policy_checked": True,
                "approved_by": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

