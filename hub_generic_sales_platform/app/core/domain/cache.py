from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TenantSemanticCache(BaseModel):
    id: str
    tenant_id: str
    query_text: str
    response_text: str
    # embedding: Optional[List[float]] = None  # Optional based on search requirements
    hit_count: int = 0
    last_hit_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
