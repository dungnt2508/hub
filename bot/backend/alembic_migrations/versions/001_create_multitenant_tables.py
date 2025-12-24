"""
Alembic migration: Create multi-tenant bot service tables
Phase 1: Foundation - Database schema for tenants, user_keys, conversations

Revision ID: 001_create_multitenant_tables
Created: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '001_create_multitenant_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create multi-tenant bot service tables"""
    
    # 1. Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False, unique=True),
        sa.Column('webhook_secret', sa.String(255)),
        
        # Plan & rate limits
        sa.Column('plan', sa.String(50), nullable=False, default='basic'),
        sa.Column('rate_limit_per_hour', sa.Integer(), default=1000),
        sa.Column('rate_limit_per_day', sa.Integer(), default=10000),
        
        # Web Embed Configuration
        sa.Column('web_embed_enabled', sa.Boolean(), default=True),
        sa.Column('web_embed_origins', postgresql.ARRAY(sa.String())),
        sa.Column('web_embed_jwt_secret', sa.String(255), nullable=False),
        sa.Column('web_embed_token_expiry_seconds', sa.Integer(), default=300),
        
        # Telegram Configuration
        sa.Column('telegram_enabled', sa.Boolean(), default=False),
        sa.Column('telegram_bot_token', sa.String(255)),
        
        # Teams Configuration
        sa.Column('teams_enabled', sa.Boolean(), default=False),
        sa.Column('teams_app_id', sa.String(255)),
        sa.Column('teams_app_password', sa.String(255)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_tenants_api_key', 'api_key'),
    )
    
    print("✅ Created tenants table")
    
    # 2. Create user_keys table
    op.create_table(
        'user_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),  # 'web', 'telegram', 'teams'
        sa.Column('user_key', sa.String(255), nullable=False),
        
        # Progressive identity (optional)
        sa.Column('user_id', sa.String(255)),
        sa.Column('user_email', sa.String(255)),
        sa.Column('user_display_name', sa.String(255)),
        
        # Timestamps
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now()),
        
        # Unique constraint per (tenant, channel, user_key)
        sa.UniqueConstraint('tenant_id', 'channel', 'user_key', 
                           name='uq_user_key_per_tenant_channel'),
        
        sa.Index('idx_user_keys_tenant', 'tenant_id'),
        sa.Index('idx_user_keys_tenant_channel', 'tenant_id', 'channel'),
    )
    
    print("✅ Created user_keys table")
    
    # 3. Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('user_key', sa.String(255), nullable=False),
        
        # State
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('last_message_at', sa.DateTime()),
        sa.Column('context_data', postgresql.JSON()),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        # Unique per (tenant, channel, user_key)
        sa.UniqueConstraint('tenant_id', 'channel', 'user_key',
                           name='uq_conversation_per_tenant_channel_user'),
        
        sa.Index('idx_conversations_tenant', 'tenant_id'),
        sa.Index('idx_conversations_tenant_channel_user', 'tenant_id', 'channel', 'user_key'),
    )
    
    print("✅ Created conversations table")
    
    # 4. Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),  # 'user', 'assistant'
        sa.Column('content', sa.Text(), nullable=False),
        
        # NLP metadata
        sa.Column('intent', sa.String(255)),
        sa.Column('confidence', sa.Float()),
        sa.Column('metadata', postgresql.JSON()),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_conversation_messages_conversation', 'conversation_id'),
        sa.Index('idx_conversation_messages_created', 'created_at'),
    )
    
    print("✅ Created conversation_messages table")
    
    # 5. Create tenant_api_keys table for service-to-service auth
    op.create_table(
        'tenant_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255)),
        sa.Column('last_used_at', sa.DateTime()),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime()),
        
        sa.Index('idx_tenant_api_keys_tenant', 'tenant_id'),
        sa.Index('idx_tenant_api_keys_key', 'key'),
    )
    
    print("✅ Created tenant_api_keys table")


def downgrade() -> None:
    """Rollback multi-tenant bot service tables"""
    
    op.drop_table('tenant_api_keys')
    print("✅ Dropped tenant_api_keys table")
    
    op.drop_table('conversation_messages')
    print("✅ Dropped conversation_messages table")
    
    op.drop_table('conversations')
    print("✅ Dropped conversations table")
    
    op.drop_table('user_keys')
    print("✅ Dropped user_keys table")
    
    op.drop_table('tenants')
    print("✅ Dropped tenants table")

