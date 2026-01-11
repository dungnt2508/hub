"""
Alembic Migration - Add DBA Alerts Table

Creates the dba_alerts table for storing database alerts.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_dba_alerts'
down_revision = '005_create_dba_connections'
branch_labels = None
depends_on = None

def upgrade():
    """Create dba_alerts table"""
    op.create_table(
        'dba_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('metric_value', sa.Float, nullable=True),
        sa.Column('threshold_value', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['connection_id'], ['dba_connections.id'], ),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_alerts_connection_status', 'dba_alerts',
                   ['connection_id', 'status'])
    op.create_index('idx_alerts_type', 'dba_alerts', ['alert_type'])
    op.create_index('idx_alerts_severity', 'dba_alerts', ['severity'])
    op.create_index('idx_alerts_created', 'dba_alerts', ['created_at'])


def downgrade():
    """Drop dba_alerts table"""
    op.drop_index('idx_alerts_created')
    op.drop_index('idx_alerts_severity')
    op.drop_index('idx_alerts_type')
    op.drop_index('idx_alerts_connection_status')
    op.drop_table('dba_alerts')
