"""
Alembic Migration - Create DBA Query Templates Table

This migration creates the dba_query_templates table for storing
SQL query templates used in DBA playbooks with versioning and audit trail.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '008_create_dba_query_templates'
down_revision = '007_add_dba_metrics_history'
branch_labels = None
depends_on = None


def upgrade():
    """Create dba_query_templates table"""
    op.create_table(
        'dba_query_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('playbook_name', sa.String(100), nullable=False),  # e.g., "QUERY_PERFORMANCE", "INDEX_HEALTH"
        sa.Column('db_type', sa.String(50), nullable=False),  # "sqlserver", "postgresql", "mysql"
        sa.Column('step_number', sa.Integer(), nullable=False),  # Step order in playbook
        sa.Column('purpose', sa.String(255), nullable=False),  # Description of what this query does
        sa.Column('query_text', sa.Text(), nullable=False),  # The SQL query
        sa.Column('read_only', sa.Boolean(), server_default='true', nullable=False),
        
        # Versioning
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('playbook_name', 'db_type', 'step_number', 'version',
                           name='uq_dba_query_templates_playbook_db_step_version'),
        sa.Index('idx_dba_query_templates_playbook_active', 'playbook_name', 'db_type', 'is_active'),
        sa.Index('idx_dba_query_templates_db_type', 'db_type', 'is_active'),
    )
    
    print("✅ Created dba_query_templates table")


def downgrade():
    """Drop dba_query_templates table"""
    op.drop_index('idx_dba_query_templates_db_type')
    op.drop_index('idx_dba_query_templates_playbook_active')
    op.drop_table('dba_query_templates')

