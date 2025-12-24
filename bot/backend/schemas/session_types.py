"""
Session Type Definitions
"""
from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionState:
    """Session state contract"""
    session_id: str
    user_id: str
    active_domain: Optional[str] = None
    last_domain: Optional[str] = None
    last_intent: Optional[str] = None
    last_intent_type: Optional[Literal["OPERATION", "KNOWLEDGE"]] = None
    pending_intent: Optional[str] = None
    missing_slots: list[str] = field(default_factory=list)
    slots_memory: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    escalation_flag: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate session state"""
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.user_id:
            raise ValueError("user_id is required")
        if self.retry_count < 0:
            raise ValueError("retry_count must be >= 0")

    def update_timestamp(self):
        """Update updated_at timestamp"""
        self.updated_at = datetime.utcnow()

    def merge_slots(self, new_slots: Dict[str, Any]):
        """Merge new slots into slots_memory"""
        self.slots_memory.update(new_slots)
        self.update_timestamp()

    def clear_slots(self):
        """Clear all slots from memory"""
        self.slots_memory.clear()
        self.missing_slots.clear()
        self.update_timestamp()

