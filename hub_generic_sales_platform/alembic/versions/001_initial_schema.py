"""Initial schema with Refactored Ontology Architecture

Revision ID: 001
Revises: 
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Nhóm 1: TENANT / ACCESS
    op.create_table(
        'tenant',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('plan', sa.String(), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenant_id', 'tenant', ['id'])
    
    op.create_table(
        'user_account',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='viewer'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_account_tenant_id', 'user_account', ['tenant_id'])
    op.create_index('ix_user_account_id', 'user_account', ['id'])

    # Nhóm 2: ONTOLOGY LAYER (GLOBAL)
    op.create_table(
        'knowledge_domain',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('domain_type', sa.String(), nullable=False, server_default='offering'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('flow_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_knowledge_domain_code')
    )
    op.create_index('ix_knowledge_domain_id', 'knowledge_domain', ['id'])

    op.create_table(
        'domain_attribute_definition',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value_type', sa.String(), nullable=False, server_default='text'),
        sa.Column('semantic_type', sa.String(), nullable=True, server_default='categorical'),
        sa.Column('value_constraint', sa.JSON(), nullable=True),
        sa.Column('scope', sa.String(), nullable=False, server_default='offering'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain_id', 'key', name='uq_domain_attr_key')
    )

    # Nhóm 3: CONFIGURATION LAYER (TENANT)
    op.create_table(
        'tenant_attribute_config',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('attribute_def_id', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('is_display', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_searchable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ui_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attribute_def_id'], ['domain_attribute_definition.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'attribute_def_id', name='uq_tenant_attr_config')
    )

    # Nhóm 4: BOT IDENTITY
    op.create_table(
        'system_capability',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('domain_id', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    op.create_table(
        'bot',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('domain_id', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_bot_tenant_code')
    )

    op.create_table(
        'bot_version',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('flow_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bot_id', 'version', name='uq_bot_version')
    )

    # Nhóm 5: ENTITY LAYER (TENANT DATA)
    op.create_table(
        'tenant_offering',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False, server_default='physical'),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('identity_key', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ext_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_offering_code')
    )
    op.create_index('idx_offering_tenant_type', 'tenant_offering', ['tenant_id', 'type'])

    op.create_table(
        'tenant_offering_version',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('offering_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['offering_id'], ['tenant_offering.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('offering_id', 'version', name='uq_tenant_offering_version')
    )

    op.create_table(
        'tenant_offering_attribute_value',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('offering_version_id', sa.String(), nullable=False),
        sa.Column('attribute_def_id', sa.String(), nullable=False),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('value_number', sa.Numeric(), nullable=True),
        sa.Column('value_bool', sa.Boolean(), nullable=True),
        sa.Column('value_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attribute_def_id'], ['domain_attribute_definition.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['offering_version_id'], ['tenant_offering_version.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('offering_version_id', 'attribute_def_id', name='uq_offering_version_attr_val'),
        sa.CheckConstraint(
            """
            (CASE WHEN value_text IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN value_number IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN value_bool IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN value_json IS NOT NULL THEN 1 ELSE 0 END) = 1
            """,
            name='ck_tenant_offering_attr_val_single_value'
        )
    )
    
    # Domain boundary enforcement via trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION check_domain_boundary_attr_val()
        RETURNS TRIGGER AS $$
        DECLARE
            attr_domain_id VARCHAR;
            offering_domain_id VARCHAR;
        BEGIN
            SELECT domain_id INTO attr_domain_id
            FROM domain_attribute_definition
            WHERE id = NEW.attribute_def_id;
            
            SELECT toff.domain_id INTO offering_domain_id
            FROM tenant_offering_version tov
            JOIN tenant_offering toff ON toff.id = tov.offering_id
            WHERE tov.id = NEW.offering_version_id;
            
            IF attr_domain_id IS NULL OR offering_domain_id IS NULL THEN
                RAISE EXCEPTION 'Cannot determine domain for attribute or offering';
            END IF;
            
            IF attr_domain_id != offering_domain_id THEN
                RAISE EXCEPTION 'Domain boundary violation: attribute domain (%) does not match offering domain (%)',
                    attr_domain_id, offering_domain_id;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_check_domain_boundary_attr_val
        BEFORE INSERT OR UPDATE ON tenant_offering_attribute_value
        FOR EACH ROW
        EXECUTE FUNCTION check_domain_boundary_attr_val();
    """)

    # --- Rest of the tables (Variant, Price, Inventory, FAQ, etc.) ---
    op.create_table(
        'tenant_offering_variant',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('offering_id', sa.String(), nullable=False),
        sa.Column('sku', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['offering_id'], ['tenant_offering.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'sku', name='uq_offering_variant_tenant_sku')
    )

    op.create_table(
        'tenant_sales_channel',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_sales_channel_code')
    )

    op.create_table(
        'tenant_price_list',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('channel_id', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('valid_to IS NULL OR valid_from < valid_to', name='check_price_list_time'),
        sa.ForeignKeyConstraint(['channel_id'], ['tenant_sales_channel.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_price_list_code')
    )


    op.create_table(
        'tenant_inventory_location',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False, server_default='warehouse'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tenant_inv_location_code')
    )


    # Runtime State tables
    op.create_table(
        'runtime_session',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=False),
        sa.Column('bot_version_id', sa.String(), nullable=False),
        sa.Column('channel_code', sa.String(), nullable=False),
        sa.Column('lifecycle_state', sa.String(), nullable=False, server_default='idle'),
        sa.Column('flow_context', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ext_metadata', sa.JSON(), nullable=True),
        sa.Column('state_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bot_version_id'], ['bot_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


    op.create_table(
        'tenant_variant_price',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('price_list_id', sa.String(), nullable=False),
        sa.Column('variant_id', sa.String(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='VND'),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('compare_at', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount >= 0', name='check_variant_price_amount'),
        sa.ForeignKeyConstraint(['price_list_id'], ['tenant_price_list.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['tenant_offering_variant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('price_list_id', 'variant_id', name='uq_offering_variant_price_list_item')
    )

    op.create_table(
        'tenant_inventory_item',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('variant_id', sa.String(), nullable=False),
        sa.Column('location_id', sa.String(), nullable=False),
        sa.Column('stock_qty', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('safety_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('stock_qty >= 0', name='check_offering_inventory_item_qty'),
        sa.ForeignKeyConstraint(['location_id'], ['tenant_inventory_location.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['tenant_offering_variant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'variant_id', 'location_id', name='uq_offering_inventory_item_unique')
    )

    op.create_table(
        'bot_use_case',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('offering_id', sa.String(), nullable=True),
        sa.Column('scenario', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['offering_id'], ['tenant_offering.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'bot_comparison',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('offering_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('comparison_data', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'bot_faq',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('offering_id', sa.String(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['offering_id'], ['tenant_offering.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'bot_capability',
        sa.Column('bot_version_id', sa.String(), nullable=False),
        sa.Column('capability_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_version_id'], ['bot_version.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['capability_id'], ['system_capability.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('bot_version_id', 'capability_id')
    )
    
    op.create_table(
        'bot_channel_config',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bot_version_id', sa.String(), nullable=False),
        sa.Column('channel_code', sa.String(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_version_id'], ['bot_version.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bot_version_id', 'channel_code', name='uq_channel_config')
    )

    op.create_table(
        'tenant_guardrail',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('condition_expression', sa.Text(), nullable=False),
        sa.Column('violation_action', sa.String(), nullable=False, server_default='block'),
        sa.Column('fallback_message', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_guardrail_tenant_code')
    )


    op.create_table(
        'tenant_semantic_cache',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('hit_count', sa.Integer(), server_default='0'),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'runtime_turn',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('speaker', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('ui_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['runtime_session.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'runtime_context_slot',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('source', sa.String(), nullable=False, server_default='user'),
        sa.Column('source_turn_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['runtime_session.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_turn_id'], ['runtime_turn.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'runtime_decision_event',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('input_turn_id', sa.String(), nullable=True),
        sa.Column('bot_version_id', sa.String(), nullable=False),
        sa.Column('tier_code', sa.String(), nullable=True),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_version_id'], ['bot_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['input_turn_id'], ['runtime_turn.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['runtime_session.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'runtime_guardrail_check',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('decision_id', sa.String(), nullable=False),
        sa.Column('guardrail_id', sa.String(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('violation_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['runtime_decision_event.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guardrail_id'], ['tenant_guardrail.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', 'decision_id', 'guardrail_id')
    )
    
    op.create_table(
        'runtime_action_execution',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('decision_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['runtime_decision_event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'migration_job',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.String(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False, server_default='web_scraper'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('batch_metadata', sa.JSON(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('staged_data', sa.JSON(), nullable=True),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bot.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domain.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # DATABASE VIEWS
    op.execute("""
        CREATE OR REPLACE VIEW offering_inventory_status_view AS
        SELECT 
            ov.tenant_id,
            o.id AS offering_id,
            o.code AS offering_code,
            over.name AS offering_name,
            ov.id AS variant_id,
            ov.sku,
            ov.name AS variant_name,
            COALESCE(SUM(ii.stock_qty), 0) AS aggregate_qty,
            COALESCE(SUM(ii.safety_stock), 0) AS aggregate_safety_stock,
            CASE 
                WHEN COALESCE(SUM(ii.stock_qty), 0) > COALESCE(SUM(ii.safety_stock), 0) THEN 'in_stock'
                WHEN COALESCE(SUM(ii.stock_qty), 0) > 0 THEN 'low_stock'
                ELSE 'out_of_stock'
            END AS stock_status
        FROM 
            tenant_offering_variant ov
        JOIN 
            tenant_offering o ON ov.offering_id = o.id
        LEFT JOIN 
            tenant_offering_version over ON over.offering_id = o.id AND over.status = 'active'
        LEFT JOIN 
            tenant_inventory_item ii ON ov.id = ii.variant_id
        GROUP BY 
            ov.tenant_id, o.id, o.code, over.name, ov.id, ov.sku, ov.name;
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS offering_inventory_status_view")
    
    # Order: Children first, then Parents
    op.drop_table('runtime_action_execution')
    op.drop_table('runtime_guardrail_check')
    op.drop_table('runtime_decision_event')
    op.drop_table('runtime_context_slot')
    op.drop_table('runtime_turn')
    op.drop_table('runtime_session')
    op.drop_table('tenant_semantic_cache')
    op.drop_table('tenant_guardrail')
    op.drop_table('bot_channel_config')
    op.drop_table('bot_capability')
    op.drop_table('bot_comparison')
    op.drop_table('bot_faq')
    op.drop_table('bot_use_case')
    op.drop_table('migration_job')
    op.drop_table('tenant_inventory_item')
    op.drop_table('tenant_inventory_location')
    op.drop_table('tenant_variant_price')
    op.drop_table('tenant_price_list')
    op.drop_table('tenant_sales_channel')
    op.drop_table('tenant_offering_variant')
    # Drop trigger and function before dropping table
    op.execute("DROP TRIGGER IF EXISTS trg_check_domain_boundary_attr_val ON tenant_offering_attribute_value")
    op.execute("DROP FUNCTION IF EXISTS check_domain_boundary_attr_val()")
    op.drop_table('tenant_offering_attribute_value')
    op.drop_table('tenant_offering_version')
    op.drop_table('tenant_offering')
    op.drop_table('bot_version')
    op.drop_table('bot')
    op.drop_table('system_capability')
    op.drop_table('tenant_attribute_config')
    op.drop_table('domain_attribute_definition')
    op.drop_table('knowledge_domain')
    op.drop_table('user_account')
    op.drop_table('tenant')
    
    op.execute("DROP EXTENSION IF EXISTS vector")
