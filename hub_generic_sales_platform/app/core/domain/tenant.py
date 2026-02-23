from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"

class TenantPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class Tenant(BaseModel):
    id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserAccount(BaseModel):
    id: str
    tenant_id: str
    email: str
    password_hash: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    tenant: Optional["Tenant"] = None

    class Config:
        from_attributes = True
