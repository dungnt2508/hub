"""
User Preferences Service

Manages user personalization preferences.
This is a cross-cutting concern, not domain-specific.
"""
from typing import Optional
from datetime import datetime

from .types import UserPreferences, Tone, Style, AvatarConfig, APIPreferences
from ..shared.exceptions import InvalidInputError
from ..shared.logger import logger


class PersonalizationService:
    """
    Service for managing user personalization preferences.
    
    This service:
    - Loads user preferences
    - Saves user preferences
    - Provides default preferences
    - Validates preferences
    """
    
    def __init__(self):
        """Initialize personalization service"""
        # TODO: Inject preferences repository
        self.preferences_repo = None
    
    async def get_preferences(self, user_id: str) -> UserPreferences:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            UserPreferences object (default if not found)
        """
        try:
            # TODO: Load from repository
            # preferences = await self.preferences_repo.get(user_id)
            # if preferences:
            #     return preferences
            
            # Return default preferences for now
            logger.debug(
                "Loading user preferences",
                extra={"user_id": user_id}
            )
            return self._get_default_preferences(user_id)
            
        except Exception as e:
            logger.error(
                f"Failed to load preferences: {e}",
                extra={"user_id": user_id},
                exc_info=True
            )
            # Return default on error
            return self._get_default_preferences(user_id)
    
    async def save_preferences(
        self,
        user_id: str,
        preferences: UserPreferences
    ) -> UserPreferences:
        """
        Save user preferences.
        
        Args:
            user_id: User ID
            preferences: User preferences to save
            
        Returns:
            Saved UserPreferences
            
        Raises:
            InvalidInputError: If preferences are invalid
        """
        # Validate
        if preferences.user_id != user_id:
            raise InvalidInputError("user_id mismatch")
        
        # Update timestamp
        preferences.updated_at = datetime.utcnow().isoformat()
        if not preferences.created_at:
            preferences.created_at = preferences.updated_at
        
        try:
            # TODO: Save to repository
            # await self.preferences_repo.save(preferences)
            
            logger.info(
                "Preferences saved",
                extra={
                    "user_id": user_id,
                    "tone": preferences.tone.value,
                    "style": preferences.style.value,
                }
            )
            return preferences
            
        except Exception as e:
            logger.error(
                f"Failed to save preferences: {e}",
                extra={"user_id": user_id},
                exc_info=True
            )
            raise
    
    async def update_preferences(
        self,
        user_id: str,
        **updates
    ) -> UserPreferences:
        """
        Update user preferences (partial update).
        
        Args:
            user_id: User ID
            **updates: Fields to update (tone, style, avatar, etc.)
            
        Returns:
            Updated UserPreferences
        """
        preferences = await self.get_preferences(user_id)
        
        # Update fields
        if "tone" in updates:
            preferences.tone = Tone(updates["tone"])
        if "style" in updates:
            preferences.style = Style(updates["style"])
        if "avatar" in updates:
            preferences.avatar = AvatarConfig(**updates["avatar"])
        if "api_preferences" in updates:
            preferences.api_preferences = APIPreferences(**updates["api_preferences"])
        if "language" in updates:
            preferences.language = updates["language"]
        if "timezone" in updates:
            preferences.timezone = updates["timezone"]
        
        return await self.save_preferences(user_id, preferences)
    
    def _get_default_preferences(self, user_id: str) -> UserPreferences:
        """Get default preferences for user"""
        return UserPreferences(
            user_id=user_id,
            tone=Tone.FRIENDLY,
            style=Style.CONVERSATIONAL,
            avatar=AvatarConfig(),
            api_preferences=APIPreferences(),
            language="vi",
        )

