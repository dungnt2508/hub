"""Decision and Event models"""

import enum
from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, JSON, Text, Numeric, DateTime, func
from sqlalchemy.orm import relationship
import uuid
from app.infrastructure.database.base import Base, TimestampMixin


class DecisionType(str, enum.Enum):
    """Decision types for the bot"""
    ASK_CLARIFY = "ASK_CLARIFY"
    PROCEED = "PROCEED"
    GUARDRAIL_BLOCK = "GUARDRAIL_BLOCK"
    FALLBACK = "FALLBACK"
    
    # Keeping these for internal logic compatibility if needed by the orchestrator
    RESOLVE_CONFLICT = "RESOLVE_CONFLICT"
    TRANSITION_STATE = "TRANSITION_STATE"
    REQUEST_REFERENCE_CLARIFICATION = "REQUEST_REFERENCE_CLARIFICATION"
    INVALID_STATE_FOR_ACTION = "INVALID_STATE_FOR_ACTION"


class RuntimeDecisionEvent(Base, TimestampMixin):
    """
    Model for bot decisions in Runtime. Append-only for audit and observability.
    """

    __tablename__ = "runtime_decision_event"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("runtime_session.id", ondelete="CASCADE"), nullable=False)
    input_turn_id = Column(String, ForeignKey("runtime_turn.id", ondelete="SET NULL"), nullable=True)
    bot_version_id = Column(String, ForeignKey("bot_version.id", ondelete="SET NULL"), nullable=False)
    tier_code = Column(String, nullable=True)  # fast_path, knowledge_path, agentic_path
    decision_type = Column(String, nullable=False)
    decision_reason = Column(Text, nullable=True)
    estimated_cost = Column(Numeric(10, 5), nullable=True) 
    token_usage = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    # Relationships
    session = relationship("RuntimeSession", back_populates="decision_events")
    guardrails_checked = relationship("RuntimeGuardrailCheck", back_populates="decision", cascade="all, delete-orphan")
    action_executions = relationship("RuntimeActionExecution", back_populates="decision", cascade="all, delete-orphan")


class RuntimeGuardrailCheck(Base, TimestampMixin):
    """Log of guardrail checks for a decision in Runtime"""

    __tablename__ = "runtime_guardrail_check"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String, ForeignKey("runtime_decision_event.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    guardrail_id = Column(String, ForeignKey("tenant_guardrail.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    passed = Column(Boolean, nullable=False)
    violation_message = Column(Text, nullable=True)

    # Relationships
    decision = relationship("RuntimeDecisionEvent", back_populates="guardrails_checked")
    guardrail = relationship("TenantGuardrail")


class ActionExecutionStatus(str, enum.Enum):
    """Status of action execution"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RuntimeActionExecution(Base, TimestampMixin):
    """Execution log for actions triggered by decisions in Runtime"""
    
    __tablename__ = "runtime_action_execution"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String, ForeignKey("runtime_decision_event.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String, nullable=False)  # respond, call_api, trigger_tool
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    decision = relationship("RuntimeDecisionEvent", back_populates="action_executions")
