"""
Personalization Module

Handles user personalization features:
- Avatar customization
- Tone and style preferences
- Custom API settings
- Response formatting
"""

from .user_preferences import UserPreferences, PersonalizationService
from .response_formatter import ResponseFormatter
from .types import Tone, Style, AvatarConfig

__all__ = [
    "UserPreferences",
    "PersonalizationService",
    "ResponseFormatter",
    "Tone",
    "Style",
    "AvatarConfig",
]

