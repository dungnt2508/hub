"""
Integration tests for HR domain
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.domain.hr.entry_handler import HREntryHandler
from backend.domain.hr.entities import Employee, LeaveRequest
from backend.schemas import DomainRequest, DomainResult
from backend.shared.exceptions import AuthorizationError


@pytest.fixture
async def mock_repository():
    """Create mock HR repository"""
    repo = AsyncMock()
    
    # Setup default employee
    employee = Employee(
        employee_id=str(uuid4()),
        user_id="user-emp-001",
        name="John Employee",
        email="john@example.com",
        department="Engineering",
        leave_balance=20,
        role="employee"
    )
    
    # Setup manager employee
    manager = Employee(
        employee_id=str(uuid4()),
        user_id="user-mgr-001",
        name="Jane Manager",
        email="jane@example.com",
        department="Engineering",
        leave_balance=25,
        role="manager"
    )
    
    async def mock_get_employee(user_id):
        if user_id == "user-emp-001":
            return employee
        elif user_id == "user-mgr-001":
            return manager
        return None
    
    repo.get_employee = mock_get_employee
    repo.get_employee_by_employee_id = AsyncMock(return_value=employee)
    repo.create_leave_request = AsyncMock(return_value=LeaveRequest(
        leave_request_id=str(uuid4()),
        employee_id=employee.employee_id,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=7),
        reason="Vacation",
        status="pending"
    ))
    repo.get_leave_request = AsyncMock(return_value=LeaveRequest(
        leave_request_id=str(uuid4()),
        employee_id=employee.employee_id,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=7),
        reason="Vacation",
        status="pending"
    ))
    repo.get_leave_requests = AsyncMock(return_value=[])
    repo.update_leave_request = AsyncMock(return_value=LeaveRequest(
        leave_request_id=str(uuid4()),
        employee_id=employee.employee_id,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=7),
        reason="Vacation",
        status="approved"
    ))
    
    return repo


@pytest.fixture
async def hr_handler(mock_repository):
    """Create HR domain handler with mock repository"""
    return HREntryHandler(repository=mock_repository)


@pytest.fixture
def sample_user_context():
    """Create sample user context"""
    return {
        "user_id": "user-emp-001",
        "user_name": "John Employee",
        "department": "Engineering",
        "role": "employee",
    }


class TestHRDomain:
    """Test HR domain operations"""
    
    @pytest.mark.asyncio
    async def test_query_leave_balance(self, hr_handler, sample_user_context):
        """Test querying leave balance"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_balance",
            intent_type="OPERATION",
            slots={},
            user_context=sample_user_context,
        )
        
        response = await hr_handler.handle(request)
        
        assert response is not None
        assert response.status == DomainResult.SUCCESS
        assert response.data["leave_balance"] == 20
        assert response.data["employee_name"] == "John Employee"
    
    @pytest.mark.asyncio
    async def test_create_leave_request(self, hr_handler, sample_user_context):
        """Test creating leave request"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": (date.today() + timedelta(days=5)).isoformat(),
                "end_date": (date.today() + timedelta(days=10)).isoformat(),
                "reason": "Personal reasons",
            },
            user_context=sample_user_context,
        )
        
        response = await hr_handler.handle(request)
        
        assert response is not None
        assert response.status == DomainResult.SUCCESS
        assert "leave_request_id" in response.data
    
    @pytest.mark.asyncio
    async def test_approve_leave(self, hr_handler):
        """Test approving leave request"""
        manager_context = {
            "user_id": "user-mgr-001",
            "user_name": "Jane Manager",
            "role": "manager",
        }
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="approve_leave",
            intent_type="OPERATION",
            slots={
                "leave_request_id": str(uuid4()),
            },
            user_context=manager_context,
        )
        
        response = await hr_handler.handle(request)
        
        assert response is not None
        assert response.status == DomainResult.SUCCESS
    
    @pytest.mark.asyncio
    async def test_reject_leave(self, hr_handler):
        """Test rejecting leave request"""
        manager_context = {
            "user_id": "user-mgr-001",
            "user_name": "Jane Manager",
            "role": "manager",
        }
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="reject_leave",
            intent_type="OPERATION",
            slots={
                "leave_request_id": str(uuid4()),
                "rejection_reason": "Conflict with project deadline"
            },
            user_context=manager_context,
        )
        
        response = await hr_handler.handle(request)
        
        assert response is not None
        assert response.status == DomainResult.SUCCESS
    
    @pytest.mark.asyncio
    async def test_query_leave_requests(self, hr_handler, sample_user_context):
        """Test querying leave requests"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="query_leave_requests",
            intent_type="OPERATION",
            slots={},
            user_context=sample_user_context,
        )
        
        response = await hr_handler.handle(request)
        
        assert response is not None
        assert response.status == DomainResult.SUCCESS
        assert "leave_requests" in response.data
    
    @pytest.mark.asyncio
    async def test_invalid_intent(self, hr_handler, sample_user_context):
        """Test handling invalid intent"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="invalid_intent",
            intent_type="OPERATION",
            slots={},
            user_context=sample_user_context,
        )
        
        with pytest.raises(Exception):
            await hr_handler.handle(request)


class TestHRDomainRBAC:
    """Test HR domain RBAC"""
    
    @pytest.mark.asyncio
    async def test_employee_can_create_leave(self, hr_handler):
        """Test employee can create leave request"""
        employee_context = {
            "user_id": "user-emp-001",
            "role": "employee",
        }
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": (date.today() + timedelta(days=5)).isoformat(),
                "end_date": (date.today() + timedelta(days=10)).isoformat(),
                "reason": "Vacation",
            },
            user_context=employee_context,
        )
        
        response = await hr_handler.handle(request)
        assert response is not None
        assert response.status == DomainResult.SUCCESS
    
    @pytest.mark.asyncio
    async def test_manager_can_approve_leave(self, hr_handler):
        """Test manager can approve leave"""
        manager_context = {
            "user_id": "user-mgr-001",
            "role": "manager",
        }
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="approve_leave",
            intent_type="OPERATION",
            slots={
                "leave_request_id": str(uuid4()),
            },
            user_context=manager_context,
        )
        
        response = await hr_handler.handle(request)
        assert response is not None
        assert response.status == DomainResult.SUCCESS
    
    @pytest.mark.asyncio
    async def test_employee_cannot_approve_leave(self, hr_handler):
        """Test employee cannot approve leave"""
        employee_context = {
            "user_id": "user-emp-001",
            "role": "employee",
        }
        
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="approve_leave",
            intent_type="OPERATION",
            slots={
                "leave_request_id": str(uuid4()),
            },
            user_context=employee_context,
        )
        
        # Should raise permission error
        with pytest.raises(AuthorizationError):
            await hr_handler.handle(request)


class TestHRDomainValidation:
    """Test HR domain input validation"""
    
    @pytest.mark.asyncio
    async def test_create_leave_missing_dates(self, hr_handler, sample_user_context):
        """Test creating leave without dates"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "reason": "Vacation",
            },
            user_context=sample_user_context,
        )
        
        response = await hr_handler.handle(request)
        # Should validate and return error
        assert response.status == DomainResult.NEED_MORE_INFO
        assert "start_date" in response.missing_slots
        assert "end_date" in response.missing_slots
    
    @pytest.mark.asyncio
    async def test_create_leave_invalid_dates(self, hr_handler, sample_user_context):
        """Test creating leave with invalid dates"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": (date.today() + timedelta(days=10)).isoformat(),
                "end_date": (date.today() + timedelta(days=5)).isoformat(),  # End before start
                "reason": "Vacation",
            },
            user_context=sample_user_context,
        )
        
        # Should validate date range
        with pytest.raises(Exception):
            await hr_handler.handle(request)
    
    @pytest.mark.asyncio
    async def test_create_leave_past_date(self, hr_handler, sample_user_context):
        """Test creating leave for past date"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={
                "start_date": (date.today() - timedelta(days=5)).isoformat(),
                "end_date": (date.today() - timedelta(days=1)).isoformat(),
                "reason": "Vacation",
            },
            user_context=sample_user_context,
        )
        
        # Should validate not in past
        with pytest.raises(Exception):
            await hr_handler.handle(request)


class TestHRDomainErrorHandling:
    """Test HR domain error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_slots(self, hr_handler, sample_user_context):
        """Test handling empty slots"""
        request = DomainRequest(
            trace_id=str(uuid4()),
            domain="hr",
            intent="create_leave_request",
            intent_type="OPERATION",
            slots={},
            user_context=sample_user_context,
        )
        
        response = await hr_handler.handle(request)
        # Should return validation error
        assert response.status == DomainResult.NEED_MORE_INFO
    
    @pytest.mark.asyncio
    async def test_null_user_context(self):
        """Test handling null user context"""
        # Should raise ValueError during validation
        with pytest.raises(ValueError):
            request = DomainRequest(
                trace_id=str(uuid4()),
                domain="hr",
                intent="query_leave_balance",
                intent_type="OPERATION",
                slots={},
                user_context={},  # Missing user_id
            )

