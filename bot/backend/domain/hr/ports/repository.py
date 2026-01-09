"""
HR Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities import Employee, LeaveRequest


class IHRRepository(ABC):
    """Interface for HR repository"""
    
    @abstractmethod
    async def get_employee(self, user_id: str) -> Optional[Employee]:
        """Get employee by user ID"""
        pass
    
    @abstractmethod
    async def get_employee_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by employee_id (UUID)"""
        pass
    
    @abstractmethod
    async def create_leave_request(self, leave_request: LeaveRequest) -> LeaveRequest:
        """Create leave request"""
        pass
    
    @abstractmethod
    async def get_leave_request(self, leave_request_id: str) -> Optional[LeaveRequest]:
        """Get leave request by ID"""
        pass
    
    @abstractmethod
    async def get_leave_requests(
        self, 
        employee_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LeaveRequest]:
        """Get leave requests for an employee with optional filtering"""
        pass
    
    @abstractmethod
    async def update_leave_request(self, leave_request: LeaveRequest) -> LeaveRequest:
        """Update leave request"""
        pass

