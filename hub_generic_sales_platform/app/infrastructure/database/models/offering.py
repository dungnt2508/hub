"""Offering models - The Core Abstraction for a Generic Sales Platform"""

import enum
import uuid
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, ForeignKey, Integer, Boolean, JSON, 
    ARRAY, UniqueConstraint, TypeDecorator, DateTime, func, 
    Numeric, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base import Base, TimestampMixin


class OfferingType(str, enum.Enum):
    """Categorization of what is being offered"""
    PHYSICAL = "physical"   # Traditional products (Retail)
    SERVICE = "service"     # Appointments, Consultations, Training
    DIGITAL = "digital"     # Licenses, Downloads, E-books
    FINANCIAL = "financial" # Loans, Stocks, Insurance, Crypto
    ASSET = "asset"         # Real Estate, Vehicles (High-ticket)


class OfferingStatus(str, enum.Enum):
    """Lifecycle status of an offering"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class TenantOffering(Base, TimestampMixin):
    """
    The Base Entity for everything the system can "sell" or "convert".
    Replaces TenantProduct in the generic architecture.
    """
    __tablename__ = "tenant_offering"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="SET NULL"), nullable=True)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="RESTRICT"), nullable=False)
    
    # Core Identity
    type = Column(String, nullable=False, default=OfferingType.PHYSICAL)
    code = Column(String, nullable=False) # Internal unique code/identifier
    identity_key = Column(String, nullable=True) # External ID: SKU, Ticker, ISIN, etc.
    
    status = Column(String, nullable=False, default=OfferingStatus.ACTIVE)
    is_archived = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    ext_metadata = Column(JSON, nullable=True) # Industry-specific fixed data
    
    # Relationships
    tenant = relationship("Tenant", back_populates="offerings")
    domain = relationship("KnowledgeDomain", back_populates="offerings")
    bot = relationship("Bot", back_populates="offerings")
    
    versions = relationship("TenantOfferingVersion", back_populates="offering", cascade="all, delete-orphan")
    variants = relationship("TenantOfferingVariant", back_populates="offering", cascade="all, delete-orphan")
    use_cases = relationship("BotUseCase", back_populates="offering")
    faqs = relationship("BotFAQ", back_populates="offering")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_offering_tenant_code'),
        Index('idx_offering_tenant_type', 'tenant_id', 'type'),
    )


class TenantOfferingVersion(Base, TimestampMixin):
    """Specific content version for an offering (Tenant scope instance)"""
    __tablename__ = "tenant_offering_version"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    offering_id = Column(String, ForeignKey("tenant_offering.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=OfferingStatus.ACTIVE)
    embedding = Column(Vector(1536), nullable=True)
    
    # Relationships
    offering = relationship("TenantOffering", back_populates="versions")
    attribute_values = relationship("TenantOfferingAttributeValue", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('offering_id', 'version', name='uq_offering_version'),
    )


class TenantOfferingAttributeValue(Base, TimestampMixin):
    """Actual attribute data for an offering version (Tenant scope instance)"""
    __tablename__ = "tenant_offering_attribute_value"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    offering_version_id = Column(String, ForeignKey("tenant_offering_version.id", ondelete="CASCADE"), nullable=False)
    attribute_def_id = Column(String, ForeignKey("domain_attribute_definition.id", ondelete="CASCADE"), nullable=False)
    
    value_text = Column(Text, nullable=True)
    value_number = Column(Numeric, nullable=True)
    value_bool = Column(Boolean, nullable=True)
    value_json = Column(JSON, nullable=True)
    
    # Relationships
    version = relationship("TenantOfferingVersion", back_populates="attribute_values")
    definition = relationship("DomainAttributeDefinition")
    
    __table_args__ = (
        UniqueConstraint('offering_version_id', 'attribute_def_id', name='uq_offering_version_attr_val'),
    )


class TenantOfferingVariant(Base, TimestampMixin):
    """SKU/Variant for an offering (Tenant scope instance)"""
    __tablename__ = "tenant_offering_variant"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    offering_id = Column(String, ForeignKey("tenant_offering.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=OfferingStatus.ACTIVE)
    
    # Relationships
    offering = relationship("TenantOffering", back_populates="variants")
    tenant = relationship("Tenant")
    prices = relationship("TenantVariantPrice", back_populates="variant", cascade="all, delete-orphan")
    inventory_items = relationship("TenantInventoryItem", back_populates="variant", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'sku', name='uq_offering_variant_tenant_sku'),
    )


class TenantSalesChannel(Base, TimestampMixin):
    """Refactored sales channel model (Tenant scope instance)"""
    __tablename__ = "tenant_sales_channel"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    tenant = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_tenant_sales_channel_code'),
    )


class TenantPriceList(Base, TimestampMixin):
    """Price list configuration (Tenant scope instance)"""
    __tablename__ = "tenant_price_list"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(String, ForeignKey("tenant_sales_channel.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    channel = relationship("TenantSalesChannel")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_tenant_price_list_code'),
        CheckConstraint('valid_to IS NULL OR valid_from < valid_to', name='check_price_list_time'),
    )

class TenantVariantPrice(Base, TimestampMixin):
    """Specific price for a variant (Tenant scope instance)"""
    __tablename__ = "tenant_variant_price"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    price_list_id = Column(String, ForeignKey("tenant_price_list.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(String, ForeignKey("tenant_offering_variant.id", ondelete="CASCADE"), nullable=False)
    currency = Column(String(3), nullable=False, default="VND")
    amount = Column(Numeric(18, 2), nullable=False)
    compare_at = Column(Numeric(18, 2), nullable=True)
    
    # Relationships
    variant = relationship("TenantOfferingVariant", back_populates="prices")
    
    __table_args__ = (
        UniqueConstraint('price_list_id', 'variant_id', name='uq_offering_variant_price_list_item'),
    )


class TenantInventoryLocation(Base, TimestampMixin):
    """Inventory location (Tenant scope instance)"""
    __tablename__ = "tenant_inventory_location"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=True)
    type = Column(String, nullable=False, server_default="warehouse")
    
    # Relationships
    tenant = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_tenant_inv_location_code'),
    )


class TenantInventoryItem(Base, TimestampMixin):
    """Stock tracking for an offering variant at a location (Tenant scope instance)"""
    __tablename__ = "tenant_inventory_item"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(String, ForeignKey("tenant_offering_variant.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(String, ForeignKey("tenant_inventory_location.id", ondelete="CASCADE"), nullable=False)
    stock_qty = Column(Integer, nullable=False, default=0)
    safety_stock = Column(Integer, nullable=False, default=0)
    
    # Relationships
    variant = relationship("TenantOfferingVariant", back_populates="inventory_items")
    location = relationship("TenantInventoryLocation")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'variant_id', 'location_id', name='uq_offering_inventory_item_unique'),
        CheckConstraint('stock_qty >= 0', name='check_offering_inventory_item_qty'),
    )
