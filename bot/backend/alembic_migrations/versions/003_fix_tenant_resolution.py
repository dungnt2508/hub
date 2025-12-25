"""
Alembic migration: Fix tenant resolution - Add tenant_sites mapping table
Priority 1 Fix: Implement proper site_id → tenant_id mapping

Revision ID: 003_fix_tenant_resolution
Created: 2025-01-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '003_fix_tenant_resolution'
down_revision = '002_add_knowledge_sync_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add tenant_sites mapping table and fix tenant resolution"""
    
    # 1. Create tenant_sites mapping table
    # This table maps site_id (public identifier) to tenant_id (internal UUID)
    op.create_table(
        'tenant_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', sa.String(255), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        # Indexes
        sa.Index('idx_tenant_sites_site_id', 'site_id'),
        sa.Index('idx_tenant_sites_tenant_id', 'tenant_id'),
        sa.Index('idx_tenant_sites_active', 'is_active'),
    )
    
    print("✅ Created tenant_sites mapping table")
    
    # 2. Add site_id column to tenants table (for backward compatibility)
    # This allows direct lookup if needed, but tenant_sites is the primary mapping
    op.add_column('tenants', sa.Column('site_id', sa.String(255), nullable=True))
    op.create_index('idx_tenants_site_id', 'tenants', ['site_id'], unique=True, 
                    postgresql_where=sa.text('site_id IS NOT NULL'))
    
    print("✅ Added site_id column to tenants table")
    
    # 3. Add is_active column to tenants table (for soft delete)
    op.add_column('tenants', sa.Column('is_active', sa.Boolean(), default=True, nullable=False))
    op.create_index('idx_tenants_is_active', 'tenants', ['is_active'])
    
    print("✅ Added is_active column to tenants table")


def downgrade() -> None:
    """Rollback tenant resolution fixes"""
    
    op.drop_index('idx_tenants_is_active', table_name='tenants')
    op.drop_column('tenants', 'is_active')
    print("✅ Dropped is_active column from tenants table")
    
    op.drop_index('idx_tenants_site_id', table_name='tenants')
    op.drop_column('tenants', 'site_id')
    print("✅ Dropped site_id column from tenants table")
    
    op.drop_table('tenant_sites')
    print("✅ Dropped tenant_sites table")

