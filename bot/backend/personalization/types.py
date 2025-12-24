"""
Personalization Type Definitions
"""
from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class Tone(str, Enum):
    """Bot tone options"""
    FORMAL = "formal"           # Trang trọng
    FRIENDLY = "friendly"       # Thân thiện
    PROFESSIONAL = "professional"  # Chuyên nghiệp
    CASUAL = "casual"           # Thân mật
    HUMOROUS = "humorous"       # Hài hước


class Style(str, Enum):
    """Bot style options"""
    CONCISE = "concise"         # Ngắn gọn
    DETAILED = "detailed"       # Chi tiết
    CONVERSATIONAL = "conversational"  # Trò chuyện
    TECHNICAL = "technical"     # Kỹ thuật


@dataclass
class AvatarConfig:
    """Avatar configuration"""
    avatar_id: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_emoji: Optional[str] = None  # Fallback emoji
    custom_name: Optional[str] = None   # Custom bot name
    
    def __post_init__(self):
        """Validate avatar config"""
        if not any([self.avatar_id, self.avatar_url, self.avatar_emoji]):
            # Default avatar
            self.avatar_emoji = "🤖"


@dataclass
class APIPreferences:
    """Custom API preferences"""
    custom_endpoints: Dict[str, str] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    response_format: Literal["json", "xml", "text"] = "json"
    timeout_seconds: int = 30


@dataclass
class UserPreferences:
    """
    User personalization preferences
    
    This is stored per user, not per session.
    """
    user_id: str
    tone: Tone = Tone.FRIENDLY
    style: Style = Style.CONVERSATIONAL
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    api_preferences: APIPreferences = field(default_factory=APIPreferences)
    language: str = "vi"
    timezone: Optional[str] = None
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate preferences"""
        if not self.user_id:
            raise ValueError("user_id is required")
        if self.api_preferences.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

