"""Converters from domain objects to schemas"""
from backend.domain.tenant import Tenant, Channel
from backend.domain.catalog import Product, ProductAttribute, UseCase, FAQ
from backend.domain.intent import Intent, IntentPattern, IntentHint, IntentAction
from backend.domain.migration import MigrationJob
from backend.domain.observability import ConversationLog, FailedQuery
from backend.schemas.admin import (
    TenantResponse,
    ChannelResponse,
    ProductResponse,
    ProductAttributeResponse,
    UseCaseResponse,
    FAQResponse,
    IntentResponse,
    IntentPatternResponse,
    IntentHintResponse,
    IntentActionResponse,
    MigrationJobResponse,
    ConversationLogResponse,
    FailedQueryResponse,
)


def tenant_to_schema(tenant: Tenant) -> TenantResponse:
    """Convert Tenant domain object to schema"""
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        settings_version=tenant.settings_version,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


def channel_to_schema(channel: Channel) -> ChannelResponse:
    """Convert Channel domain object to schema"""
    return ChannelResponse(
        id=channel.id,
        tenant_id=channel.tenant_id,
        type=channel.type,
        enabled=channel.enabled,
        config_json=channel.config_json,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


def product_to_schema(product: Product) -> ProductResponse:
    """Convert Product domain object to schema"""
    return ProductResponse(
        id=product.id,
        tenant_id=product.tenant_id,
        sku=product.sku,
        slug=product.slug,
        name=product.name,
        category=product.category,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


def product_attribute_to_schema(attr: ProductAttribute) -> ProductAttributeResponse:
    """Convert ProductAttribute domain object to schema"""
    return ProductAttributeResponse(
        id=attr.id,
        attributes_key=attr.attributes_key,
        attributes_value=attr.attributes_value,
        attributes_value_type=attr.attributes_value_type
    )


def use_case_to_schema(uc: UseCase) -> UseCaseResponse:
    """Convert UseCase domain object to schema"""
    return UseCaseResponse(
        id=uc.id,
        type=uc.type,
        description=uc.description
    )


def faq_to_schema(faq: FAQ) -> FAQResponse:
    """Convert FAQ domain object to schema"""
    return FAQResponse(
        id=faq.id,
        scope=faq.scope,
        product_id=faq.product_id,
        question=faq.question,
        answer=faq.answer
    )


def intent_to_schema(intent: Intent) -> IntentResponse:
    """Convert Intent domain object to schema"""
    return IntentResponse(
        id=intent.id,
        tenant_id=intent.tenant_id,
        name=intent.name,
        domain=intent.domain,
        priority=intent.priority,
        created_at=intent.created_at,
        updated_at=intent.updated_at
    )


def intent_pattern_to_schema(pattern: IntentPattern) -> IntentPatternResponse:
    """Convert IntentPattern domain object to schema"""
    return IntentPatternResponse(
        id=pattern.id,
        type=pattern.type,
        pattern=pattern.pattern,
        weight=pattern.weight
    )


def intent_hint_to_schema(hint: IntentHint) -> IntentHintResponse:
    """Convert IntentHint domain object to schema"""
    return IntentHintResponse(
        id=hint.id,
        hint_text=hint.hint_text
    )


def intent_action_to_schema(action: IntentAction) -> IntentActionResponse:
    """Convert IntentAction domain object to schema"""
    return IntentActionResponse(
        id=action.id,
        action_type=action.action_type,
        config_json=action.config_json,
        priority=action.priority
    )


def migration_job_to_schema(job: MigrationJob) -> MigrationJobResponse:
    """Convert MigrationJob domain object to schema"""
    return MigrationJobResponse(
        id=job.id,
        tenant_id=job.tenant_id,
        source_type=job.source_type,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


def conversation_log_to_schema(log: ConversationLog) -> ConversationLogResponse:
    """Convert ConversationLog domain object to schema"""
    return ConversationLogResponse(
        id=log.id,
        tenant_id=log.tenant_id,
        channel_id=log.channel_id,
        intent=log.intent,
        domain=log.domain,
        success=log.success,
        created_at=log.created_at
    )


def failed_query_to_schema(query: FailedQuery) -> FailedQueryResponse:
    """Convert FailedQuery domain object to schema"""
    return FailedQueryResponse(
        id=query.id,
        tenant_id=query.tenant_id,
        query=query.query,
        reason=query.reason,
        created_at=query.created_at
    )
