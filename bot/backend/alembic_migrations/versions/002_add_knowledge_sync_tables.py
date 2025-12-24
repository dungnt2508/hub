"""
Alembic migration: Add knowledge sync tables
Phase 2: Catalog Knowledge Integration - Track product sync status

Revision ID: 002_add_knowledge_sync_tables
Created: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '002_add_knowledge_sync_tables'
down_revision = '001_create_multitenant_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create knowledge sync tracking tables"""
    
    # 1. Create knowledge_sync_status table
    op.create_table(
        'knowledge_sync_status',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                 primary_key=True),
        sa.Column('last_sync_at', sa.DateTime()),
        sa.Column('product_count', sa.Integer(), default=0),
        sa.Column('sync_status', sa.String(50)),  # 'syncing', 'completed', 'failed'
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_knowledge_sync_status_tenant', 'tenant_id'),
        sa.Index('idx_knowledge_sync_status_sync_status', 'sync_status'),
    )
    
    print("✅ Created knowledge_sync_status table")
    
    # 2. Create knowledge_products table
    op.create_table(
        'knowledge_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),  # Reference to catalog product
        sa.Column('vector_id', sa.String(255)),  # Qdrant vector ID
        sa.Column('title', sa.String(500)),
        sa.Column('description', sa.Text()),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.func.now()),
        
        # Unique constraint per (tenant_id, product_id)
        sa.UniqueConstraint('tenant_id', 'product_id',
                           name='uq_knowledge_product_per_tenant'),
        
        sa.Index('idx_knowledge_products_tenant', 'tenant_id'),
        sa.Index('idx_knowledge_products_product_id', 'product_id'),
        sa.Index('idx_knowledge_products_tenant_product', 'tenant_id', 'product_id'),
    )
    
    print("✅ Created knowledge_products table")


def downgrade() -> None:
    """Rollback knowledge sync tables"""
    
    op.drop_table('knowledge_products')
    print("✅ Dropped knowledge_products table")
    
    op.drop_table('knowledge_sync_status')
    print("✅ Dropped knowledge_sync_status table")

