"""Tenant and Access models"""
import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import Base, TimestampMixin
from sqlalchemy.dialects.postgresql import UUID


class TenantStatus(str, enum.Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"


class TenantPlan(str, enum.Enum):
    """Tenant plan"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(Base, TimestampMixin):
    """Tenant model"""
    
    __tablename__ = "tenant"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default=TenantStatus.ACTIVE.value)
    plan = Column(String(20), nullable=False, default=TenantPlan.FREE.value)
    
    # Relationships
    user_accounts = relationship("UserAccount", back_populates="tenant", cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="tenant", cascade="all, delete-orphan")
    offerings = relationship("TenantOffering", back_populates="tenant", cascade="all, delete-orphan")
    price_lists = relationship("TenantPriceList", back_populates="tenant", cascade="all, delete-orphan")
    sales_channels = relationship("TenantSalesChannel", back_populates="tenant", cascade="all, delete-orphan")
    inventory_locations = relationship("TenantInventoryLocation", back_populates="tenant", cascade="all, delete-orphan")


class UserRole(str, enum.Enum):
    """User role"""
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    """User status"""
    ACTIVE = "active"
    DISABLED = "disabled"


class UserAccount(Base, TimestampMixin):
    """User account model"""
    
    __tablename__ = "user_account"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)  # Nullable for backward compatibility
    role = Column(String(20), nullable=False, default=UserRole.VIEWER)
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="user_accounts")
