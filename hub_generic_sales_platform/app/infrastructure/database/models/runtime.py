"""Runtime State models"""

import enum
from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, DateTime, JSON, func
from sqlalchemy.orm import relationship
import uuid
from app.infrastructure.database.base import Base, TimestampMixin
from sqlalchemy.dialects.postgresql import UUID

# Import from domain layer (Single Source of Truth)
from app.core.domain.runtime import LifecycleState


class ChannelCode(str, enum.Enum):
    """Channel code"""
    WEBCHAT = "webchat"
    MESSENGER = "messenger"
    ZALO = "zalo"


class RuntimeSession(Base, TimestampMixin):
    """Conversation session model (Runtime scope)"""
    
    __tablename__ = "runtime_session"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=False)
    bot_version_id = Column(String, ForeignKey("bot_version.id", ondelete="SET NULL"), nullable=False)
    channel_code = Column(String, nullable=False)  # webchat, messenger, zalo, etc.
    lifecycle_state = Column(String, nullable=False, default=LifecycleState.IDLE.value)
    flow_context = Column(JSON, nullable=True) # State data for the current flow
    version = Column(Integer, nullable=False, default=0)
    ext_metadata = Column(JSON, nullable=True)  # extensible data (e.g., user_role, preferences)
    state_updated_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    turns = relationship("RuntimeTurn", back_populates="session", cascade="all, delete-orphan")
    context_slots = relationship("RuntimeContextSlot", back_populates="session", cascade="all, delete-orphan")
    decision_events = relationship("RuntimeDecisionEvent", back_populates="session")


class Speaker(str, enum.Enum):
    """Speaker type"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class RuntimeTurn(Base, TimestampMixin):
    """Conversation turn (message log) in Runtime"""
    
    __tablename__ = "runtime_turn"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("runtime_session.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String, nullable=False)  # user, bot, system
    message = Column(String, nullable=False)
    ui_metadata = Column(JSON, nullable=True)  # metadata for UI (G-UI components, images, links)
    
    # Relationships
    session = relationship("RuntimeSession", back_populates="turns")


class SlotStatus(str, enum.Enum):
    """Slot status"""
    ACTIVE = "active"
    OVERRIDDEN = "overridden"
    CONFLICT = "conflict"
    INFERRED = "inferred"


class SlotSource(str, enum.Enum):
    """Slot source"""
    USER = "user"
    SYSTEM = "system"
    INFERRED = "inferred"


class RuntimeContextSlot(Base, TimestampMixin):
    """Context data extracted during session runtime"""
    
    __tablename__ = "runtime_context_slot"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("runtime_session.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    status = Column(String, nullable=False, default=SlotStatus.ACTIVE)
    source = Column(String, nullable=False, default=SlotSource.USER)
    source_turn_id = Column(String, ForeignKey("runtime_turn.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    session = relationship("RuntimeSession", back_populates="context_slots")
    source_turn = relationship("RuntimeTurn")
