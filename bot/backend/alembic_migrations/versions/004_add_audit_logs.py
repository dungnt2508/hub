"""
Alembic migration: Add tenant audit logs table
Priority 2 Fix: Implement audit logging for tenant operations

Revision ID: 004_add_audit_logs
Created: 2025-12-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '004_add_audit_logs'
down_revision = '003_fix_tenant_resolution'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add tenant audit logs table for tracking all tenant operations"""
    
    # Create tenant_audit_logs table
    op.create_table(
        'tenant_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation', sa.String(100), nullable=False),  # 'create', 'update', 'delete', 'read', etc.
        sa.Column('resource_type', sa.String(50)),  # 'tenant', 'product', 'conversation', etc.
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),  # ID of the resource being operated on
        sa.Column('user_key', sa.String(255)),  # User who performed the operation
        sa.Column('channel', sa.String(50)),  # 'web', 'telegram', 'teams', 'api'
        sa.Column('ip_address', sa.String(45)),  # IPv4 or IPv6
        sa.Column('request_id', sa.String(255)),  # Correlation ID for tracing
        sa.Column('metadata', postgresql.JSONB),  # Additional context
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        
        # Indexes for common queries
        sa.Index('idx_audit_logs_tenant', 'tenant_id'),
        sa.Index('idx_audit_logs_tenant_created', 'tenant_id', 'created_at'),
        sa.Index('idx_audit_logs_operation', 'operation'),
        sa.Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        sa.Index('idx_audit_logs_created', 'created_at'),
    )
    
    print("✅ Created tenant_audit_logs table")


def downgrade() -> None:
    """Rollback audit logs table"""
    
    op.drop_table('tenant_audit_logs')
    print("✅ Dropped tenant_audit_logs table")

