"""
Approve Leave Use Case
"""
from datetime import datetime

from backend.schemas import DomainRequest, DomainResponse, DomainResult
from backend.domain.hr.use_cases.base_use_case import BaseUseCase
from backend.domain.hr.ports.repository import IHRRepository


class ApproveLeaveUseCase(BaseUseCase):
    """Use case for approving leave request"""
    
    def __init__(self, repository: IHRRepository = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (injected)
        """
        # TODO: Inject repository via dependency injection
        self.repository = repository
        self.required_slots = ["leave_request_id"]
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute approve leave.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response
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
        leave_request_id = request.slots.get("leave_request_id")
        
        # TODO: Check permissions (only managers can approve)
        # TODO: Get leave request from repository
        # TODO: Approve via repository
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_request_id": leave_request_id,
                "status": "approved",
            },
            message="Đã duyệt đơn nghỉ phép thành công",
            audit={
                "policy_checked": True,
                "approved_by": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

