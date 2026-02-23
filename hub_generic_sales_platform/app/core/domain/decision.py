from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal

class DecisionType(str, Enum):
    ASK_CLARIFY = "ASK_CLARIFY"
    PROCEED = "PROCEED"
    GUARDRAIL_BLOCK = "GUARDRAIL_BLOCK"
    FALLBACK = "FALLBACK"
    RESOLVE_CONFLICT = "RESOLVE_CONFLICT"
    TRANSITION_STATE = "TRANSITION_STATE"
    REQUEST_REFERENCE_CLARIFICATION = "REQUEST_REFERENCE_CLARIFICATION"
    INVALID_STATE_FOR_ACTION = "INVALID_STATE_FOR_ACTION"

class ActionExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class RuntimeDecisionEvent(BaseModel):
    id: str
    session_id: str
    input_turn_id: Optional[str] = None
    bot_version_id: str
    tier_code: Optional[str] = None
    decision_type: str
    decision_reason: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    token_usage: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RuntimeGuardrailCheck(BaseModel):
    id: str
    decision_id: str
    guardrail_id: str
    passed: bool
    violation_message: Optional[str] = None

    class Config:
        from_attributes = True

class RuntimeActionExecution(BaseModel):
    id: str
    decision_id: str
    action_type: str
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    status: ActionExecutionStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
