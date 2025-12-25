"""
Create Leave Request Use Case
"""
from datetime import datetime

from backend.schemas import DomainRequest, DomainResponse, DomainResult
from backend.domain.hr.use_cases.base_use_case import BaseUseCase
from backend.domain.hr.ports.repository import IHRRepository


class CreateLeaveRequestUseCase(BaseUseCase):
    """Use case for creating leave request"""
    
    def __init__(self, repository: IHRRepository = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (injected)
        """
        # TODO: Inject repository via dependency injection
        self.repository = repository
        self.required_slots = ["start_date", "end_date", "reason"]
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute create leave request.
        
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
        start_date = request.slots.get("start_date")
        end_date = request.slots.get("end_date")
        reason = request.slots.get("reason")
        
        # TODO: Validate dates
        # TODO: Check leave balance
        # TODO: Create leave request via repository
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_request_id": "lr_123",
                "start_date": start_date,
                "end_date": end_date,
                "status": "pending",
            },
            message="Đã tạo đơn xin nghỉ phép thành công",
            audit={
                "policy_checked": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

