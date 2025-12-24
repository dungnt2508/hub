"""
Multi-tenant authentication types and schemas.
Định nghĩa các kiểu dữ liệu cho multi-tenant bot service.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime


class AuthMethod(str, Enum):
    """Authentication methods supported by bot service"""
    JWT_WEB_EMBED = "jwt_web_embed"
    TELEGRAM_BOT = "telegram_bot"
    TEAMS_BOT = "teams_bot"
    API_KEY = "api_key"


class ChannelType(str, Enum):
    """Supported communication channels"""
    WEB = "web"
    TELEGRAM = "telegram"
    TEAMS = "teams"
    API = "api"


class PlanType(str, Enum):
    """Service plans for rate limiting"""
    BASIC = "basic"           # 1000/hour
    PROFESSIONAL = "professional"  # 5000/hour
    ENTERPRISE = "enterprise"      # unlimited


# ============================================================================
# WEB EMBED FLOW
# ============================================================================

@dataclass
class EmbedInitRequest:
    """Request to initialize web embed session"""
    site_id: str
    platform: str = "web"
    user_data: Optional[Dict[str, str]] = None  # {email, external_id}
    
    def validate(self) -> bool:
        """Validate request"""
        if not self.site_id or not self.site_id.strip():
            raise ValueError("site_id is required")
        return True


@dataclass
class EmbedInitResponse:
    """Response from embed initialization"""
    token: str              # JWT token
    expires_in: int        # Seconds
    bot_config: Dict[str, Any]  # {name, avatar, theme, etc}


@dataclass
class BotMessageRequest:
    """Chat message to bot"""
    message: str
    session_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


@dataclass
class BotMessageResponse:
    """Response from bot"""
    message_id: str
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    follow_up_actions: Optional[List[str]] = None


# ============================================================================
# JWT TOKEN
# ============================================================================

@dataclass
class JWTPayload:
    """JWT token payload for web embed"""
    tenant_id: str
    channel: str
    user_key: str          # hash(session_id) or random, NOT from user input
    origin: str           # bind to this origin
    iat: int             # issued at
    exp: int             # expiration
    auth_method: str = AuthMethod.JWT_WEB_EMBED


# ============================================================================
# IDENTITY & CONTEXT
# ============================================================================

@dataclass
class UserKey:
    """Technical user identity (non-PII)"""
    id: str = None
    tenant_id: str = None
    channel: str = None
    user_key: str = None         # hash(session_id) | telegram_user_id | aadObjectId
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


@dataclass
class RequestContext:
    """Resolved request context from authentication"""
    tenant_id: str
    channel: str
    user_key: str
    auth_method: str
    
    # Optional identity details
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    
    # Request metadata
    platform: str = "api"
    ip: Optional[str] = None
    origin: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "channel": self.channel,
            "user_key": self.user_key,
            "auth_method": self.auth_method,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "platform": self.platform,
            "ip": self.ip,
            "origin": self.origin,
        }


# ============================================================================
# TENANT CONFIGURATION
# ============================================================================

@dataclass
class TenantConfig:
    """Tenant configuration"""
    id: str
    name: str
    api_key: str
    webhook_secret: Optional[str] = None
    plan: str = PlanType.BASIC
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # Web Embed Configuration
    web_embed_enabled: bool = True
    web_embed_origins: List[str] = None  # allowed origins
    web_embed_jwt_secret: str = None
    web_embed_token_expiry_seconds: int = 300  # 5 minutes
    
    # Telegram Configuration
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None  # encrypted
    
    # Teams Configuration
    teams_enabled: bool = False
    teams_app_id: Optional[str] = None
    teams_app_password: Optional[str] = None  # encrypted
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate tenant config"""
        if not self.id or not self.name or not self.api_key:
            raise ValueError("id, name, api_key are required")
        if self.plan not in [p.value for p in PlanType]:
            raise ValueError(f"Invalid plan: {self.plan}")
        return True


# ============================================================================
# CONVERSATION
# ============================================================================

@dataclass
class ConversationMessage:
    """Single message in conversation"""
    id: str = None
    conversation_id: str = None
    role: str = "user"  # 'user', 'assistant'
    content: str = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class Conversation:
    """Conversation session"""
    id: str = None
    tenant_id: str = None
    channel: str = None
    user_key: str = None
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    context_data: Optional[Dict[str, Any]] = None
    messages: List[ConversationMessage] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def add_message(self, role: str, content: str, 
                   intent: str = None, confidence: float = None):
        """Add message to conversation"""
        if self.messages is None:
            self.messages = []
        
        msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=self.id,
            role=role,
            content=content,
            intent=intent,
            confidence=confidence,
            created_at=datetime.now()
        )
        self.messages.append(msg)
        self.message_count += 1
        self.last_message_at = datetime.now()
        return msg


# ============================================================================
# RATE LIMITING
# ============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration per plan"""
    plan: str
    per_minute: int
    per_hour: int
    per_day: int


RATE_LIMIT_CONFIGS = {
    PlanType.BASIC: RateLimitConfig(
        plan=PlanType.BASIC,
        per_minute=20,
        per_hour=1000,
        per_day=10000,
    ),
    PlanType.PROFESSIONAL: RateLimitConfig(
        plan=PlanType.PROFESSIONAL,
        per_minute=100,
        per_hour=5000,
        per_day=50000,
    ),
    PlanType.ENTERPRISE: RateLimitConfig(
        plan=PlanType.ENTERPRISE,
        per_minute=1000,
        per_hour=100000,
        per_day=1000000,
    ),
}


# ============================================================================
# WEBHOOK VERIFICATION
# ============================================================================

@dataclass
class TelegramUpdate:
    """Telegram webhook update"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    edited_message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


@dataclass
class TeamsMessage:
    """Teams Bot Framework message"""
    type: str  # 'message', 'endOfConversation', etc
    id: str
    timestamp: str
    conversation: Dict[str, Any]
    from_user: Dict[str, Any]  # 'from' is reserved keyword
    text: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# ERROR RESPONSES
# ============================================================================

@dataclass
class ErrorResponse:
    """Standard error response"""
    error: bool = True
    message: str = None
    code: str = None
    status_code: int = 400
    details: Optional[Dict[str, Any]] = None

