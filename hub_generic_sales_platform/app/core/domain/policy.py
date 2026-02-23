from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ViolationAction(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    FALLBACK = "fallback"

class TenantGuardrail(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: str
    condition_expression: str
    violation_action: ViolationAction = ViolationAction.BLOCK
    fallback_message: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
