"""
RBAC Middleware for HR Domain

Enforces role-based access control for HR operations.
"""
from typing import Optional
from ..entities import Employee
from ..ports.repository import IHRRepository
from ....shared.exceptions import AuthorizationError
from ....shared.logger import logger


class PermissionChecker:
    """
    Permission checker for HR domain operations.
    
    Checks if user has permission to perform specific actions.
    """
    
    def __init__(self, repository: IHRRepository):
        """
        Initialize permission checker.
        
        Args:
            repository: HR repository to get employee info
        """
        self.repository = repository
    
    async def can_query_employee(
        self,
        requester_user_id: str,
        target_user_id: Optional[str] = None
    ) -> bool:
        """
        Check if requester can query employee information.
        
        Rules:
        - Employee can only query their own info
        - Manager can query info of employees in their department
        - Admin can query any employee info
        
        Args:
            requester_user_id: User ID of the requester
            target_user_id: User ID of the target employee (None = self)
            
        Returns:
            True if allowed, False otherwise
            
        Raises:
            AuthorizationError: If permission denied (with reason)
        """
        # Get requester info
        requester = await self.repository.get_employee(requester_user_id)
        if not requester:
            raise AuthorizationError(f"Requester not found: {requester_user_id}")
        
        # If no target specified, requester is querying themselves (always allowed)
        if not target_user_id or target_user_id == requester_user_id:
            return True
        
        # Admin can query anyone
        if requester.role == "admin":
            return True
        
        # Manager can query employees in their department
        if requester.role == "manager":
            target = await self.repository.get_employee(target_user_id)
            if not target:
                raise AuthorizationError(f"Target employee not found: {target_user_id}")
            
            # Manager can query employees in same department
            if target.department == requester.department:
                return True
            
            # Manager cannot query employees from other departments
            raise AuthorizationError(
                f"Manager can only query employees in their department ({requester.department}). "
                f"Target employee is in {target.department}."
            )
        
        # Regular employee can only query themselves
        raise AuthorizationError(
            "Bạn chỉ có thể xem thông tin của chính mình. "
            "Chỉ manager hoặc admin mới có thể xem thông tin của nhân viên khác."
        )
    
    async def can_approve_leave(
        self,
        approver_user_id: str
    ) -> bool:
        """
        Check if user can approve leave requests.
        
        Rules:
        - Only managers and admins can approve
        
        Args:
            approver_user_id: User ID of the approver
            
        Returns:
            True if allowed, False otherwise
            
        Raises:
            AuthorizationError: If permission denied
        """
        approver = await self.repository.get_employee(approver_user_id)
        if not approver:
            raise AuthorizationError(f"Approver not found: {approver_user_id}")
        
        if approver.role not in ["manager", "admin"]:
            raise AuthorizationError(
                f"Bạn không có quyền duyệt đơn nghỉ phép. "
                f"Chỉ manager hoặc admin mới có quyền này. "
                f"Role hiện tại: {approver.role}"
            )
        
        return True
    
    async def can_reject_leave(
        self,
        rejector_user_id: str
    ) -> bool:
        """
        Check if user can reject leave requests.
        
        Rules:
        - Only managers and admins can reject
        
        Args:
            rejector_user_id: User ID of the rejector
            
        Returns:
            True if allowed, False otherwise
            
        Raises:
            AuthorizationError: If permission denied
        """
        rejector = await self.repository.get_employee(rejector_user_id)
        if not rejector:
            raise AuthorizationError(f"Rejector not found: {rejector_user_id}")
        
        if rejector.role not in ["manager", "admin"]:
            raise AuthorizationError(
                f"Bạn không có quyền từ chối đơn nghỉ phép. "
                f"Chỉ manager hoặc admin mới có quyền này. "
                f"Role hiện tại: {rejector.role}"
            )
        
        return True
    
    async def can_create_leave_request(
        self,
        user_id: str
    ) -> bool:
        """
        Check if user can create leave request.
        
        Rules:
        - All employees can create leave requests for themselves
        
        Args:
            user_id: User ID
            
        Returns:
            True if allowed (all employees can)
            
        Raises:
            AuthorizationError: If employee not found
        """
        employee = await self.repository.get_employee(user_id)
        if not employee:
            raise AuthorizationError(f"Employee not found: {user_id}")
        
        # All employees can create leave requests
        return True
    
    async def can_view_leave_request(
        self,
        requester_user_id: str,
        leave_request_employee_id: str
    ) -> bool:
        """
        Check if user can view a specific leave request.
        
        Rules:
        - Employee can view their own leave requests
        - Manager can view leave requests of employees in their department
        - Admin can view any leave request
        
        Args:
            requester_user_id: User ID of the requester
            leave_request_employee_id: Employee ID who owns the leave request
            
        Returns:
            True if allowed
            
        Raises:
            AuthorizationError: If permission denied
        """
        requester = await self.repository.get_employee(requester_user_id)
        if not requester:
            raise AuthorizationError(f"Requester not found: {requester_user_id}")
        
        # Get employee who owns the leave request
        leave_request_owner = await self.repository.get_employee_by_employee_id(leave_request_employee_id)
        if not leave_request_owner:
            raise AuthorizationError(f"Leave request owner not found: {leave_request_employee_id}")
        
        # If requester owns the leave request, allow
        if leave_request_owner.user_id == requester_user_id:
            return True
        
        # Admin can view any leave request
        if requester.role == "admin":
            return True
        
        # Manager can view leave requests of employees in their department
        if requester.role == "manager":
            if leave_request_owner.department == requester.department:
                return True
            raise AuthorizationError(
                f"Manager can only view leave requests of employees in their department ({requester.department})"
            )
        
        # Regular employee can only view their own
        raise AuthorizationError(
            "Bạn chỉ có thể xem đơn nghỉ phép của chính mình."
        )


class RBACMiddleware:
    """
    RBAC Middleware for HR domain.
    
    Wraps permission checking logic and provides easy-to-use interface.
    """
    
    def __init__(self, repository: IHRRepository):
        """
        Initialize RBAC middleware.
        
        Args:
            repository: HR repository
        """
        self.permission_checker = PermissionChecker(repository)
    
    async def enforce_query_employee_permission(
        self,
        requester_user_id: str,
        target_user_id: Optional[str] = None
    ) -> None:
        """
        Enforce permission to query employee info.
        
        Raises AuthorizationError if not allowed.
        """
        await self.permission_checker.can_query_employee(requester_user_id, target_user_id)
    
    async def enforce_approve_leave_permission(
        self,
        approver_user_id: str
    ) -> None:
        """
        Enforce permission to approve leave requests.
        
        Raises AuthorizationError if not allowed.
        """
        await self.permission_checker.can_approve_leave(approver_user_id)
    
    async def enforce_create_leave_request_permission(
        self,
        user_id: str
    ) -> None:
        """
        Enforce permission to create leave request.
        
        Raises AuthorizationError if not allowed.
        """
        await self.permission_checker.can_create_leave_request(user_id)
    
    async def enforce_view_leave_request_permission(
        self,
        requester_user_id: str,
        leave_request_employee_id: str
    ) -> None:
        """
        Enforce permission to view leave request.
        
        Raises AuthorizationError if not allowed.
        """
        await self.permission_checker.can_view_leave_request(requester_user_id, leave_request_employee_id)
    
    async def enforce_reject_leave_permission(
        self,
        rejector_user_id: str
    ) -> None:
        """
        Enforce permission to reject leave requests.
        
        Raises AuthorizationError if not allowed.
        """
        await self.permission_checker.can_reject_leave(rejector_user_id)

