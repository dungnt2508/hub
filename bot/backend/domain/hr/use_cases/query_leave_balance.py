"""
Query Leave Balance Use Case
"""
from datetime import datetime

from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import BaseUseCase
from ..entities import Employee
from ..ports.repository import IHRRepository


class QueryLeaveBalanceUseCase(BaseUseCase):
    """Use case for querying employee leave balance"""
    
    def __init__(self, repository: IHRRepository = None):
        """
        Initialize use case.
        
        Args:
            repository: HR repository (injected)
        """
        # TODO: Inject repository via dependency injection
        self.repository = repository
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute query leave balance.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response with leave balance
        """
        user_id = request.user_context.get("user_id")
        
        # TODO: Get employee from repository
        # employee = await self.repository.get_employee(user_id)
        # leave_balance = employee.leave_balance
        
        # Mock data for now
        leave_balance = 7
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "leave_balance": leave_balance,
                "user_id": user_id,
            },
            message=f"Bạn còn {leave_balance} ngày phép",
            audit={
                "policy_checked": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

