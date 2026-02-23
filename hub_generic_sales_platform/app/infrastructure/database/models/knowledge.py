"""Knowledge models - Domain-Centric Ontology Architecture"""

import enum
import uuid
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, ForeignKey, Integer, Boolean, JSON, 
    ARRAY, UniqueConstraint, TypeDecorator, DateTime, func, 
    Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base import Base, TimestampMixin


class JSONArray(TypeDecorator):
    """Portable Array type for PostgreSQL/SQLite"""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON)


class DomainType(str, enum.Enum):
    """Domain classification as per Canon"""
    BUSINESS = "business"  # HR, Sales, Finance
    OFFERING = "offering"  # New Generic Type
    PRODUCT = "product"    # Legacy - Jewelry, Fashion, EV


# Offering Status defined in offering.py


class AttributeValueType(str, enum.Enum):
    """Primitive data types for attributes"""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class AttributeSemanticType(str, enum.Enum):
    """Semantic meaning for AI reasoning"""
    PHYSICAL = "physical"
    FINANCIAL = "financial"
    CATEGORICAL = "categorical"
    IDENTIFIER = "identifier"


class AttributeScope(str, enum.Enum):
    """Owner level of the attribute"""
    OFFERING = "offering"
    VARIANT = "variant"


class PriceType(str, enum.Enum):
    """Price type"""
    BASE = "base"
    PROMO = "promo"


class InventoryLocationType(str, enum.Enum):
    """Inventory location type"""
    WAREHOUSE = "warehouse"
    STORE = "store"


# --- ONTOLOGY LAYER (GLOBAL) ---

class KnowledgeDomain(Base, TimestampMixin):
    """
    Business or Product domains (Jewelry, HR, etc.) 
    GLOBAL: No tenant_id. Everyone shares the same domain definition.
    """
    __tablename__ = "knowledge_domain"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    domain_type = Column(String, nullable=False, default=DomainType.OFFERING)
    is_archived = Column(Boolean, nullable=False, default=False)
    flow_config = Column(JSON, nullable=True) # Template flow for the domain
    
    # Relationships
    bots = relationship("Bot", back_populates="domain_rel")
    attribute_definitions = relationship("DomainAttributeDefinition", back_populates="domain", cascade="all, delete-orphan")
    offerings = relationship("TenantOffering", back_populates="domain")


class DomainAttributeDefinition(Base, TimestampMixin):
    """
    The "Dictionary" of attributes for a domain.
    GLOBAL: No tenant_id, no bot_id.
    """
    __tablename__ = "domain_attribute_definition"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value_type = Column(String, nullable=False, default=AttributeValueType.TEXT)
    semantic_type = Column(String, nullable=True, default=AttributeSemanticType.CATEGORICAL)
    value_constraint = Column(JSON, nullable=True)  # {enum: [], range: [min, max], regex: ""}
    scope = Column(String, nullable=False, default=AttributeScope.OFFERING)
    
    # Relationships
    domain = relationship("KnowledgeDomain", back_populates="attribute_definitions")
    tenant_configs = relationship("TenantAttributeConfig", back_populates="definition", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('domain_id', 'key', name='uq_domain_attr_key'),
    )


# --- CUSTOMIZATION LAYER (TENANT) ---

class TenantAttributeConfig(Base, TimestampMixin):
    """
    Tenant-specific overrides for Global Attributes.
    UI/Business logic only, no semantic definition here.
    """
    __tablename__ = "tenant_attribute_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    attribute_def_id = Column(String, ForeignKey("domain_attribute_definition.id", ondelete="RESTRICT"), nullable=False)
    
    label = Column(String, nullable=True)  # e.g. "MSRP" instead of "price"
    is_display = Column(Boolean, nullable=False, default=True)
    is_searchable = Column(Boolean, nullable=False, default=False)
    is_required = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    ui_config = Column(JSON, nullable=True) # Tooltips, placeholders, CSS hints
    
    # Relationships
    tenant = relationship("Tenant")
    definition = relationship("DomainAttributeDefinition", back_populates="tenant_configs")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'attribute_def_id', name='uq_tenant_attr_config'),
    )


# --- CORE ENTITY LAYER (TENANT DATA) ---

# --- LEGACY MODELS REMOVED ---
# Consolidated into offering.py


# --- KNOWLEDGE BASE (FAQ, UseCase, Comparison) ---

class BotUseCase(Base, TimestampMixin):
    """Use case context for products (Bot-specific instance)"""
    __tablename__ = "bot_use_case"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=True)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="RESTRICT"), nullable=False)
    offering_id = Column(String, ForeignKey("tenant_offering.id", ondelete="SET NULL"), nullable=True)
    scenario = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="use_cases")
    domain = relationship("KnowledgeDomain")
    offering = relationship("TenantOffering", back_populates="use_cases")


class BotFAQ(Base, TimestampMixin):
    """FAQ model for knowledge base (Bot-specific instance)"""
    __tablename__ = "bot_faq"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=True)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="RESTRICT"), nullable=False)
    offering_id = Column(String, ForeignKey("tenant_offering.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="faqs")
    offering = relationship("TenantOffering", back_populates="faqs")
    domain = relationship("KnowledgeDomain")


class BotComparison(Base, TimestampMixin):
    """Product comparison model (Bot-specific instance)"""
    __tablename__ = "bot_comparison"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=True)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    offering_ids = Column(JSONArray, nullable=False)
    comparison_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    bot = relationship("Bot", back_populates="comparisons")
    domain = relationship("KnowledgeDomain")


# --- MIGRATION HUB ---

class MigrationSourceType(str, enum.Enum):
    """Migration source types"""
    WEB_SCRAPER = "web_scraper"
    EXCEL_UPLOAD = "excel_upload"
    SHOPIFY_SYNC = "shopify_sync"
    HARAVAN_SYNC = "haravan_sync"


class MigrationJobStatus(str, enum.Enum):
    """Migration job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    STAGED = "staged"
    COMPLETED = "completed"
    FAILED = "failed"


class MigrationJob(Base, TimestampMixin):
    """Job for bulk data migration/import"""
    __tablename__ = "migration_job"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=True)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="RESTRICT"), nullable=False)
    
    source_type = Column(String, nullable=False, default=MigrationSourceType.WEB_SCRAPER)
    status = Column(String, nullable=False, default=MigrationJobStatus.PENDING)
    
    batch_metadata = Column(JSON, nullable=True)  # URL, Filename, etc.
    raw_data = Column(JSON, nullable=True)        # Original data before AI parsing
    staged_data = Column(JSON, nullable=True)     # Standardized data for Preview
    error_log = Column(Text, nullable=True)
    
    # Relationships
    bot = relationship("Bot")
    domain = relationship("KnowledgeDomain")
