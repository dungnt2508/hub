"""
PostgreSQL HR Repository Implementation
"""
import uuid
from typing import Optional, List
from datetime import date, datetime

from ....infrastructure.database_client import database_client
from ....shared.logger import logger
from ....shared.exceptions import ExternalServiceError, DomainError
from ..entities import Employee, LeaveRequest
from ..ports.repository import IHRRepository


class PostgreSQLHRRepository(IHRRepository):
    """
    PostgreSQL implementation of HR Repository.
    
    Uses asyncpg connection pool from DatabaseClient.
    """
    
    def __init__(self, db_client=None):
        """
        Initialize repository.
        
        Args:
            db_client: Database client (defaults to global database_client)
        """
        self.db = db_client or database_client
    
    async def get_employee(self, user_id: str) -> Optional[Employee]:
        """
        Get employee by user ID.
        
        Args:
            user_id: User ID (from JWT/auth context)
            
        Returns:
            Employee entity or None if not found
            
        Raises:
            ExternalServiceError: If database query fails
        """
        try:
            pool = self.db.pool
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        employee_id,
                        user_id,
                        name,
                        email,
                        department,
                        leave_balance,
                        role
                    FROM employees
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                if not row:
                    logger.info(f"Employee not found for user_id: {user_id}")
                    return None
                
                return Employee(
                    employee_id=str(row['employee_id']),
                    user_id=row['user_id'],
                    name=row['name'],
                    email=row['email'],
                    department=row['department'],
                    leave_balance=row['leave_balance'],
                    role=row['role']
                )
                
        except Exception as e:
            logger.error(
                f"Failed to get employee: {e}",
                extra={"user_id": user_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Database query failed: {e}") from e
    
    async def create_leave_request(self, leave_request: LeaveRequest) -> LeaveRequest:
        """
        Create leave request.
        
        Args:
            leave_request: Leave request entity
            
        Returns:
            Created leave request with generated ID and timestamps
            
        Raises:
            ExternalServiceError: If database insert fails
            DomainError: If validation fails (e.g., employee not found)
        """
        try:
            # Validate employee exists
            employee = await self.get_employee_by_employee_id(leave_request.employee_id)
            if not employee:
                raise DomainError(f"Employee not found: {leave_request.employee_id}")
            
            # Generate UUID if not provided
            if not leave_request.leave_request_id:
                leave_request_id = str(uuid.uuid4())
            else:
                leave_request_id = leave_request.leave_request_id
            
            pool = self.db.pool
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO leave_requests (
                        leave_request_id,
                        employee_id,
                        start_date,
                        end_date,
                        reason,
                        status,
                        approved_by,
                        created_at,
                        updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                    """,
                    uuid.UUID(leave_request_id),
                    uuid.UUID(leave_request.employee_id),
                    leave_request.start_date,
                    leave_request.end_date,
                    leave_request.reason,
                    leave_request.status,
                    uuid.UUID(leave_request.approved_by) if leave_request.approved_by else None
                )
                
                logger.info(
                    f"Created leave request: {leave_request_id}",
                    extra={
                        "leave_request_id": leave_request_id,
                        "employee_id": leave_request.employee_id
                    }
                )
                
                # Return created leave request with ID
                return LeaveRequest(
                    leave_request_id=leave_request_id,
                    employee_id=leave_request.employee_id,
                    start_date=leave_request.start_date,
                    end_date=leave_request.end_date,
                    reason=leave_request.reason,
                    status=leave_request.status,
                    approved_by=leave_request.approved_by,
                    created_at=datetime.utcnow().isoformat()
                )
                
        except DomainError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create leave request: {e}",
                extra={"employee_id": leave_request.employee_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Database insert failed: {e}") from e
    
    async def get_leave_request(self, leave_request_id: str) -> Optional[LeaveRequest]:
        """
        Get leave request by ID.
        
        Args:
            leave_request_id: Leave request UUID
            
        Returns:
            Leave request entity or None if not found
            
        Raises:
            ExternalServiceError: If database query fails
        """
        try:
            pool = self.db.pool
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        leave_request_id,
                        employee_id,
                        start_date,
                        end_date,
                        reason,
                        status,
                        approved_by,
                        created_at
                    FROM leave_requests
                    WHERE leave_request_id = $1
                    """,
                    uuid.UUID(leave_request_id)
                )
                
                if not row:
                    logger.info(f"Leave request not found: {leave_request_id}")
                    return None
                
                return LeaveRequest(
                    leave_request_id=str(row['leave_request_id']),
                    employee_id=str(row['employee_id']),
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    reason=row['reason'],
                    status=row['status'],
                    approved_by=str(row['approved_by']) if row['approved_by'] else None,
                    created_at=row['created_at'].isoformat() if row['created_at'] else None
                )
                
        except Exception as e:
            logger.error(
                f"Failed to get leave request: {e}",
                extra={"leave_request_id": leave_request_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Database query failed: {e}") from e
    
    async def update_leave_request(self, leave_request: LeaveRequest) -> LeaveRequest:
        """
        Update leave request.
        
        Args:
            leave_request: Leave request entity with updated fields
            
        Returns:
            Updated leave request
            
        Raises:
            ExternalServiceError: If database update fails
            DomainError: If leave request not found
        """
        try:
            # Check if exists
            existing = await self.get_leave_request(leave_request.leave_request_id)
            if not existing:
                raise DomainError(f"Leave request not found: {leave_request.leave_request_id}")
            
            pool = self.db.pool
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE leave_requests
                    SET 
                        start_date = $1,
                        end_date = $2,
                        reason = $3,
                        status = $4,
                        approved_by = $5,
                        updated_at = NOW()
                    WHERE leave_request_id = $6
                    """,
                    leave_request.start_date,
                    leave_request.end_date,
                    leave_request.reason,
                    leave_request.status,
                    uuid.UUID(leave_request.approved_by) if leave_request.approved_by else None,
                    uuid.UUID(leave_request.leave_request_id)
                )
                
                logger.info(
                    f"Updated leave request: {leave_request.leave_request_id}",
                    extra={
                        "leave_request_id": leave_request.leave_request_id,
                        "status": leave_request.status
                    }
                )
                
                # Return updated leave request
                updated = await self.get_leave_request(leave_request.leave_request_id)
                return updated
                
        except DomainError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update leave request: {e}",
                extra={"leave_request_id": leave_request.leave_request_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Database update failed: {e}") from e
    
    async def get_leave_requests(
        self, 
        employee_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Get leave requests for an employee.
        
        Args:
            employee_id: Employee UUID
            status: Optional filter by status (pending, approved, rejected)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of leave request entities
            
        Raises:
            ExternalServiceError: If database query fails
        """
        try:
            pool = self.db.pool
            async with pool.acquire() as conn:
                if status:
                    rows = await conn.fetch(
                        """
                        SELECT 
                            leave_request_id,
                            employee_id,
                            start_date,
                            end_date,
                            reason,
                            status,
                            approved_by,
                            created_at
                        FROM leave_requests
                        WHERE employee_id = $1 AND status = $2
                        ORDER BY created_at DESC
                        LIMIT $3 OFFSET $4
                        """,
                        uuid.UUID(employee_id),
                        status,
                        limit,
                        offset
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT 
                            leave_request_id,
                            employee_id,
                            start_date,
                            end_date,
                            reason,
                            status,
                            approved_by,
                            created_at
                        FROM leave_requests
                        WHERE employee_id = $1
                        ORDER BY created_at DESC
                        LIMIT $2 OFFSET $3
                        """,
                        uuid.UUID(employee_id),
                        limit,
                        offset
                    )
                
                return [
                    LeaveRequest(
                        leave_request_id=str(row['leave_request_id']),
                        employee_id=str(row['employee_id']),
                        start_date=row['start_date'],
                        end_date=row['end_date'],
                        reason=row['reason'],
                        status=row['status'],
                        approved_by=str(row['approved_by']) if row['approved_by'] else None,
                        created_at=row['created_at'].isoformat() if row['created_at'] else None
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(
                f"Failed to get leave requests: {e}",
                extra={"employee_id": employee_id, "status": status},
                exc_info=True
            )
            raise ExternalServiceError(f"Database query failed: {e}") from e
    
    # Helper method for internal use
    async def get_employee_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """
        Get employee by employee_id (UUID).
        
        Args:
            employee_id: Employee UUID
            
        Returns:
            Employee entity or None if not found
        """
        try:
            pool = self.db.pool
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        employee_id,
                        user_id,
                        name,
                        email,
                        department,
                        leave_balance,
                        role
                    FROM employees
                    WHERE employee_id = $1
                    """,
                    uuid.UUID(employee_id)
                )
                
                if not row:
                    return None
                
                return Employee(
                    employee_id=str(row['employee_id']),
                    user_id=row['user_id'],
                    name=row['name'],
                    email=row['email'],
                    department=row['department'],
                    leave_balance=row['leave_balance'],
                    role=row['role']
                )
                
        except Exception as e:
            logger.error(
                f"Failed to get employee by employee_id: {e}",
                extra={"employee_id": employee_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Database query failed: {e}") from e

