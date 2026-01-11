"""Create dba_connections table

Revision ID: 005_create_dba_connections
Revises: 004_create_hr_tables
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_dba_connections'
down_revision = '004_create_hr_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dba_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('connection_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('db_type', sa.String(length=50), nullable=False),
        sa.Column('connection_string', sa.Text(), nullable=False),  # Encrypted
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id'),
        sa.UniqueConstraint('name', 'tenant_id', name='uq_dba_connections_name_tenant')
    )
    
    # Create indexes
    op.create_index('idx_dba_connections_db_type', 'dba_connections', ['db_type'])
    op.create_index('idx_dba_connections_tenant', 'dba_connections', ['tenant_id'])
    op.create_index('idx_dba_connections_status', 'dba_connections', ['status'])
    op.create_index('idx_dba_connections_environment', 'dba_connections', ['environment'])


def downgrade():
    op.drop_index('idx_dba_connections_environment', table_name='dba_connections')
    op.drop_index('idx_dba_connections_status', table_name='dba_connections')
    op.drop_index('idx_dba_connections_tenant', table_name='dba_connections')
    op.drop_index('idx_dba_connections_db_type', table_name='dba_connections')
    op.drop_table('dba_connections')
