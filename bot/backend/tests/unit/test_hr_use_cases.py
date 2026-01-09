"""
Unit tests for HR domain use cases
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.domain.hr.use_cases import (
    CreateLeaveRequestUseCase,
    QueryLeaveBalanceUseCase,
    ApproveLeaveUseCase,
    QueryLeaveRequestsUseCase,
    RejectLeaveUseCase,
)
from backend.domain.hr.entities import Employee, LeaveRequest
from backend.domain.hr.middleware.rbac import RBACMiddleware
from backend.schemas import DomainRequest, DomainResult
from backend.shared.exceptions import DomainError, InvalidInputError, AuthorizationError


@pytest.fixture
def mock_repository():
    """Create mock HR repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_rbac():
    """Create mock RBAC middleware"""
    rbac = AsyncMock(spec=RBACMiddleware)
    return rbac


@pytest.fixture
def employee_entity():
    """Create sample employee entity"""
    return Employee(
        employee_id=str(uuid4()),
        user_id="user-123",
        name="John Doe",
        email="john@example.com",
        department="Engineering",
        leave_balance=20,
        role="employee"
    )


@pytest.fixture
def manager_entity():
    """Create sample manager entity"""
    return Employee(
        employee_id=str(uuid4()),
        user_id="manager-123",
        name="Jane Manager",
        email="jane@example.com",
        department="Engineering",
        leave_balance=25,
        role="manager"
    )


@pytest.fixture
def leave_request_entity(employee_entity):
    """Create sample leave request"""
    return LeaveRequest(
        leave_request_id=str(uuid4()),
        employee_id=employee_entity.employee_id,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=7),
        reason="Vacation",
        status="pending",
        approved_by=None,
        created_at=datetime.utcnow().isoformat()
    )


class TestQueryLeaveBalanceUseCase:
    """Test QueryLeaveBalanceUseCase"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_repository, mock_rbac, employee_entity):
        """Test successful query leave balance"""
        # Setup
        mock_repository.get_employee.return_value = employee_entity
        use_case = QueryLeaveBalanceUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_balance",
            intent_type="OPERATION",
            slots={},
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        assert response.data["leave_balance"] == 20
        assert response.data["employee_name"] == "John Doe"
        assert response.message == "Bạn còn 20 ngày phép"
    
    @pytest.mark.asyncio
    async def test_execute_missing_user_id(self, mock_repository, mock_rbac):
        """Test query with missing user_id"""
        use_case = QueryLeaveBalanceUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_balance",
            intent_type="OPERATION",
            slots={},
            user_context={},
        )
        
        # Should raise InvalidInputError
        with pytest.raises(InvalidInputError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_employee_not_found(self, mock_repository, mock_rbac):
        """Test query when employee not found"""
        mock_repository.get_employee.return_value = None
        use_case = QueryLeaveBalanceUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_balance",
            intent_type="OPERATION",
            slots={},
            user_context={"user_id": "user-123"},
        )
        
        # Should raise DomainError
        with pytest.raises(DomainError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_permission_denied(self, mock_repository, mock_rbac):
        """Test query with permission denied"""
        mock_rbac.enforce_query_employee_permission.side_effect = AuthorizationError("Permission denied")
        use_case = QueryLeaveBalanceUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_balance",
            intent_type="OPERATION",
            slots={"target_user_id": "user-456"},
            user_context={"user_id": "user-123"},
        )
        
        # Should raise AuthorizationError
        with pytest.raises(AuthorizationError):
            await use_case.execute(request)


class TestCreateLeaveRequestUseCase:
    """Test CreateLeaveRequestUseCase"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_repository, mock_rbac, employee_entity, leave_request_entity):
        """Test successful create leave request"""
        mock_repository.get_employee.return_value = employee_entity
        mock_repository.create_leave_request.return_value = leave_request_entity
        use_case = CreateLeaveRequestUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": (date.today() + timedelta(days=5)).isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
                "reason": "Vacation",
            },
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        assert response.data["leave_request_id"] == leave_request_entity.leave_request_id
        assert response.message == "Đã tạo đơn xin nghỉ phép thành công"
    
    @pytest.mark.asyncio
    async def test_execute_missing_slots(self, mock_repository, mock_rbac):
        """Test create with missing required slots"""
        use_case = CreateLeaveRequestUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={"reason": "Vacation"},  # Missing start_date and end_date
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert - should ask for more info
        assert response.status == DomainResult.NEED_MORE_INFO
        assert "start_date" in response.missing_slots
        assert "end_date" in response.missing_slots
    
    @pytest.mark.asyncio
    async def test_execute_invalid_date_range(self, mock_repository, mock_rbac, employee_entity):
        """Test create with invalid date range (end before start)"""
        mock_repository.get_employee.return_value = employee_entity
        use_case = CreateLeaveRequestUseCase(mock_repository, mock_rbac)
        
        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=5)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "reason": "Vacation",
            },
            user_context={"user_id": "user-123"},
        )
        
        # Should raise InvalidInputError
        with pytest.raises(InvalidInputError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_past_date(self, mock_repository, mock_rbac, employee_entity):
        """Test create with past date"""
        mock_repository.get_employee.return_value = employee_entity
        use_case = CreateLeaveRequestUseCase(mock_repository, mock_rbac)
        
        start_date = date.today() - timedelta(days=5)
        end_date = date.today() - timedelta(days=2)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "reason": "Vacation",
            },
            user_context={"user_id": "user-123"},
        )
        
        # Should raise InvalidInputError
        with pytest.raises(InvalidInputError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_insufficient_balance(self, mock_repository, mock_rbac):
        """Test create with insufficient leave balance"""
        # Employee with only 1 day balance
        poor_employee = Employee(
            employee_id=str(uuid4()),
            user_id="user-123",
            name="John Doe",
            email="john@example.com",
            department="Engineering",
            leave_balance=1,
            role="employee"
        )
        mock_repository.get_employee.return_value = poor_employee
        use_case = CreateLeaveRequestUseCase(mock_repository, mock_rbac)
        
        start_date = date.today() + timedelta(days=5)
        end_date = date.today() + timedelta(days=10)  # 6 days requested
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "reason": "Vacation",
            },
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert - should return error
        assert response.status == DomainResult.ERROR
        assert "không đủ ngày phép" in response.message


class TestApproveLeaveUseCase:
    """Test ApproveLeaveUseCase"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_repository, mock_rbac, manager_entity, leave_request_entity):
        """Test successful approve leave"""
        mock_repository.get_employee.return_value = manager_entity
        mock_repository.get_leave_request.return_value = leave_request_entity
        
        approved_request = leave_request_entity
        approved_request.status = "approved"
        approved_request.approved_by = manager_entity.employee_id
        mock_repository.update_leave_request.return_value = approved_request
        
        use_case = ApproveLeaveUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="approve_leave",
            intent_type="OPERATION",
            slots={"leave_request_id": leave_request_entity.leave_request_id},
            user_context={"user_id": "manager-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        assert response.message == "Đã duyệt đơn xin nghỉ phép thành công"
    
    @pytest.mark.asyncio
    async def test_execute_missing_leave_request_id(self, mock_repository, mock_rbac):
        """Test approve with missing leave_request_id"""
        use_case = ApproveLeaveUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="approve_leave",
            intent_type="OPERATION",
            slots={},  # Missing leave_request_id
            user_context={"user_id": "manager-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert - should ask for more info
        assert response.status == DomainResult.NEED_MORE_INFO
        assert "leave_request_id" in response.missing_slots


class TestRejectLeaveUseCase:
    """Test RejectLeaveUseCase"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_repository, mock_rbac, manager_entity, leave_request_entity):
        """Test successful reject leave"""
        mock_repository.get_employee.return_value = manager_entity
        mock_repository.get_leave_request.return_value = leave_request_entity
        
        rejected_request = leave_request_entity
        rejected_request.status = "rejected"
        rejected_request.approved_by = manager_entity.employee_id
        mock_repository.update_leave_request.return_value = rejected_request
        
        use_case = RejectLeaveUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="reject_leave",
            intent_type="OPERATION",
            slots={
                "leave_request_id": leave_request_entity.leave_request_id,
                "rejection_reason": "Conflict with project deadline"
            },
            user_context={"user_id": "manager-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        assert response.message == "Đã từ chối đơn xin nghỉ phép"


class TestQueryLeaveRequestsUseCase:
    """Test QueryLeaveRequestsUseCase"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_repository, mock_rbac, employee_entity, leave_request_entity):
        """Test successful query leave requests"""
        mock_repository.get_employee.return_value = employee_entity
        mock_repository.get_leave_requests.return_value = [leave_request_entity]
        use_case = QueryLeaveRequestsUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_requests",
            intent_type="OPERATION",
            slots={},
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        assert len(response.data["leave_requests"]) == 1
        assert response.data["total_count"] == 1
        assert response.message == "Tìm thấy 1 đơn xin nghỉ phép"
    
    @pytest.mark.asyncio
    async def test_execute_with_status_filter(self, mock_repository, mock_rbac, employee_entity, leave_request_entity):
        """Test query with status filter"""
        mock_repository.get_employee.return_value = employee_entity
        mock_repository.get_leave_requests.return_value = [leave_request_entity]
        use_case = QueryLeaveRequestsUseCase(mock_repository, mock_rbac)
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_requests",
            intent_type="OPERATION",
            slots={"status": "pending"},
            user_context={"user_id": "user-123"},
        )
        
        # Execute
        response = await use_case.execute(request)
        
        # Assert
        assert response.status == DomainResult.SUCCESS
        # Verify that get_leave_requests was called with status filter
        mock_repository.get_leave_requests.assert_called_once()
        call_args = mock_repository.get_leave_requests.call_args
        assert call_args[1]["status"] == "pending"

