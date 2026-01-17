"""Initial schema for bot_v2

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # I. Core platform (bắt buộc)
    
    # 1. tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),  # active, suspended, etc.
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('settings_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenants_status', 'tenants', ['status'])
    
    # 2. tenant_secrets
    op.create_table(
        'tenant_secrets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # api_key, telegram, web_embed, teams
        sa.Column('secret_encrypted', sa.Text(), nullable=False),
        sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenant_secrets_tenant_id', 'tenant_secrets', ['tenant_id'])
    op.create_index('ix_tenant_secrets_type', 'tenant_secrets', ['type'])
    
    # 3. channels
    op.create_table(
        'channels',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # telegram, web, teams
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_channels_tenant_id', 'channels', ['tenant_id'])
    op.create_index('ix_channels_type', 'channels', ['type'])
    
    # II. Catalog / knowledge (read-only runtime)
    
    # 1. products
    op.create_table(
        'products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('sku', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),  # active, archived, etc.
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'sku', name='uq_products_tenant_sku'),
        sa.UniqueConstraint('tenant_id', 'slug', name='uq_products_tenant_slug')
    )
    op.create_index('ix_products_tenant_id', 'products', ['tenant_id'])
    op.create_index('ix_products_sku', 'products', ['sku'])
    op.create_index('ix_products_slug', 'products', ['slug'])
    op.create_index('ix_products_status', 'products', ['status'])
    
    # 2. product_attributes
    op.create_table(
        'product_attributes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('attributes_key', sa.String(length=255), nullable=False),
        sa.Column('attributes_value', sa.Text(), nullable=False),
        sa.Column('attributes_value_type', sa.String(length=50), nullable=False),  # string, number, boolean, json
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_attributes_tenant_id', 'product_attributes', ['tenant_id'])
    op.create_index('ix_product_attributes_product_id', 'product_attributes', ['product_id'])
    op.create_index('ix_product_attributes_key', 'product_attributes', ['attributes_key'])
    
    # 3. use_cases
    op.create_table(
        'use_cases',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # allowed, disallowed
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_use_cases_tenant_id', 'use_cases', ['tenant_id'])
    op.create_index('ix_use_cases_product_id', 'use_cases', ['product_id'])
    op.create_index('ix_use_cases_type', 'use_cases', ['type'])
    
    # 4. faqs
    op.create_table(
        'faqs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),  # global, product
        sa.Column('product_id', sa.UUID(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_faqs_tenant_id', 'faqs', ['tenant_id'])
    op.create_index('ix_faqs_scope', 'faqs', ['scope'])
    op.create_index('ix_faqs_product_id', 'faqs', ['product_id'])
    
    # 5. comparisons
    op.create_table(
        'comparisons',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('product_a', sa.UUID(), nullable=False),
        sa.Column('product_b', sa.UUID(), nullable=False),
        sa.Column('allowed_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # array of attribute keys
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_a'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_b'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'product_a', 'product_b', name='uq_comparisons_tenant_products')
    )
    op.create_index('ix_comparisons_tenant_id', 'comparisons', ['tenant_id'])
    op.create_index('ix_comparisons_product_a', 'comparisons', ['product_a'])
    op.create_index('ix_comparisons_product_b', 'comparisons', ['product_b'])
    
    # 6. guardrails
    op.create_table(
        'guardrails',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('forbidden_topics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # array of forbidden topics
        sa.Column('disclaimers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # array of disclaimers
        sa.Column('fallback_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', name='uq_guardrails_tenant')
    )
    op.create_index('ix_guardrails_tenant_id', 'guardrails', ['tenant_id'])
    
    # III. Flow & logic support
    
    # 1. intents
    op.create_table(
        'intents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),  # ask_price, compare, suitability
        sa.Column('domain', sa.String(length=100), nullable=False),  # product, policy, sales
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_intents_tenant_name')
    )
    op.create_index('ix_intents_tenant_id', 'intents', ['tenant_id'])
    op.create_index('ix_intents_name', 'intents', ['name'])
    op.create_index('ix_intents_domain', 'intents', ['domain'])
    op.create_index('ix_intents_priority', 'intents', ['priority'])
    
    # 2. intent_patterns
    op.create_table(
        'intent_patterns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('intent_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # keyword, regex, phrase
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intent_patterns_intent_id', 'intent_patterns', ['intent_id'])
    op.create_index('ix_intent_patterns_type', 'intent_patterns', ['type'])
    
    # 3. intent_hints
    op.create_table(
        'intent_hints',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('intent_id', sa.UUID(), nullable=False),
        sa.Column('hint_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intent_hints_intent_id', 'intent_hints', ['intent_id'])
    
    # 4. intent_actions
    op.create_table(
        'intent_actions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('intent_id', sa.UUID(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),  # query_db, handoff, refuse, rag
        sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intent_actions_intent_id', 'intent_actions', ['intent_id'])
    op.create_index('ix_intent_actions_action_type', 'intent_actions', ['action_type'])
    op.create_index('ix_intent_actions_priority', 'intent_actions', ['priority'])
    
    # IV. Migration & versioning (admin only)
    
    # 1. migration_jobs
    op.create_table(
        'migration_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),  # excel, cms, crawl, ai
        sa.Column('status', sa.String(length=50), nullable=False),  # pending, processing, completed, failed
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_migration_jobs_tenant_id', 'migration_jobs', ['tenant_id'])
    op.create_index('ix_migration_jobs_status', 'migration_jobs', ['status'])
    
    # 2. migration_versions
    op.create_table(
        'migration_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'version', name='uq_migration_versions_tenant_version')
    )
    op.create_index('ix_migration_versions_tenant_id', 'migration_versions', ['tenant_id'])
    op.create_index('ix_migration_versions_version', 'migration_versions', ['version'])
    
    # V. Observability (bắt buộc nếu vận hành)
    
    # 1. conversation_logs
    op.create_table(
        'conversation_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('channel_id', sa.UUID(), nullable=True),
        sa.Column('intent', sa.String(length=255), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_logs_tenant_id', 'conversation_logs', ['tenant_id'])
    op.create_index('ix_conversation_logs_channel_id', 'conversation_logs', ['channel_id'])
    op.create_index('ix_conversation_logs_intent', 'conversation_logs', ['intent'])
    op.create_index('ix_conversation_logs_created_at', 'conversation_logs', ['created_at'])
    
    # 2. failed_queries
    op.create_table(
        'failed_queries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_failed_queries_tenant_id', 'failed_queries', ['tenant_id'])
    op.create_index('ix_failed_queries_created_at', 'failed_queries', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('failed_queries')
    op.drop_table('conversation_logs')
    op.drop_table('migration_versions')
    op.drop_table('migration_jobs')
    op.drop_table('intent_actions')
    op.drop_table('intent_hints')
    op.drop_table('intent_patterns')
    op.drop_table('intents')
    op.drop_table('guardrails')
    op.drop_table('comparisons')
    op.drop_table('faqs')
    op.drop_table('use_cases')
    op.drop_table('product_attributes')
    op.drop_table('products')
    op.drop_table('channels')
    op.drop_table('tenant_secrets')
    op.drop_table('tenants')
