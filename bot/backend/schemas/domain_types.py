"""
Domain Engine Type Definitions
"""
from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class DomainResult(str, Enum):
    """Domain result status"""
    SUCCESS = "SUCCESS"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    REJECT_POLICY = "REJECT_POLICY"
    REJECT_PERMISSION = "REJECT_PERMISSION"
    INVALID_REQUEST = "INVALID_REQUEST"
    ERROR = "ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class DomainRequest:
    """Domain engine input request"""
    domain: str
    intent: str
    intent_type: Literal["OPERATION", "KNOWLEDGE"]
    slots: Dict[str, Any]
    user_context: Dict[str, Any]
    trace_id: str

    def __post_init__(self):
        """Validate domain request"""
        if not self.domain:
            raise ValueError("domain is required")
        if not self.intent:
            raise ValueError("intent is required")
        if not self.user_context.get("user_id"):
            raise ValueError("user_context.user_id is required")
        if not self.trace_id:
            raise ValueError("trace_id is required")


@dataclass
class DomainResponse:
    """Domain engine output response"""
    status: DomainResult
    data: Optional[Dict[str, Any]] = None
    missing_slots: Optional[list[str]] = None
    message: Optional[str] = None
    audit: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    next_action: Optional[Literal["ASK_SLOT", "CONFIRM", "CONTINUE", "END"]] = None
    next_action_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate domain response"""
        if self.status == DomainResult.SUCCESS and not self.data:
            raise ValueError("data is required when status is SUCCESS")
        if self.status == DomainResult.NEED_MORE_INFO and not self.missing_slots:
            raise ValueError("missing_slots is required when status is NEED_MORE_INFO")
        # Auto-set next_action based on status if not provided
        if self.next_action is None:
            if self.status == DomainResult.NEED_MORE_INFO:
                self.next_action = "ASK_SLOT"
            elif self.status == DomainResult.SUCCESS:
                self.next_action = "END"
            elif self.status in [DomainResult.REJECT_POLICY, DomainResult.REJECT_PERMISSION]:
                self.next_action = "END"
            else:
                self.next_action = "END"

