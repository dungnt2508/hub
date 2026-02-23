"""Bot Identity models"""

import enum
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, UniqueConstraint, func, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
from app.infrastructure.database.base import Base, TimestampMixin


class BotStatus(str, enum.Enum):
    """Bot status"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class Bot(Base, TimestampMixin):
    """Bot model"""
    
    __tablename__ = "bot"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=BotStatus.ACTIVE)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="bots")
    domain_rel = relationship("KnowledgeDomain", back_populates="bots")
    versions = relationship("BotVersion", back_populates="bot", cascade="all, delete-orphan")
    offerings = relationship("TenantOffering", back_populates="bot", cascade="all, delete-orphan")
    faqs = relationship("BotFAQ", back_populates="bot", cascade="all, delete-orphan")
    comparisons = relationship("BotComparison", back_populates="bot", cascade="all, delete-orphan")
    use_cases = relationship("BotUseCase", back_populates="bot", cascade="all, delete-orphan")
    
    @hybrid_property
    def versions_count(self):
        # Prevent lazy loading error during Pydantic validation/mapping
        if 'versions' not in self.__dict__:
            return 0
        return len(self.versions)

    @versions_count.expression
    def versions_count(cls):
        return (
            select(func.count(BotVersion.id))
            .where(BotVersion.bot_id == cls.id)
            .label("versions_count")
        )
    
    @property
    def domain(self):
        """Safe access to domain relationship"""
        try:
            return self.domain_rel
        except Exception:
            return None

    @property
    def capabilities(self):
        """Get capabilities of the currently active version (list of codes)"""
        try:
            # Check if versions are loaded
            if not self.versions:
                return []
            active_version = next((v for v in self.versions if v.is_active), None)
            if active_version:
                # Try to access capabilities on the version
                return [c.code for c in active_version.capabilities_rel]
        except Exception:
            pass
        return []
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_bot_tenant_code'),
    )


class BotVersion(Base, TimestampMixin):
    """Bot version model"""
    
    __tablename__ = "bot_version"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bot.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    flow_config = Column(JSON, nullable=True) # Overrides domain flow
    
    # Relationships
    bot = relationship("Bot", back_populates="versions")
    capabilities_rel = relationship("SystemCapability", secondary="bot_capability", back_populates="bot_versions")
    channel_configs = relationship("BotChannelConfig", back_populates="bot_version", cascade="all, delete-orphan")
    
    @property
    def capabilities(self):
        """Safe access to capabilities relationship (list of objects)"""
        try:
            return self.capabilities_rel
        except Exception:
            return []
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('bot_id', 'version', name='uq_bot_version'),
    )


class SystemCapability(Base, TimestampMixin):
    """Global capability blueprint list"""
    
    __tablename__ = "system_capability"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain_id = Column(String, ForeignKey("knowledge_domain.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False, unique=True)  # search, recommend, automate, crawl
    name = Column(String, nullable=True) # Human readable name
    description = Column(String, nullable=True)
    
    # Relationships
    domain = relationship("KnowledgeDomain")
    bot_versions = relationship("BotVersion", secondary="bot_capability", back_populates="capabilities_rel")


class BotCapability(Base, TimestampMixin):
    """The assignment of a SystemCapability to a specific BotVersion"""
    
    __tablename__ = "bot_capability"
    
    bot_version_id = Column(String, ForeignKey("bot_version.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    capability_id = Column(String, ForeignKey("system_capability.id", ondelete="CASCADE"), nullable=False, primary_key=True)


class BotChannelConfig(Base, TimestampMixin):
    """Configuration for specific chat channels (Bot instance scope)"""
    
    __tablename__ = "bot_channel_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_version_id = Column(String, ForeignKey("bot_version.id", ondelete="CASCADE"), nullable=False)
    channel_code = Column(String, nullable=False)  # webchat, messenger, zalo, etc.
    config = Column(JSON, nullable=True)  # channel-specific settings
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    bot_version = relationship("BotVersion", back_populates="channel_configs")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('bot_version_id', 'channel_code', name='uq_channel_config'),
    )
