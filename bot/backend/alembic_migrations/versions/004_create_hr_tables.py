"""
Alembic migration: Create HR domain tables
Phase 1.1: HR Repository - Employees and Leave Requests

Revision ID: 004_create_hr_tables
Created: 2026-01-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '004_create_hr_tables'
down_revision = '003_create_admin_config_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create HR domain tables"""
    
    # 1. Create employees table
    op.create_table(
        'employees',
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('department', sa.String(255), nullable=False),
        sa.Column('leave_balance', sa.Integer(), nullable=False, default=12),
        sa.Column('role', sa.String(50)),  # 'employee', 'manager', 'admin'
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_employees_user_id', 'user_id'),
        sa.Index('idx_employees_email', 'email'),
        sa.Index('idx_employees_department', 'department'),
    )
    
    print("✅ Created employees table")
    
    # 2. Create leave_requests table
    op.create_table(
        'leave_requests',
        sa.Column('leave_request_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('employees.employee_id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),  # 'pending', 'approved', 'rejected'
        sa.Column('approved_by', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('employees.employee_id', ondelete='SET NULL')),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_leave_requests_employee', 'employee_id'),
        sa.Index('idx_leave_requests_status', 'status'),
        sa.Index('idx_leave_requests_dates', 'start_date', 'end_date'),
    )
    
    print("✅ Created leave_requests table")
    
    # 3. Insert sample employee data for testing
    # Note: This is for development/testing. In production, employees should be synced from HR system
    # Using explicit UUIDs for consistency
    op.execute("""
        INSERT INTO employees (employee_id, user_id, name, email, department, leave_balance, role, created_at, updated_at)
        VALUES 
            ('550e8400-e29b-41d4-a716-446655440001'::uuid, 'user-001', 'Nguyễn Văn A', 'nguyen.van.a@example.com', 'Engineering', 10, 'employee', NOW(), NOW()),
            ('550e8400-e29b-41d4-a716-446655440002'::uuid, 'user-002', 'Trần Thị B', 'tran.thi.b@example.com', 'Engineering', 8, 'manager', NOW(), NOW()),
            ('550e8400-e29b-41d4-a716-446655440003'::uuid, 'user-003', 'Lê Văn C', 'le.van.c@example.com', 'HR', 12, 'employee', NOW(), NOW())
        ON CONFLICT (user_id) DO NOTHING;
    """)
    
    print("✅ Inserted sample employee data")


def downgrade() -> None:
    """Rollback HR domain tables"""
    
    op.drop_table('leave_requests')
    print("✅ Dropped leave_requests table")
    
    op.drop_table('employees')
    print("✅ Dropped employees table")

