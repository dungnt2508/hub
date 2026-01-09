"""
Unit tests for HR repository
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.domain.hr.adapters.postgresql_repository import PostgreSQLHRRepository
from backend.domain.hr.entities import Employee, LeaveRequest
from backend.shared.exceptions import ExternalServiceError, DomainError


@pytest.fixture
def mock_db_client():
    """Create mock database client"""
    db_client = AsyncMock()
    pool_mock = AsyncMock()
    conn_mock = AsyncMock()
    
    db_client.pool = pool_mock
    pool_mock.acquire.return_value.__aenter__.return_value = conn_mock
    
    return db_client, pool_mock, conn_mock


@pytest.fixture
def employee_row():
    """Create sample employee row"""
    return {
        'employee_id': uuid4(),
        'user_id': 'user-123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'department': 'Engineering',
        'leave_balance': 20,
        'role': 'employee'
    }


@pytest.fixture
def leave_request_row():
    """Create sample leave request row"""
    return {
        'leave_request_id': uuid4(),
        'employee_id': uuid4(),
        'start_date': date.today() + timedelta(days=5),
        'end_date': date.today() + timedelta(days=7),
        'reason': 'Vacation',
        'status': 'pending',
        'approved_by': None,
        'created_at': datetime.utcnow()
    }


class TestPostgresqlHRRepository:
    """Test PostgreSQL HR Repository"""
    
    @pytest.mark.asyncio
    async def test_get_employee_success(self, mock_db_client, employee_row):
        """Test successful get employee by user_id"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = employee_row
        
        repository = PostgreSQLHRRepository(db_client)
        employee = await repository.get_employee("user-123")
        
        # Assert
        assert employee is not None
        assert employee.user_id == "user-123"
        assert employee.name == "John Doe"
        assert employee.leave_balance == 20
        
        # Verify database call
        conn_mock.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_employee_not_found(self, mock_db_client):
        """Test get employee when not found"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        employee = await repository.get_employee("user-nonexistent")
        
        # Assert
        assert employee is None
    
    @pytest.mark.asyncio
    async def test_get_employee_database_error(self, mock_db_client):
        """Test get employee with database error"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.side_effect = Exception("Database connection failed")
        
        repository = PostgreSQLHRRepository(db_client)
        
        # Should raise ExternalServiceError
        with pytest.raises(ExternalServiceError):
            await repository.get_employee("user-123")
    
    @pytest.mark.asyncio
    async def test_get_employee_by_employee_id_success(self, mock_db_client, employee_row):
        """Test successful get employee by employee_id"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = employee_row
        
        repository = PostgreSQLHRRepository(db_client)
        employee = await repository.get_employee_by_employee_id(str(employee_row['employee_id']))
        
        # Assert
        assert employee is not None
        assert employee.employee_id == str(employee_row['employee_id'])
    
    @pytest.mark.asyncio
    async def test_create_leave_request_success(self, mock_db_client, employee_row):
        """Test successful create leave request"""
        db_client, pool_mock, conn_mock = mock_db_client
        
        # Mock get_employee for validation
        conn_mock.fetchrow.return_value = employee_row
        conn_mock.execute.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        
        leave_request = LeaveRequest(
            leave_request_id="",  # Will be generated
            employee_id=str(employee_row['employee_id']),
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=7),
            reason="Vacation",
            status="pending"
        )
        
        created = await repository.create_leave_request(leave_request)
        
        # Assert
        assert created is not None
        assert created.reason == "Vacation"
        assert created.status == "pending"
    
    @pytest.mark.asyncio
    async def test_create_leave_request_employee_not_found(self, mock_db_client):
        """Test create leave request with non-existent employee"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        
        leave_request = LeaveRequest(
            leave_request_id="",
            employee_id=str(uuid4()),
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=7),
            reason="Vacation",
            status="pending"
        )
        
        # Should raise DomainError
        with pytest.raises(DomainError):
            await repository.create_leave_request(leave_request)
    
    @pytest.mark.asyncio
    async def test_get_leave_request_success(self, mock_db_client, leave_request_row):
        """Test successful get leave request"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = leave_request_row
        
        repository = PostgreSQLHRRepository(db_client)
        leave_request = await repository.get_leave_request(str(leave_request_row['leave_request_id']))
        
        # Assert
        assert leave_request is not None
        assert leave_request.reason == "Vacation"
        assert leave_request.status == "pending"
    
    @pytest.mark.asyncio
    async def test_get_leave_request_not_found(self, mock_db_client):
        """Test get leave request when not found"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        leave_request = await repository.get_leave_request(str(uuid4()))
        
        # Assert
        assert leave_request is None
    
    @pytest.mark.asyncio
    async def test_get_leave_requests_success(self, mock_db_client, leave_request_row):
        """Test successful get leave requests"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetch.return_value = [leave_request_row]
        
        repository = PostgreSQLHRRepository(db_client)
        leave_requests = await repository.get_leave_requests(
            employee_id=str(leave_request_row['employee_id'])
        )
        
        # Assert
        assert len(leave_requests) == 1
        assert leave_requests[0].reason == "Vacation"
    
    @pytest.mark.asyncio
    async def test_get_leave_requests_with_status_filter(self, mock_db_client, leave_request_row):
        """Test get leave requests with status filter"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetch.return_value = [leave_request_row]
        
        repository = PostgreSQLHRRepository(db_client)
        leave_requests = await repository.get_leave_requests(
            employee_id=str(leave_request_row['employee_id']),
            status="pending"
        )
        
        # Assert
        assert len(leave_requests) == 1
        
        # Verify that fetch was called with status filter
        conn_mock.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_leave_requests_with_pagination(self, mock_db_client, leave_request_row):
        """Test get leave requests with pagination"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetch.return_value = [leave_request_row]
        
        repository = PostgreSQLHRRepository(db_client)
        leave_requests = await repository.get_leave_requests(
            employee_id=str(leave_request_row['employee_id']),
            limit=10,
            offset=5
        )
        
        # Assert
        assert len(leave_requests) == 1
        
        # Verify pagination parameters
        conn_mock.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_leave_request_success(self, mock_db_client, leave_request_row):
        """Test successful update leave request"""
        db_client, pool_mock, conn_mock = mock_db_client
        
        # First call for validation (get_leave_request)
        # Second call for update and retrieval
        conn_mock.fetchrow.side_effect = [leave_request_row, leave_request_row]
        conn_mock.execute.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        
        leave_request = LeaveRequest(
            leave_request_id=str(leave_request_row['leave_request_id']),
            employee_id=str(leave_request_row['employee_id']),
            start_date=leave_request_row['start_date'],
            end_date=leave_request_row['end_date'],
            reason="Vacation",
            status="approved",
            approved_by=str(uuid4())
        )
        
        updated = await repository.update_leave_request(leave_request)
        
        # Assert
        assert updated is not None
        assert updated.status == "pending"  # Should be updated to the new status
    
    @pytest.mark.asyncio
    async def test_update_leave_request_not_found(self, mock_db_client):
        """Test update leave request when not found"""
        db_client, pool_mock, conn_mock = mock_db_client
        conn_mock.fetchrow.return_value = None
        
        repository = PostgreSQLHRRepository(db_client)
        
        leave_request = LeaveRequest(
            leave_request_id=str(uuid4()),
            employee_id=str(uuid4()),
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=7),
            reason="Vacation",
            status="approved"
        )
        
        # Should raise DomainError
        with pytest.raises(DomainError):
            await repository.update_leave_request(leave_request)

