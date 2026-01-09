"""
Reject Leave Use Case
"""
from datetime import datetime
from typing import Optional

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import DomainError, InvalidInputError, AuthorizationError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.repository import IHRRepository
from ..middleware.rbac import RBACMiddleware


class RejectLeaveUseCase(BaseUseCase):
    """Use case for rejecting leave request"""
    
    def __init__(self, repository: IHRRepository, rbac_middleware: Optional[RBACMiddleware] = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (required, injected)
            rbac_middleware: RBAC middleware (optional, will be created if not provided)
        """
        if repository is None:
            raise ValueError("Repository is required for RejectLeaveUseCase")
        self.repository = repository
        self.rbac = rbac_middleware or RBACMiddleware(repository)
        self.required_slots = ["leave_request_id"]
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute reject leave.
        
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
        rejection_reason = request.slots.get("rejection_reason", "No reason provided")
        
        # Enforce RBAC: Check permission to reject leave requests
        try:
            await self.rbac.enforce_approve_leave_permission(user_id)
        except AuthorizationError as e:
            logger.warning(
                f"Permission denied for reject leave: {e}",
                extra={
                    "user_id": user_id,
                    "leave_request_id": leave_request_id,
                    "trace_id": request.trace_id
                }
            )
            raise
        
        # Get rejector (already verified to be manager/admin by RBAC)
        rejector = await self.repository.get_employee(user_id)
        if not rejector:
            raise DomainError(f"Không tìm thấy thông tin người từ chối với user_id: {user_id}")
        
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
        
        # Update leave request status to rejected
        leave_request.status = "rejected"
        leave_request.approved_by = rejector.employee_id  # Store rejector info
        
        updated_request = await self.repository.update_leave_request(leave_request)
        
        logger.info(
            f"Rejected leave request: {leave_request_id}",
            extra={
                "leave_request_id": leave_request_id,
                "rejected_by": user_id,
                "rejector_employee_id": rejector.employee_id,
                "rejection_reason": rejection_reason,
                "trace_id": request.trace_id
            }
        )
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_request_id": leave_request_id,
                "status": updated_request.status,
                "rejection_reason": rejection_reason,
            },
            message="Đã từ chối đơn xin nghỉ phép",
            audit={
                "policy_checked": True,
                "rejected_by": user_id,
                "rejection_reason": rejection_reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

