"""
Alembic migration: Create admin config tables
Admin Dashboard - Runtime configuration system

Revision ID: 003_create_admin_config_tables
Created: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration meta
revision = '003_create_admin_config_tables'
down_revision = '002_add_knowledge_sync_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin config tables for runtime configuration"""
    
    # 1. Create admin_users table (RBAC)
    op.create_table(
        'admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),  # 'admin' | 'operator' | 'viewer'
        sa.Column('permissions', postgresql.JSONB, server_default='{}'),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('last_login_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_admin_users_email', 'email'),
        sa.Index('idx_admin_users_tenant_role', 'tenant_id', 'role', 'active'),
    )
    
    print("✅ Created admin_users table")
    
    # 2. Create routing_rules table
    op.create_table(
        'routing_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Matching criteria
        sa.Column('intent_pattern', postgresql.JSONB, nullable=False),
        
        # Routing decision
        sa.Column('target_domain', sa.String(100)),
        sa.Column('target_agent', sa.String(100)),
        sa.Column('target_workflow', postgresql.JSONB),
        
        # Priority & Fallback
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('fallback_chain', postgresql.JSONB),
        
        # Scope
        sa.Column('scope', sa.String(50), server_default='global'),
        sa.Column('scope_filter', postgresql.JSONB),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), server_default='1'),
        
        sa.Index('idx_routing_rules_tenant_enabled', 'tenant_id', 'enabled', 'priority'),
        sa.Index('idx_routing_rules_intent_pattern', 'intent_pattern', postgresql_using='gin'),
    )
    
    print("✅ Created routing_rules table")
    
    # 3. Create pattern_rules table
    op.create_table(
        'pattern_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Pattern config
        sa.Column('pattern_regex', sa.Text(), nullable=False),
        sa.Column('pattern_flags', sa.String(20), server_default='IGNORECASE'),
        
        # Routing decision
        sa.Column('target_domain', sa.String(100), nullable=False),
        sa.Column('target_intent', sa.String(100)),
        sa.Column('intent_type', sa.String(50)),
        sa.Column('slots_extraction', postgresql.JSONB),
        
        # Priority
        sa.Column('priority', sa.Integer(), server_default='0'),
        
        # Scope
        sa.Column('scope', sa.String(50), server_default='global'),
        sa.Column('scope_filter', postgresql.JSONB),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), server_default='1'),
        
        sa.Index('idx_pattern_rules_tenant_enabled', 'tenant_id', 'enabled', 'priority'),
    )
    
    print("✅ Created pattern_rules table")
    
    # 4. Create keyword_hints table
    op.create_table(
        'keyword_hints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Keyword config
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('keywords', postgresql.JSONB, nullable=False),
        
        # Scope
        sa.Column('scope', sa.String(50), server_default='global'),
        sa.Column('scope_filter', postgresql.JSONB),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('tenant_id', 'domain', 'rule_name',
                           name='uq_keyword_hints_tenant_domain_name'),
        sa.Index('idx_keyword_hints_tenant_enabled', 'tenant_id', 'enabled'),
        sa.Index('idx_keyword_hints_domain', 'domain'),
    )
    
    print("✅ Created keyword_hints table")
    
    # 5. Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('template_type', sa.String(50), nullable=False),  # 'system' | 'agent' | 'tool' | 'rag'
        sa.Column('domain', sa.String(100)),
        sa.Column('agent', sa.String(100)),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Template content
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('variables', postgresql.JSONB),
        
        # Versioning
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('tenant_id', 'template_name', 'version',
                           name='uq_prompt_templates_tenant_name_version'),
        sa.Index('idx_prompt_templates_tenant_active', 'tenant_id', 'template_type', 'is_active'),
        sa.Index('idx_prompt_templates_domain_agent', 'domain', 'agent', 'is_active'),
    )
    
    print("✅ Created prompt_templates table")
    
    # 6. Create tool_permissions table
    op.create_table(
        'tool_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Permission config
        sa.Column('allowed_contexts', postgresql.JSONB),
        sa.Column('rate_limit', sa.Integer()),
        sa.Column('required_params', postgresql.JSONB),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('tenant_id', 'agent_name', 'tool_name',
                           name='uq_tool_permissions_tenant_agent_tool'),
        sa.Index('idx_tool_permissions_tenant_agent', 'tenant_id', 'agent_name', 'enabled'),
    )
    
    print("✅ Created tool_permissions table")
    
    # 7. Create guardrails table
    op.create_table(
        'guardrails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),  # 'hard' | 'soft'
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        
        # Rule config
        sa.Column('trigger_condition', postgresql.JSONB, nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # 'block' | 'redirect' | 'flag' | 'require_confirmation'
        sa.Column('action_params', postgresql.JSONB),
        
        # Scope
        sa.Column('scope', sa.String(50), server_default='global'),
        sa.Column('scope_filter', postgresql.JSONB),
        
        # Priority
        sa.Column('priority', sa.Integer(), server_default='0'),
        
        # Metadata
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('tenant_id', 'rule_name',
                           name='uq_guardrails_tenant_name'),
        sa.Index('idx_guardrails_tenant_enabled', 'tenant_id', 'enabled', 'priority'),
        sa.Index('idx_guardrails_type', 'rule_type', 'enabled'),
    )
    
    print("✅ Created guardrails table")
    
    # 8. Create config_audit_logs table
    op.create_table(
        'config_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        
        # What changed
        sa.Column('config_type', sa.String(50), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_name', sa.String(255)),
        
        # Who changed
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_by_email', sa.String(255)),
        
        # Change details
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('old_value', postgresql.JSONB),
        sa.Column('new_value', postgresql.JSONB),
        sa.Column('diff', postgresql.JSONB),
        
        # When
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now()),
        
        # Why
        sa.Column('reason', sa.Text()),
        
        sa.Index('idx_config_audit_logs_tenant', 'tenant_id', 'changed_at'),
        sa.Index('idx_config_audit_logs_config', 'config_type', 'config_id', 'changed_at'),
        sa.Index('idx_config_audit_logs_user', 'changed_by', 'changed_at'),
    )
    
    print("✅ Created config_audit_logs table")


def downgrade() -> None:
    """Rollback admin config tables"""
    
    op.drop_table('config_audit_logs')
    print("✅ Dropped config_audit_logs table")
    
    op.drop_table('guardrails')
    print("✅ Dropped guardrails table")
    
    op.drop_table('tool_permissions')
    print("✅ Dropped tool_permissions table")
    
    op.drop_table('prompt_templates')
    print("✅ Dropped prompt_templates table")
    
    op.drop_table('keyword_hints')
    print("✅ Dropped keyword_hints table")
    
    op.drop_table('pattern_rules')
    print("✅ Dropped pattern_rules table")
    
    op.drop_table('routing_rules')
    print("✅ Dropped routing_rules table")
    
    op.drop_table('admin_users')
    print("✅ Dropped admin_users table")

