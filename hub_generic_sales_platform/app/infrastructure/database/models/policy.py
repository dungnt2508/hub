"""Policy models"""

import enum
from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, JSON, UniqueConstraint
import uuid
from app.infrastructure.database.base import Base, TimestampMixin


class ViolationAction(str, enum.Enum):
    """Violation action"""
    BLOCK = "block"
    WARN = "warn"
    FALLBACK = "fallback"


class TenantGuardrail(Base, TimestampMixin):
    """Guardrail policies (Tenant scope)"""
    
    __tablename__ = "tenant_guardrail"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    condition_expression = Column(Text, nullable=False)  # when to trigger
    violation_action = Column(String, nullable=False, default=ViolationAction.BLOCK)
    fallback_message = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_guardrail_tenant_code'),
    )

