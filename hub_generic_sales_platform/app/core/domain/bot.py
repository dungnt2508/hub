from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.core.domain.knowledge import KnowledgeDomain

class BotStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class SystemCapability(BaseModel):
    id: str
    domain_id: Optional[str] = None
    code: str
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class Bot(BaseModel):
    id: str
    tenant_id: str
    domain_id: Optional[str] = None
    code: str
    name: str
    status: BotStatus = BotStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships & Properties (populated by repo)
    versions_count: int = 0
    capabilities: List[str] = []
    domain: Optional[KnowledgeDomain] = None
    
    class Config:
        from_attributes = True

class BotVersion(BaseModel):
    id: str
    bot_id: str
    version: int
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships
    capabilities: List[SystemCapability] = []

    class Config:
        from_attributes = True

class BotChannelConfig(BaseModel):
    id: str
    bot_version_id: str
    channel_code: str
    config: Optional[dict] = None
    is_active: bool = True

    class Config:
        from_attributes = True
