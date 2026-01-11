"""
Alembic Migration - Add DBA Metrics History Table

This migration creates the dba_metrics_history table for storing
historical performance metrics used for trending and baseline comparison.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '007_add_dba_metrics_history'
down_revision = '006_add_dba_alerts'
branch_labels = None
depends_on = None

def upgrade():
    """Create dba_metrics_history table"""
    op.create_table(
        'dba_metrics_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('database_type', sa.String(50), nullable=True),
        sa.Column('query_hash', sa.String(64), nullable=True),
        sa.Column('wait_type', sa.String(100), nullable=True),
        sa.Column('mean_time_ms', sa.Float, nullable=True),
        sa.Column('max_time_ms', sa.Float, nullable=True),
        sa.Column('total_calls', sa.Integer, nullable=True),
        sa.Column('rows_examined', sa.Integer, nullable=True),
        sa.Column('rows_returned', sa.Integer, nullable=True),
        sa.Column('wait_count', sa.Integer, nullable=True),
        sa.Column('total_wait_ms', sa.Float, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('recorded_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['dba_connections.id'], ),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_metrics_connection_date', 'dba_metrics_history', 
                   ['connection_id', 'recorded_at'])
    op.create_index('idx_metrics_type', 'dba_metrics_history', ['metric_type'])
    op.create_index('idx_metrics_query_hash', 'dba_metrics_history', ['query_hash'])
    op.create_index('idx_metrics_wait_type', 'dba_metrics_history', ['wait_type'])


def downgrade():
    """Drop dba_metrics_history table"""
    op.drop_index('idx_metrics_wait_type')
    op.drop_index('idx_metrics_query_hash')
    op.drop_index('idx_metrics_type')
    op.drop_index('idx_metrics_connection_date')
    op.drop_table('dba_metrics_history')
