from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ChannelCode(str, Enum):
    WEBCHAT = "webchat"
    MESSENGER = "messenger"
    ZALO = "zalo"

class SlotKey(str, Enum):
    """Standardized slot keys for conversation context"""
    OFFERING_ID = "offering_id"
    OFFERING_CODE = "offering_code"
    PRODUCT_ID = "product_id"
    PRODUCT_CODE = "product_code"
    CUSTOMER_NAME = "customer_name"

class Intent(str, Enum):
    """Business Intents as defined in INTENT_USAGE_POLICY.md"""
    GREETING = "GREETING"
    SEARCH_PRODUCT = "SEARCH_PRODUCT"
    INQUIRY_PRICE = "INQUIRY_PRICE"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    PROVIDE_INFO = "PROVIDE_INFO"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"
    UNKNOWN = "UNKNOWN"

class LifecycleState(str, Enum):
    """
    Lifecycle states for conversation flow.
    
    This is the SINGLE SOURCE OF TRUTH for all lifecycle states.
    Infrastructure layer imports this enum to ensure consistency.
    """
    IDLE = "idle"
    BROWSING = "browsing"
    SEARCHING = "searching"
    VIEWING = "viewing"
    COMPARING = "comparing"
    FILTERING = "filtering"  # Added from infrastructure
    ANALYZING = "analyzing"
    PURCHASING = "purchasing"
    COMPLETED = "completed"  # Added from infrastructure
    CLOSED = "closed"
    HANDOVER = "handover"  # Human agent has taken over the conversation
    ERROR = "error"
    WAITING_INPUT = "waiting_input"

class Speaker(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"

class SlotStatus(str, Enum):
    ACTIVE = "active"
    OVERRIDDEN = "overridden"
    CONFLICT = "conflict"
    INFERRED = "inferred"

class SlotSource(str, Enum):
    USER = "user"
    SYSTEM = "system"
    INFERRED = "inferred"

class RuntimeSession(BaseModel):
    id: str
    tenant_id: str
    bot_id: str
    bot_version_id: str
    channel_code: str
    lifecycle_state: str = LifecycleState.IDLE.value
    ext_metadata: Optional[Dict[str, Any]] = None
    state_updated_at: Optional[datetime] = None
    version: int = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_handover_mode(self) -> bool:
        """Human agent đã tiếp quản hội thoại."""
        return (self.lifecycle_state or "").lower() == LifecycleState.HANDOVER.value

    def is_active(self) -> bool:
        """Session chưa kết thúc (chưa closed/completed)."""
        state = (self.lifecycle_state or "").lower()
        return state not in (LifecycleState.CLOSED.value, LifecycleState.COMPLETED.value)

    class Config:
        from_attributes = True

class RuntimeTurn(BaseModel):
    id: str
    session_id: str
    speaker: Speaker
    message: str
    ui_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RuntimeContextSlot(BaseModel):
    id: str
    session_id: str
    key: str
    value: str
    status: SlotStatus = SlotStatus.ACTIVE
    source: SlotSource = SlotSource.USER
    source_turn_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Slot còn hiệu lực (chưa bị overridden)."""
        return self.status == SlotStatus.ACTIVE

    class Config:
        from_attributes = True
