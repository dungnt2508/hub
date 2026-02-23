from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from decimal import Decimal


class DomainType(str, Enum):
    BUSINESS = "business"
    OFFERING = "offering"
    PRODUCT = "product"


class OfferingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class OfferingVersionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AttributeValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class AttributeSemanticType(str, Enum):
    PHYSICAL = "physical"
    FINANCIAL = "financial"
    CATEGORICAL = "categorical"
    IDENTIFIER = "identifier"


class AttributeScope(str, Enum):
    OFFERING = "offering"
    VARIANT = "variant"


class PriceType(str, Enum):
    BASE = "base"
    PROMO = "promo"


class InventoryLocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"


# --- ONTOLOGY ---

class KnowledgeDomain(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    domain_type: DomainType = DomainType.OFFERING
    is_archived: bool = False

    class Config:
        from_attributes = True


class DomainAttributeDefinition(BaseModel):
    id: str
    domain_id: str
    key: str
    value_type: AttributeValueType = AttributeValueType.TEXT
    semantic_type: Optional[AttributeSemanticType] = AttributeSemanticType.CATEGORICAL
    value_constraint: Optional[Dict[str, Any]] = None
    scope: AttributeScope = AttributeScope.OFFERING

    class Config:
        from_attributes = True


class TenantAttributeConfig(BaseModel):
    id: str
    tenant_id: str
    attribute_def_id: str
    label: Optional[str] = None
    is_display: bool = True
    is_searchable: bool = False
    is_required: bool = False
    display_order: int = 0
    ui_config: Optional[Dict[str, Any]] = None
    
    # Optional relationship
    definition: Optional[DomainAttributeDefinition] = None

    class Config:
        from_attributes = True


# --- PRODUCTS ---

class TenantOffering(BaseModel):
    id: str
    tenant_id: str
    domain_id: str
    type: str = "physical"
    code: str
    identity_key: Optional[str] = None
    status: OfferingStatus = OfferingStatus.ACTIVE
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_purchasable(self) -> bool:
        """Offering có thể mua (active và chưa archived)."""
        return self.status == OfferingStatus.ACTIVE and not self.is_archived

    class Config:
        from_attributes = True


class TenantOfferingVersion(BaseModel):
    id: str
    offering_id: str
    version: int
    name: str
    description: Optional[str] = None
    status: OfferingVersionStatus = OfferingVersionStatus.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TenantOfferingAttributeValue(BaseModel):
    id: str
    offering_version_id: str
    attribute_def_id: str
    value_text: Optional[str] = None
    value_number: Optional[Decimal] = None
    value_bool: Optional[bool] = None
    value_json: Optional[Dict[str, Any]] = None
    
    definition: Optional[DomainAttributeDefinition] = None

    class Config:
        from_attributes = True


class TenantOfferingVariant(BaseModel):
    id: str
    tenant_id: str
    offering_id: str
    sku: str
    name: str
    status: OfferingStatus = OfferingStatus.ACTIVE
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- SALES & PRICING ---

class TenantSalesChannel(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: str
    is_active: bool = True

    class Config:
        from_attributes = True


class TenantPriceList(BaseModel):
    id: str
    tenant_id: str
    channel_id: Optional[str] = None
    code: str
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    class Config:
        from_attributes = True


class TenantVariantPrice(BaseModel):
    id: str
    price_list_id: str
    variant_id: str
    currency: str = "VND"
    amount: Decimal
    compare_at: Optional[Decimal] = None

    class Config:
        from_attributes = True


# --- INVENTORY ---

class TenantInventoryLocation(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: Optional[str] = None
    type: InventoryLocationType = InventoryLocationType.WAREHOUSE

    class Config:
        from_attributes = True


class TenantInventoryItem(BaseModel):
    id: str
    tenant_id: str
    variant_id: str
    location_id: str
    stock_qty: int = 0
    safety_stock: int = 0

    class Config:
        from_attributes = True


# --- KNOWLEDGE BASE ---

class BotUseCase(BaseModel):
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    domain_id: str
    offering_id: Optional[str] = None
    scenario: str
    answer: str
    priority: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


class BotFAQ(BaseModel):
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    domain_id: str
    question: str
    answer: str
    category: Optional[str] = None
    priority: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


class BotComparison(BaseModel):
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    domain_id: str
    title: str
    description: Optional[str] = None
    offering_ids: List[str]
    comparison_data: Optional[Dict[str, Any]] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# --- MIGRATION ---

class MigrationSourceType(str, Enum):
    WEB_SCRAPER = "web_scraper"
    EXCEL_UPLOAD = "excel_upload"
    SHOPIFY_SYNC = "shopify_sync"
    HARAVAN_SYNC = "haravan_sync"


class MigrationJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STAGED = "staged"
    COMPLETED = "completed"
    FAILED = "failed"


class MigrationJob(BaseModel):
    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    domain_id: str
    source_type: MigrationSourceType = MigrationSourceType.WEB_SCRAPER
    status: MigrationJobStatus = MigrationJobStatus.PENDING
    batch_metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
    staged_data: Optional[Dict[str, Any]] = None
    error_log: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
