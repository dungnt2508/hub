"""
Router Type Definitions
"""
from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class RouterRequest:
    """Router input request"""
    raw_message: str
    user_id: str
    tenant_id: str  # Task 7: Add tenant_id for multi-tenancy
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Personalization context (optional, loaded from service)
    preferences_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request"""
        if not self.raw_message or not self.raw_message.strip():
            raise ValueError("raw_message is required and non-empty")
        if len(self.raw_message) > 5000:
            raise ValueError("raw_message exceeds 5000 characters")
        if not self._is_valid_uuid(self.user_id):
            raise ValueError("user_id must be valid UUID")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id is required and non-empty")
        if not self._is_valid_uuid(self.tenant_id):
            raise ValueError("tenant_id must be valid UUID")
        if self.session_id and not self._is_valid_uuid(self.session_id):
            raise ValueError("session_id must be valid UUID if provided")

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Check if string is valid UUID"""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False


@dataclass
class NormalizedInput:
    """Normalized input after STEP 0.5"""
    normalized_message: str
    normalized_entities: Dict[str, Any] = field(default_factory=dict)
    language: str = "vi"
    noise_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"

    def __post_init__(self):
        """Validate normalized input"""
        if not self.normalized_message:
            raise ValueError("normalized_message is required")


@dataclass
class RouterTrace:
    """Trace information for audit"""
    trace_id: str
    spans: list[Dict[str, Any]] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_span(
        self,
        step: str,
        input_data: Any,
        output_data: Any,
        duration_ms: int,
        score: Optional[float] = None,
        decision_source: Optional[str] = None
    ):
        """Add span to trace with full audit information"""
        span = {
            "step": step,
            "input": input_data,  # Keep full input for audit
            "output": output_data,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if score is not None:
            span["score"] = score
        if decision_source:
            span["decision_source"] = decision_source
        self.spans.append(span)


@dataclass
class RouterResponse:
    """Router output response"""
    trace_id: str
    domain: Optional[str] = None
    intent: Optional[str] = None
    intent_type: Optional[Literal["OPERATION", "KNOWLEDGE"]] = None
    slots: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None
    source: Literal["META", "PATTERN", "EMBEDDING", "LLM", "UNKNOWN"] = "UNKNOWN"
    message: Optional[str] = None
    status: Literal["ROUTED", "META_HANDLED", "UNKNOWN"] = "UNKNOWN"
    trace: Optional[RouterTrace] = None

    def __post_init__(self):
        """Validate response"""
        if self.status == "ROUTED":
            if not self.domain:
                raise ValueError("domain is required when status is ROUTED")
            if not self.intent:
                raise ValueError("intent is required when status is ROUTED")
            if self.confidence is None and self.source != "PATTERN":
                raise ValueError("confidence is required for non-PATTERN sources")

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError("confidence must be between 0.0 and 1.0")
