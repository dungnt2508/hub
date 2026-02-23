"""Cache entities for Tier 2 performance"""

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer, JSON, DateTime, func
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base import Base, TimestampMixin


class TenantSemanticCache(Base, TimestampMixin):
    """Semantic Cache (Tenant scope)"""
    
    __tablename__ = "tenant_semantic_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # Vector embedding for semantic matching
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)
