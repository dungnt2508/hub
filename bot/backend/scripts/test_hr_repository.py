"""
Test script for HR Repository
Run this to verify HRRepository works with real database
"""
import asyncio
import sys
import os

# Add project root to path (two levels up from scripts/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.database_client import database_client
from backend.domain.hr.adapters.postgresql_repository import PostgreSQLHRRepository
from backend.domain.hr.entities import LeaveRequest
from datetime import date, timedelta
from backend.shared.logger import logger


async def test_hr_repository():
    """Test HR Repository with real database"""
    
    print("=" * 60)
    print("Testing HR Repository")
    print("=" * 60)
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        await database_client.connect()
        print("✅ Database connected")
        
        # Initialize repository
        print("\n2. Initializing repository...")
        repository = PostgreSQLHRRepository()
        print("✅ Repository initialized")
        
        # Test 1: Get employee by user_id
        print("\n3. Testing get_employee()...")
        employee = await repository.get_employee("user-001")
        if employee:
            print(f"✅ Found employee: {employee.name} ({employee.email})")
            print(f"   - Department: {employee.department}")
            print(f"   - Leave Balance: {employee.leave_balance} days")
            print(f"   - Role: {employee.role}")
        else:
            print("❌ Employee not found (user-001)")
            print("   Make sure migration 004_create_hr_tables has been run")
            return
        
        # Test 2: Create leave request
        print("\n4. Testing create_leave_request()...")
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=2)
        
        leave_request = LeaveRequest(
            leave_request_id="",  # Will be generated
            employee_id=employee.employee_id,
            start_date=start_date,
            end_date=end_date,
            reason="Nghỉ phép cá nhân",
            status="pending"
        )
        
        created_request = await repository.create_leave_request(leave_request)
        print(f"✅ Created leave request: {created_request.leave_request_id}")
        print(f"   - Start: {created_request.start_date}")
        print(f"   - End: {created_request.end_date}")
        print(f"   - Status: {created_request.status}")
        
        # Test 3: Get leave request
        print("\n5. Testing get_leave_request()...")
        retrieved_request = await repository.get_leave_request(created_request.leave_request_id)
        if retrieved_request:
            print(f"✅ Retrieved leave request: {retrieved_request.leave_request_id}")
            print(f"   - Reason: {retrieved_request.reason}")
        else:
            print("❌ Failed to retrieve leave request")
        
        # Test 4: Update leave request
        print("\n6. Testing update_leave_request()...")
        retrieved_request.status = "approved"
        # Get manager to approve
        manager = await repository.get_employee("user-002")
        if manager:
            retrieved_request.approved_by = manager.employee_id
            updated_request = await repository.update_leave_request(retrieved_request)
            print(f"✅ Updated leave request: {updated_request.status}")
            print(f"   - Approved by: {manager.name}")
        else:
            print("⚠️  Manager not found, skipping approval test")
        
        # Test 5: Query leave balance (via use case)
        print("\n7. Testing QueryLeaveBalanceUseCase...")
        from backend.domain.hr.use_cases.query_leave_balance import QueryLeaveBalanceUseCase
        from backend.schemas import DomainRequest, DomainResult
        
        use_case = QueryLeaveBalanceUseCase(repository)
        domain_request = DomainRequest(
            trace_id="test-trace-001",
            intent="query_leave_balance",
            intent_type="OPERATION",
            domain="hr",
            user_context={"user_id": "user-001"},
            slots={}
        )
        
        response = await use_case.execute(domain_request)
        if response.status == DomainResult.SUCCESS:
            print(f"✅ Query leave balance successful")
            print(f"   - Message: {response.message}")
            print(f"   - Leave Balance: {response.data.get('leave_balance')} days")
        else:
            print(f"❌ Query leave balance failed: {response.status}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Disconnect
        await database_client.disconnect()
        print("\n✅ Database disconnected")


if __name__ == "__main__":
    asyncio.run(test_hr_repository())

