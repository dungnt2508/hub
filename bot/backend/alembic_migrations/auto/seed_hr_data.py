"""
Seed HR domain data for testing and development
"""
import asyncio
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.infrastructure.database_client import DatabaseClient
from backend.shared.logger import logger


async def seed_hr_data():
    """Seed HR domain data to database"""
    db_client = DatabaseClient()
    
    try:
        await db_client.connect()
        logger.info("Connected to database for seeding HR data")
        
        # Seed employees
        employees = [
            {
                "employee_id": uuid.uuid4(),
                "user_id": "user-emp-001",
                "name": "Nguyễn Văn A",
                "email": "nguyena@example.com",
                "department": "Kỹ thuật",
                "leave_balance": 20,
                "role": "employee"
            },
            {
                "employee_id": uuid.uuid4(),
                "user_id": "user-emp-002",
                "name": "Trần Thị B",
                "email": "tranb@example.com",
                "department": "Kỹ thuật",
                "leave_balance": 18,
                "role": "employee"
            },
            {
                "employee_id": uuid.uuid4(),
                "user_id": "user-mgr-001",
                "name": "Lê Văn Manager",
                "email": "lemanager@example.com",
                "department": "Kỹ thuật",
                "leave_balance": 25,
                "role": "manager"
            },
            {
                "employee_id": uuid.uuid4(),
                "user_id": "user-admin-001",
                "name": "Admin",
                "email": "admin@example.com",
                "department": "Quản trị",
                "leave_balance": 30,
                "role": "admin"
            },
        ]
        
        pool = db_client.pool
        async with pool.acquire() as conn:
            for emp in employees:
                try:
                    await conn.execute(
                        """
                        INSERT INTO employees 
                        (employee_id, user_id, name, email, department, leave_balance, role, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                        ON CONFLICT (user_id) DO UPDATE
                        SET 
                            name = EXCLUDED.name,
                            department = EXCLUDED.department,
                            leave_balance = EXCLUDED.leave_balance,
                            role = EXCLUDED.role,
                            updated_at = NOW()
                        """,
                        emp["employee_id"],
                        emp["user_id"],
                        emp["name"],
                        emp["email"],
                        emp["department"],
                        emp["leave_balance"],
                        emp["role"]
                    )
                    logger.info(f"Seeded employee: {emp['name']} ({emp['user_id']})")
                except Exception as e:
                    logger.warning(f"Failed to seed employee {emp['user_id']}: {e}")
        
        # Seed leave requests
        leave_requests = [
            {
                "leave_request_id": uuid.uuid4(),
                "employee_id": employees[0]["employee_id"],
                "start_date": date.today() + timedelta(days=5),
                "end_date": date.today() + timedelta(days=7),
                "reason": "Nghỉ phép hàng năm",
                "status": "pending",
                "approved_by": None
            },
            {
                "leave_request_id": uuid.uuid4(),
                "employee_id": employees[1]["employee_id"],
                "start_date": date.today() + timedelta(days=10),
                "end_date": date.today() + timedelta(days=12),
                "reason": "Đau ốm",
                "status": "pending",
                "approved_by": None
            },
            {
                "leave_request_id": uuid.uuid4(),
                "employee_id": employees[0]["employee_id"],
                "start_date": date.today() - timedelta(days=10),
                "end_date": date.today() - timedelta(days=8),
                "reason": "Nghỉ phép trước đó",
                "status": "approved",
                "approved_by": employees[2]["employee_id"]
            },
        ]
        
        async with pool.acquire() as conn:
            for lr in leave_requests:
                try:
                    await conn.execute(
                        """
                        INSERT INTO leave_requests 
                        (leave_request_id, employee_id, start_date, end_date, reason, status, approved_by, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                        ON CONFLICT (leave_request_id) DO UPDATE
                        SET 
                            status = EXCLUDED.status,
                            approved_by = EXCLUDED.approved_by,
                            updated_at = NOW()
                        """,
                        lr["leave_request_id"],
                        lr["employee_id"],
                        lr["start_date"],
                        lr["end_date"],
                        lr["reason"],
                        lr["status"],
                        lr["approved_by"]
                    )
                    logger.info(f"Seeded leave request: {lr['reason']} ({lr['status']})")
                except Exception as e:
                    logger.warning(f"Failed to seed leave request: {e}")
        
        logger.info("HR data seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to seed HR data: {e}", exc_info=True)
    finally:
        await db_client.disconnect()


async def main():
    """Main entry point"""
    print("🌱 Seeding HR domain data...")
    await seed_hr_data()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())

