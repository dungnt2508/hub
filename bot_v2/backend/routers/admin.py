"""Admin API router - admin dashboard endpoints"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.database import get_db
from backend.repositories.tenant_repository import TenantRepository
from backend.repositories.catalog_repository import CatalogRepository
from backend.repositories.intent_repository import IntentRepository
from backend.repositories.migration_repository import MigrationRepository
from backend.repositories.observability_repository import ObservabilityRepository
from backend.services.migration_service import MigrationService
from backend.schemas.admin import (
    TenantResponse,
    ChannelResponse,
    ProductResponse,
    ProductDetailResponse,
    IntentResponse,
    IntentDetailResponse,
    MigrationJobResponse,
    ConversationLogResponse,
    FailedQueryResponse,
)
from backend.schemas.admin_requests import TenantCreateRequest
from backend.schemas.converters import (
    tenant_to_schema,
    channel_to_schema,
    product_to_schema,
    product_attribute_to_schema,
    use_case_to_schema,
    faq_to_schema,
    intent_to_schema,
    intent_pattern_to_schema,
    intent_hint_to_schema,
    intent_action_to_schema,
    migration_job_to_schema,
    conversation_log_to_schema,
    failed_query_to_schema,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])


# Tenant Management
@router.get("/tenants")
async def list_tenants(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all tenants"""
    repo = TenantRepository(db)
    tenants = await repo.list_tenants(limit=limit, offset=offset)
    return {"tenants": [tenant_to_schema(t).dict() for t in tenants]}


@router.post("/tenants")
async def create_tenant(
    request: TenantCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant"""
    repo = TenantRepository(db)
    
    # Check if tenant name already exists
    existing = await repo.get_tenant_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Tenant with this name already exists")
    
    tenant = await repo.create_tenant(
        name=request.name,
        status=request.status,
        plan=request.plan
    )
    return tenant_to_schema(tenant).dict()


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get tenant by ID"""
    repo = TenantRepository(db)
    tenant = await repo.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_to_schema(tenant).dict()


# Channel Management
@router.get("/tenants/{tenant_id}/channels")
async def list_channels(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List channels for tenant"""
    repo = TenantRepository(db)
    channels = await repo.list_channels(tenant_id)
    return {"channels": [channel_to_schema(c).dict() for c in channels]}


# Catalog Management
@router.get("/tenants/{tenant_id}/products")
async def list_products(
    tenant_id: UUID,
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List products for tenant"""
    repo = CatalogRepository(db)
    products = await repo.search_products(
        tenant_id=tenant_id,
        query=query,
        category=category,
        limit=limit,
        offset=offset
    )
    return {"products": [product_to_schema(p).dict() for p in products]}


@router.get("/tenants/{tenant_id}/products/{product_id}")
async def get_product(
    tenant_id: UUID,
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get product details"""
    repo = CatalogRepository(db)
    product = await repo.get_product(product_id, tenant_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    attributes = await repo.get_product_attributes(product_id, tenant_id)
    use_cases = await repo.get_use_cases(product_id, tenant_id)
    faqs = await repo.get_faqs(tenant_id=tenant_id, product_id=product_id)
    
    return ProductDetailResponse(
        product=product_to_schema(product),
        attributes=[product_attribute_to_schema(a) for a in attributes],
        use_cases=[use_case_to_schema(uc) for uc in use_cases],
        faqs=[faq_to_schema(f) for f in faqs]
    ).dict()


# Intent Management
@router.get("/tenants/{tenant_id}/intents")
async def list_intents(
    tenant_id: UUID,
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List intents for tenant"""
    repo = IntentRepository(db)
    intents = await repo.list_intents(tenant_id=tenant_id, domain=domain)
    return {"intents": [intent_to_schema(i).dict() for i in intents]}


@router.get("/tenants/{tenant_id}/intents/{intent_id}")
async def get_intent(
    tenant_id: UUID,
    intent_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get intent details"""
    repo = IntentRepository(db)
    intent = await repo.get_intent(intent_id, tenant_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    patterns = await repo.get_intent_patterns(intent_id)
    hints = await repo.get_intent_hints(intent_id)
    actions = await repo.get_intent_actions(intent_id)
    
    return IntentDetailResponse(
        intent=intent_to_schema(intent),
        patterns=[intent_pattern_to_schema(p) for p in patterns],
        hints=[intent_hint_to_schema(h) for h in hints],
        actions=[intent_action_to_schema(a) for a in actions]
    ).dict()


# Migration Management
@router.get("/tenants/{tenant_id}/migrations")
async def list_migrations(
    tenant_id: UUID,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List migration jobs"""
    repo = MigrationRepository(db)
    jobs = await repo.list_migration_jobs(
        tenant_id=tenant_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return {"migrations": [migration_job_to_schema(j).dict() for j in jobs]}


@router.post("/tenants/{tenant_id}/migrations")
async def create_migration(
    tenant_id: UUID,
    source_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Create migration job"""
    service = MigrationService(db)
    job = await service.create_migration_job(
        tenant_id=tenant_id,
        source_type=source_type,
        source_data={}
    )
    return migration_job_to_schema(job).dict()


# Observability
@router.get("/tenants/{tenant_id}/logs")
async def list_conversation_logs(
    tenant_id: UUID,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List conversation logs"""
    repo = ObservabilityRepository(db)
    logs = await repo.list_conversation_logs(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset
    )
    return {"logs": [conversation_log_to_schema(l).dict() for l in logs]}


@router.get("/tenants/{tenant_id}/failed-queries")
async def list_failed_queries(
    tenant_id: UUID,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List failed queries"""
    repo = ObservabilityRepository(db)
    queries = await repo.list_failed_queries(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset
    )
    return {"queries": [failed_query_to_schema(q).dict() for q in queries]}
