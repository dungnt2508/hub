from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.infrastructure.database.repositories import KnowledgeDomainRepository
from app.infrastructure.database.repositories import DomainAttributeDefinitionRepository, TenantAttributeConfigRepository
from app.interfaces.api.dependencies import get_current_tenant_id

ontology_router = APIRouter(prefix="/knowledge", tags=["ontology"])  # Match frontend path /api/knowledge

# ========== Schemas ==========

class KnowledgeDomainRead(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    domain_type: str

    class Config:
        from_attributes = True

class DomainAttributeDefinitionRead(BaseModel):
    id: str
    domain_id: str
    key: str
    value_type: str
    semantic_type: Optional[str] = None
    value_constraint: Optional[Dict[str, Any]] = None
    scope: str

    class Config:
        from_attributes = True

class TenantAttributeConfigRead(BaseModel):
    id: str
    tenant_id: str
    attribute_def_id: str
    label: Optional[str] = None
    is_display: bool
    is_searchable: bool

    class Config:
        from_attributes = True

class TenantAttributeConfigUpdate(BaseModel):
    label: Optional[str] = None
    is_display: Optional[bool] = None
    is_searchable: Optional[bool] = None

# ========== Endpoints ==========

@ontology_router.get("/domains", response_model=List[KnowledgeDomainRead])
async def list_domains(
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách tất cả Knowledge Domains (Global)"""
    repo = KnowledgeDomainRepository(db)
    domains = await repo.get_multi()
    return domains

@ontology_router.post("/domains", response_model=KnowledgeDomainRead)
async def create_domain(
    domain_in: Dict[str, Any],
    db: AsyncSession = Depends(get_session)
):
    """Tạo mới một Knowledge Domain (Global)"""
    repo = KnowledgeDomainRepository(db)
    existing = await repo.get_by_code(domain_in.get("code"))
    if existing:
        raise HTTPException(status_code=400, detail=f"Domain code '{domain_in.get('code')}' already exists")
    
    return await repo.create(domain_in)

@ontology_router.get("/attribute-definitions", response_model=List[DomainAttributeDefinitionRead])
async def list_attribute_definitions(
    domain_id: Optional[str] = Query(None, description="Filter by domain ID"),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách attribute definitions (Global Ontology)"""
    repo = DomainAttributeDefinitionRepository(db)
    if domain_id:
        definitions = await repo.get_by_domain(domain_id)
    else:
        # Get all if no domain_id specified
        from app.infrastructure.database.base import BaseRepository
        from app.infrastructure.database.models.knowledge import DomainAttributeDefinition
        repo_all = BaseRepository(DomainAttributeDefinition, db)
        definitions = await repo_all.get_multi()
    return definitions

@ontology_router.post("/attribute-definitions", response_model=DomainAttributeDefinitionRead)
async def create_attribute_definition(
    attr_def_in: Dict[str, Any],
    db: AsyncSession = Depends(get_session)
):
    """Định nghĩa một thuộc tính mới cho Domain (Global)"""
    repo = DomainAttributeDefinitionRepository(db)
    existing = await repo.get_by_key(attr_def_in.get("key"), attr_def_in.get("domain_id"))
    if existing:
        raise HTTPException(status_code=400, detail=f"Attribute key '{attr_def_in.get('key')}' already exists for this domain")
    
    return await repo.create(attr_def_in)

@ontology_router.get("/attribute-configs")
async def list_tenant_configs(
    domain_id: Optional[str] = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách cấu hình hiển thị/tìm kiếm của tenant"""
        
    repo = TenantAttributeConfigRepository(db)
    return await repo.get_all_for_tenant(tenant_id, domain_id)

@ontology_router.post("/attribute-definitions/{attr_def_id}/config")
async def update_tenant_config(
    attr_def_id: str,
    config_in: TenantAttributeConfigUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Ghi đè cấu hình hiển thị cho một thuộc tính (Tenant scope)"""
        
    repo = TenantAttributeConfigRepository(db)
    
    # Check if exists
    config = await repo.get_config(tenant_id, attr_def_id)
    if config:
        return await repo.update(config, config_in.model_dump(exclude_unset=True))
    else:
        # Create new override
        data = {
            "tenant_id": tenant_id,
            "attribute_def_id": attr_def_id,
            **config_in.model_dump(exclude_unset=True)
        }
        return await repo.create(data, tenant_id=tenant_id)
