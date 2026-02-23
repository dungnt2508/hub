"""
Catalog API Router - Support Catalog V4 (Versioning, Pricing, Inventory)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.infrastructure.database.engine import get_session
from app.core.services.catalog_service import CatalogService
from app.interfaces.api.dependencies import get_current_tenant_id

catalog_router = APIRouter(prefix="/catalog", tags=["catalog"])  # Prefix sẽ được thêm khi include trong main.py

# ========== Schemas ==========

class InventoryStatusResponse(BaseModel):
    tenant_id: str
    offering_code: str
    offering_name: str
    sku: str
    variant_name: str
    aggregate_qty: int
    aggregate_safety_stock: int
    stock_status: str

class InventoryLocationResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: Optional[str] = None

class InventoryUpdateRequest(BaseModel):
    sku: str
    location_code: str
    new_qty: int

class OfferingVersionResponse(BaseModel):
    id: str
    offering_id: str
    version: int
    name: str
    description: Optional[str]
    status: str
    created_at: Any

class OfferingVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PriceListResponse(BaseModel):
    id: str
    tenant_id: str
    channel_id: Optional[str]
    code: str
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]

    class Config:
        from_attributes = True

class SalesChannelResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True

class OfferingSummaryResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    domain_id: str
    version: int
    version_id: str
    price: Optional[Dict[str, Any]]
    inventory: List[Dict[str, Any]]
    status: str

class OfferingVariantCreate(BaseModel):
    sku: str
    name: str

class OfferingVariantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

class OfferingVariantResponse(BaseModel):
    id: str
    offering_id: str
    sku: str
    name: str
    status: str
    created_at: Any

class VariantPriceSet(BaseModel):
    price_list_id: str
    amount: float
    currency: str = "VND"
    price_type: str = "base"
    compare_at: Optional[float] = None

class OfferingCreate(BaseModel):
    code: str
    name: str
    bot_id: Optional[str] = None
    domain_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "draft"

class OfferingUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class OfferingAttributeCreate(BaseModel):
    attribute_key: str
    attribute_value: Any
    value_type: str = "text"
    display_order: int = 0

class OfferingAttributeUpdate(BaseModel):
    attribute_key: Optional[str] = None
    attribute_value: Optional[Any] = None
    value_type: Optional[str] = None
    display_order: Optional[int] = None

class OfferingAttributeResponse(BaseModel):
    id: str
    offering_version_id: str
    attribute_key: str
    label: str
    attribute_value: str
    value_type: str
    is_display: bool = True
    display_order: int = 0
    is_searchable: bool = False

    class Config:
        from_attributes = True

class OfferingResponse(BaseModel):
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    code: str
    name: str
    description: Optional[str] = None
    version: int = 1
    version_id: Optional[str] = None
    price: Optional[Dict[str, Any]] = None
    inventory: List[Dict[str, Any]] = []
    status: str
    created_at: Any
    updated_at: Optional[Any] = None
    attributes: List[OfferingAttributeResponse] = []

    class Config:
        from_attributes = True

# ========== Endpoints ==========

@catalog_router.get("/offerings", response_model=List[OfferingSummaryResponse])
async def list_offerings(
    bot_id: Optional[str] = Query(None, description="Lọc offering theo domain của Bot"),
    domain_id: Optional[str] = Query(None, description="Lọc offering theo Domain"),
    channel: str = Query("WEB", description="Kênh bán hàng để lấy giá tương ứng"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Lấy danh sách sản phẩm kèm thông tin hợp nhất (Version + Giá + Kho).
    Dành cho Bot và Admin Dashboard.
    Bot là executor, không phải owner. Products được filter theo tenant_id + domain_id.
    """
    
    # Nếu có bot_id, lấy domain_id từ bot (không filter trực tiếp theo bot_id)
    resolved_domain_id = domain_id
    if bot_id and not resolved_domain_id:
        from app.infrastructure.database.repositories import BotRepository
        bot_repo = BotRepository(db)
        bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
        if bot and bot.domain_id:
            resolved_domain_id = bot.domain_id
        
    service = CatalogService(db)
    offerings = await service.offering_repo.get_active_offerings(tenant_id, domain_id=resolved_domain_id)
    
    result = []
    for o in offerings:
        summary = await service.get_offering_for_bot(
            tenant_id, o.code, channel, domain_id=o.domain_id, enabled_capabilities=["inventory"]
        )
        if summary:
            result.append(summary)
            
    return result

@catalog_router.get("/offerings/{code}", response_model=OfferingSummaryResponse)
async def get_offering_detail(
    code: str,
    bot_id: Optional[str] = Query(None, description="Dùng để lấy domain_id từ bot"),
    domain_id: Optional[str] = Query(None, description="Domain của offering"),
    channel: str = Query("WEB"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy chi tiết một sản phẩm theo code"""
    
    # Nếu có bot_id, lấy domain_id từ bot
    resolved_domain_id = domain_id
    if bot_id and not resolved_domain_id:
        from app.infrastructure.database.repositories import BotRepository
        bot_repo = BotRepository(db)
        bot = await bot_repo.get(bot_id, tenant_id=tenant_id)
        if bot and bot.domain_id:
            resolved_domain_id = bot.domain_id
        
    service = CatalogService(db)
    summary = await service.get_offering_for_bot(
        tenant_id, code, channel, domain_id=resolved_domain_id, enabled_capabilities=["inventory"]
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Offering not found or inactive")
        
    return summary

@catalog_router.post("/offerings", response_model=OfferingResponse)
async def create_offering(
    offering: OfferingCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Create offering for current authenticated user's tenant"""
    service = CatalogService(db)
    # Check if Code already exists
    existing_code = await service.offering_repo.get_by_code(offering.code, tenant_id)
    if existing_code:
        raise HTTPException(status_code=400, detail=f"Mã offering '{offering.code}' đã tồn tại")

    if not offering.domain_id:
        raise HTTPException(status_code=400, detail="domain_id là bắt buộc")

    # Create Offering
    offering_obj = await service.offering_repo.create({
        "code": offering.code,
        "bot_id": offering.bot_id,
        "domain_id": offering.domain_id,
        "status": offering.status,
        "tenant_id": tenant_id
    })
    
    # Create Initial Version
    new_version = await service.version_repo.create({
        "offering_id": offering_obj.id,
        "version": 1,
        "name": offering.name,
        "description": offering.description,
        "status": "draft"
    })
    
    return {
        "id": offering_obj.id,
        "tenant_id": offering_obj.tenant_id,
        "code": offering_obj.code,
        "name": new_version.name,
        "description": new_version.description,
        "status": offering_obj.status,
        "created_at": offering_obj.created_at,
        "updated_at": offering_obj.updated_at,
        "attributes": []
    }

@catalog_router.put("/offerings/{offering_id}", response_model=OfferingResponse)
async def update_offering(
    offering_id: str,
    offering_in: OfferingUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Update offering and its metadata"""
    service = CatalogService(db)
    db_obj = await service.offering_repo.get(offering_id, tenant_id=tenant_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Offering not found")
    
    off_data = offering_in.model_dump(exclude_unset=True)
    version_data = {}
    for k in ["name", "description"]:
        if k in off_data:
            version_data[k] = off_data.pop(k)

    if off_data:
        await service.offering_repo.update(db_obj, off_data, tenant_id=tenant_id)
    
    if version_data:
        version = await service.version_repo.get_active_version(offering_id, tenant_id=tenant_id)
        if not version:
            version = await service.version_repo.get_latest_version(offering_id, tenant_id=tenant_id)
        if version:
            await service.version_repo.update(version, version_data)
    
    return await get_offering_detail_by_id(offering_id, tenant_id=tenant_id, db=db)

async def get_offering_detail_by_id(offering_id: str, tenant_id: str, db: AsyncSession):
    # Helper to re-fetch offering after update
    from app.infrastructure.database.repositories import OfferingRepository, OfferingVersionRepository, OfferingAttributeRepository
    o_repo = OfferingRepository(db)
    v_repo = OfferingVersionRepository(db)
    a_repo = OfferingAttributeRepository(db)
    
    offering = await o_repo.get(offering_id, tenant_id=tenant_id)
    version = await v_repo.get_active_version(offering_id, tenant_id=tenant_id)
    if not version:
        version = await v_repo.get_latest_version(offering_id, tenant_id=tenant_id)
    
    attrs = await a_repo.get_by_offering(offering_id)
    
    return {
        "id": offering.id,
        "tenant_id": offering.tenant_id,
        "code": offering.code,
        "name": version.name if version else "Unnamed",
        "description": version.description if version else None,
        "status": offering.status,
        "created_at": offering.created_at,
        "updated_at": offering.updated_at,
        "attributes": [
            {
                "id": attr.id,
                "offering_version_id": attr.offering_version_id,
                "attribute_key": attr.definition.key if attr.definition else "unknown",
                "label": attr.definition.key if attr.definition else "unknown",
                "attribute_value": str(attr.value_text or attr.value_number or attr.value_bool or attr.value_json or ""),
                "value_type": attr.definition.value_type if attr.definition else "text",
                "display_order": 0
            }
            for attr in attrs
        ]
    }

@catalog_router.delete("/offerings/{offering_id}")
async def delete_offering(
    offering_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    service = CatalogService(db)
    await service.offering_repo.delete(offering_id, tenant_id=tenant_id)
    return {"message": "Offering deleted successfully"}

# ========== Offering Attributes ==========

@catalog_router.get("/versions/{version_id}/attributes", response_model=List[OfferingAttributeResponse])
async def list_version_attributes(
    version_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """List attributes for an offering version"""
    service = CatalogService(db)
    attributes = await service.attr_val_repo.get_by_version(version_id, tenant_id=tenant_id)
    resolved = await service.attr_resolver.resolve_attributes(tenant_id, attributes)
    
    return [
        {
            "id": attr["id"],
            "offering_version_id": version_id,
            "attribute_key": attr["key"],
            "label": attr["label"],
            "attribute_value": str(attr["value"]),
            "value_type": attr["value_type"],
            "is_display": attr["is_display"],
            "display_order": attr["display_order"],
            "is_searchable": attr["is_searchable"]
        }
        for attr in resolved
    ]

@catalog_router.post("/versions/{version_id}/attributes", response_model=OfferingAttributeResponse)
async def create_offering_attribute(
    version_id: str,
    attribute: OfferingAttributeCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Assign attribute value to an offering version with proper type validation"""
    service = CatalogService(db)
    version = await service.version_repo.get(version_id, tenant_id=tenant_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    offering = await service.offering_repo.get(version.offering_id, tenant_id=tenant_id)
    if not offering:
         raise HTTPException(status_code=403, detail="Forbidden")

    from app.infrastructure.database.repositories import DomainAttributeDefinitionRepository
    def_repo = DomainAttributeDefinitionRepository(db)
    attr_def = await def_repo.get_by_key(attribute.attribute_key, offering.domain_id)
    
    if not attr_def:
        raise HTTPException(status_code=400, detail=f"Attribute '{attribute.attribute_key}' not found in domain")
    
    # Validate value type matches definition
    if attr_def.value_type != attribute.value_type:
        raise HTTPException(
            status_code=400, 
            detail=f"Value type mismatch: attribute '{attribute.attribute_key}' expects '{attr_def.value_type}' but got '{attribute.value_type}'"
        )
    
    # CHECK DUPLICATE before insert - this is crucial!
    from sqlalchemy import select
    stmt = select(service.attr_val_repo.model).where(
        service.attr_val_repo.model.offering_version_id == version_id,
        service.attr_val_repo.model.attribute_def_id == attr_def.id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Attribute '{attribute.attribute_key}' already exists for this version"
        )
    
    # Use validator to ensure constraint compliance
    from app.core.services.attribute_validator import AttributeValueValidator
    try:
        attr_data = {
            "offering_version_id": version_id,
            "attribute_def_id": attr_def.id
        }
        # Validate and coerce value
        attr_data.update(AttributeValueValidator.validate_and_coerce(attribute.attribute_value, attr_def))
        # Create attribute
        db_obj = await service.attr_val_repo.create(attr_data)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create attribute: {str(e)}")
    
    return {
        "id": db_obj.id,
        "offering_version_id": version_id,
        "attribute_key": attr_def.key,
        "label": attr_def.key,
        "attribute_value": str(attribute.attribute_value),
        "value_type": attr_def.value_type,
        "is_display": True,
        "display_order": 0,
        "is_searchable": False
    }

@catalog_router.delete("/versions/{version_id}/attributes/{attribute_id}")
async def delete_offering_attribute(
    version_id: str,
    attribute_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    service = CatalogService(db)
    success = await service.attr_val_repo.delete(attribute_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return {"message": "Attribute deleted successfully"}


@catalog_router.get("/inventory/status", response_model=List[InventoryStatusResponse])
async def get_all_inventory_status(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy trạng thái tồn kho tổng hợp từ Database View"""
        
    service = CatalogService(db)
    return await service.inventory_repo.get_all_stock_status(tenant_id, bot_id=None)

@catalog_router.get("/locations", response_model=List[InventoryLocationResponse])
async def list_locations(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách điểm lưu kho"""
        
    service = CatalogService(db)
    return await service.loc_repo.get_multi(tenant_id=tenant_id)

@catalog_router.post("/inventory/update")
async def update_inventory(
    item: InventoryUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Cập nhật tồn kho cho SKU"""
        
    service = CatalogService(db)
    success = await service.update_inventory(
        tenant_id=tenant_id,
        sku=item.sku,
        location_code=item.location_code,
        new_qty=item.new_qty
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update inventory. Check SKU and Location Code.")
        
    return {"message": "Inventory updated successfully"}

@catalog_router.get("/offerings/{offering_id}/versions", response_model=List[OfferingVersionResponse])
async def list_offering_versions(
    offering_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách tất cả phiên bản của một offering"""
        
    service = CatalogService(db)
    # Lấy tất cả version của offering_id
    versions = await service.version_repo.get_multi(offering_id=offering_id)
    return versions

@catalog_router.post("/offerings/{offering_id}/publish")
async def publish_offering_version(
    offering_id: str,
    version: int,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Kích hoạt một phiên bản offering cụ thể"""
        
    service = CatalogService(db)
    success = await service.publish_version(offering_id, version, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
        
    return {"message": "Version published successfully"}

@catalog_router.post("/offerings/{offering_id}/versions", response_model=OfferingVersionResponse)
async def create_new_version(
    offering_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    copy_from: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_session)
):
    """Tạo một phiên bản nháp mới"""
        
    service = CatalogService(db)
    # Check ownership
    offering = await service.offering_repo.get(offering_id, tenant_id=tenant_id)
    if not offering:
        raise HTTPException(status_code=404, detail="Offering not found")
        
    new_v = await service.create_draft_version(offering_id, tenant_id=tenant_id, copy_from_version=copy_from)
    return new_v

@catalog_router.put("/versions/{version_id}", response_model=OfferingVersionResponse)
async def update_version_metadata(
    version_id: str,
    version_in: OfferingVersionUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Cập nhật thông tin phiên bản (Tên, mô tả)"""
        
    service = CatalogService(db)
    v_repo = service.version_repo
    version = await v_repo.get(version_id, tenant_id=tenant_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Verify ownership through offering
    offering = await service.offering_repo.get(version.offering_id, tenant_id=tenant_id)
    if not offering:
         raise HTTPException(status_code=403, detail="Forbidden")

    updated = await v_repo.update(version, version_in.model_dump(exclude_unset=True))
    return updated

@catalog_router.delete("/versions/{version_id}")
async def delete_version(
    version_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Xóa một phiên bản (chỉ khi là bản nháp và không phải bản duy nhất)"""
        
    service = CatalogService(db)
    version = await service.version_repo.get(version_id, tenant_id=tenant_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.status == "active":
        raise HTTPException(status_code=400, detail="Cannot delete an active version. Archive or publish another one first.")

    # Verify ownership
    offering = await service.offering_repo.get(version.offering_id, tenant_id=tenant_id)
    if not offering:
         raise HTTPException(status_code=403, detail="Forbidden")
         
    await service.version_repo.delete(version_id, tenant_id=tenant_id)
    return {"message": "Version deleted"}

# --- Variant & Price Management ---

@catalog_router.post("/offerings/{offering_id}/variants", response_model=OfferingVariantResponse)
async def create_variant(
    offering_id: str,
    variant_in: OfferingVariantCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Tạo một biến thể mới cho offering"""
        
    service = CatalogService(db)
    # Check if SKU exists
    existing = await service.variant_repo.get_by_sku(variant_in.sku, tenant_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU '{variant_in.sku}' already exists")
        
    new_v = await service.create_variant(offering_id, tenant_id, variant_in.sku, variant_in.name)
    return new_v

@catalog_router.put("/variants/{variant_id}", response_model=OfferingVariantResponse)
async def update_variant(
    variant_id: str,
    variant_in: OfferingVariantUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Cập nhật thông tin biến thể"""
        
    service = CatalogService(db)
    updated = await service.update_variant(variant_id, tenant_id=tenant_id, **variant_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found")
    return updated

@catalog_router.delete("/variants/{variant_id}")
async def delete_variant(
    variant_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Xóa biến thể"""
    service = CatalogService(db)
    success = await service.delete_variant(variant_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Variant not found")
    await service.variant_repo.delete(variant_id, tenant_id=tenant_id)
    return {"message": "Variant deleted successfully"}

@catalog_router.get("/price-lists", response_model=List[PriceListResponse])
async def list_price_lists(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách các bảng giá hiện có"""
       
    service = CatalogService(db)
    return await service.price_repo.get_multi(tenant_id=tenant_id)


@catalog_router.post("/channels/{channel_code}/price-list")
async def get_or_create_price_list_for_channel(
    channel_code: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy hoặc tạo price_list cho channel cụ thể"""
    from app.infrastructure.database.repositories import TenantSalesChannelRepository
    
    service = CatalogService(db)
    channel_repo = TenantSalesChannelRepository(db)
    
    # 1. Find channel
    channel = await channel_repo.get_by_code(channel_code, tenant_id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_code} not found")
    
    # 2. Find or create price_list for this channel
    from sqlalchemy import select
    from app.infrastructure.database.models.offering import TenantPriceList
    
    stmt = select(TenantPriceList).where(
        TenantPriceList.tenant_id == tenant_id,
        TenantPriceList.channel_id == channel.id
    )
    result = await db.execute(stmt)
    price_list = result.scalar_one_or_none()
    
    if not price_list:
        # Create new price_list for this channel
        import uuid
        price_list = TenantPriceList(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel_id=channel.id,
            code=f"{channel_code}-LIST"
        )
        db.add(price_list)
        await db.flush()
        print(f"✅ Created price_list for channel {channel_code}: {price_list.id}")
    
    return {
        "id": price_list.id,
        "tenant_id": price_list.tenant_id,
        "channel_id": price_list.channel_id,
        "code": price_list.code,
        "valid_from": price_list.valid_from,
        "valid_to": price_list.valid_to,
        "channel_code": channel_code
    }

@catalog_router.get("/channels", response_model=List[SalesChannelResponse])
async def list_channels(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Lấy danh sách các kênh bán hàng"""
       
    service = CatalogService(db)
    return await service.channel_repo.get_multi(tenant_id=tenant_id)

@catalog_router.post("/variants/{variant_id}/prices")
async def set_variant_price(
    variant_id: str,
    price_in: VariantPriceSet,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """Thiết lập hoặc cập nhật giá cho biến thể"""
    if not (price_in.price_list_id or "").strip():
        raise HTTPException(status_code=400, detail="price_list_id is required. Tenant must have at least one price list.")
       
    service = CatalogService(db)
    try:
        # Verify price_list exists, if not raise error with helpful message
        from app.infrastructure.database.models.offering import TenantPriceList
        from sqlalchemy import select
        
        price_list = await db.execute(
            select(TenantPriceList).where(
                TenantPriceList.id == price_in.price_list_id,
                TenantPriceList.tenant_id == tenant_id
            )
        )
        if not price_list.scalar_one_or_none():
            raise HTTPException(
                status_code=404, 
                detail=f"Price list {price_in.price_list_id} not found for this tenant"
            )
        
        price_obj = await service.set_variant_price(
            variant_id=variant_id,
            price_list_id=price_in.price_list_id,
            tenant_id=tenant_id,
            amount=price_in.amount,
            currency=price_in.currency,
            compare_at=price_in.compare_at
        )
        return price_obj
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)
