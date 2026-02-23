"""
Knowledge Base Management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import FAQRepository, SemanticCacheRepository
from app.infrastructure.database.base import BaseRepository
from app.infrastructure.database.models.knowledge import BotUseCase, BotComparison
from app.interfaces.api.dependencies import get_current_tenant_id

knowledge_router = APIRouter(tags=["knowledge"])

# ========== Schemas ==========

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    priority: int = 0
    domain_id: Optional[str] = None

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    domain_id: Optional[str] = None

class UseCaseCreate(BaseModel):
    domain_id: Optional[str] = None
    offering_id: Optional[str] = None
    scenario: str
    answer: str
    priority: int = 0
    is_active: bool = True

class UseCaseUpdate(BaseModel):
    domain_id: Optional[str] = None
    offering_id: Optional[str] = None
    scenario: Optional[str] = None
    answer: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class UseCaseResponse(BaseModel):
    id: str
    tenant_id: str
    domain_id: Optional[str]
    offering_id: Optional[str] = None
    scenario: str
    answer: str
    priority: int
    is_active: bool

    model_config = {"from_attributes": True}

class ComparisonCreate(BaseModel):
    domain_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    offering_ids: List[str]
    comparison_data: Optional[Dict[str, Any]] = None
    is_active: bool = True

class ComparisonUpdate(BaseModel):
    domain_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    offering_ids: Optional[List[str]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ComparisonResponse(BaseModel):
    id: str
    tenant_id: str
    domain_id: Optional[str]
    title: str
    description: Optional[str]
    offering_ids: List[str]
    comparison_data: Optional[Dict[str, Any]]
    is_active: bool

    model_config = {"from_attributes": True}

class CacheCreate(BaseModel):
    query_text: str
    response_text: str

# ========== Endpoints ==========

@knowledge_router.get("/faqs")
async def list_faqs(
    tenant_id: str = Depends(get_current_tenant_id),
    domain_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session)
):
    repo = FAQRepository(db)
    filters = {}
    if domain_id:
        filters["domain_id"] = domain_id
    return await repo.get_multi(tenant_id=tenant_id, **filters)

@knowledge_router.post("/faqs")
async def create_faq(
    faq: FAQCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = FAQRepository(db)
    return await repo.create(faq.model_dump(), tenant_id=tenant_id)

@knowledge_router.put("/faqs/{faq_id}", response_model=FAQCreate)
async def update_faq(
    faq_id: str,
    faq_in: FAQUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = FAQRepository(db)
    db_obj = await repo.get(faq_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return await repo.update(db_obj, faq_in.model_dump(exclude_unset=True), tenant_id=tenant_id)

@knowledge_router.delete("/faqs/{faq_id}")
async def delete_faq(
    faq_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = FAQRepository(db)
    success = await repo.delete(faq_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"message": "FAQ deleted successfully"}

@knowledge_router.get("/usecases", response_model=List[UseCaseResponse])
async def list_usecases(
    tenant_id: str = Depends(get_current_tenant_id),
    offering_id: Optional[str] = Query(None, description="Filter by offering ID"),
    domain_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotUseCase, db)
    filters = {}
    if offering_id:
        filters["offering_id"] = offering_id
    if domain_id:
        filters["domain_id"] = domain_id
    return await repo.get_multi(tenant_id=tenant_id, **filters)

@knowledge_router.post("/usecases", response_model=UseCaseResponse)
async def create_usecase(
    usecase: UseCaseCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotUseCase, db)
    data = usecase.model_dump()
    # Empty string "" violates FK; must be None for nullable offering_id
    if "offering_id" in data:
        oid = data["offering_id"]
        if not (oid and isinstance(oid, str) and oid.strip()):
            data["offering_id"] = None
    return await repo.create(data, tenant_id=tenant_id)

@knowledge_router.put("/usecases/{usecase_id}", response_model=UseCaseResponse)
async def update_usecase(
    usecase_id: str,
    usecase_in: UseCaseUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotUseCase, db)
    db_obj = await repo.get(usecase_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Use Case not found")
    data = usecase_in.model_dump(exclude_unset=True)
    if "offering_id" in data and not (data["offering_id"] or "").strip():
        data["offering_id"] = None
    return await repo.update(db_obj, data, tenant_id=tenant_id)

@knowledge_router.delete("/usecases/{usecase_id}")
async def delete_usecase(
    usecase_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotUseCase, db)
    success = await repo.delete(usecase_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Use Case not found")
    return {"message": "Use Case deleted successfully"}

@knowledge_router.get("/comparisons", response_model=List[ComparisonResponse])
async def list_comparisons(
    tenant_id: str = Depends(get_current_tenant_id),
    domain_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotComparison, db)
    filters = {}
    if domain_id:
        filters["domain_id"] = domain_id
    return await repo.get_multi(tenant_id=tenant_id, **filters)

@knowledge_router.post("/comparisons", response_model=ComparisonResponse)
async def create_comparison(
    comparison: ComparisonCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotComparison, db)
    return await repo.create(comparison.model_dump(), tenant_id=tenant_id)

@knowledge_router.put("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def update_comparison(
    comparison_id: str,
    comparison_in: ComparisonUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotComparison, db)
    db_obj = await repo.get(comparison_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return await repo.update(db_obj, comparison_in.model_dump(exclude_unset=True), tenant_id=tenant_id)

@knowledge_router.delete("/comparisons/{comparison_id}")
async def delete_comparison(
    comparison_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = BaseRepository(BotComparison, db)
    success = await repo.delete(comparison_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return {"message": "Comparison deleted successfully"}

@knowledge_router.get("/cache")
async def list_cache(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = SemanticCacheRepository(db)
    return await repo.get_multi(tenant_id=tenant_id)

@knowledge_router.post("/cache")
async def create_cache(
    cache: CacheCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    repo = SemanticCacheRepository(db)
    return await repo.create(cache.model_dump(), tenant_id=tenant_id)
