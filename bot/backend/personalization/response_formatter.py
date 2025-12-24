"""
Response Formatter

Applies personalization to bot responses.
This runs in the Interface Layer, after domain/router processing.
"""
from typing import Dict, Any, Optional

from ..schemas import RouterResponse, DomainResponse, KnowledgeResponse
from .types import UserPreferences, Tone, Style
from .user_preferences import PersonalizationService
from ..shared.logger import logger


class ResponseFormatter:
    """
    Formats bot responses according to user preferences.
    
    This service:
    - Applies tone and style to messages
    - Adds avatar information
    - Formats response structure
    - Handles custom API preferences
    """
    
    def __init__(self, personalization_service: Optional[PersonalizationService] = None):
        """
        Initialize response formatter.
        
        Args:
            personalization_service: Personalization service (injected)
        """
        self.personalization_service = personalization_service or PersonalizationService()
    
    async def format_router_response(
        self,
        response: RouterResponse,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Format router response with personalization.
        
        Args:
            response: Router response
            user_id: User ID for preferences
            
        Returns:
            Formatted response dict
        """
        preferences = await self.personalization_service.get_preferences(user_id)
        
        # Format message
        formatted_message = self._format_message(
            response.message or "",
            preferences.tone,
            preferences.style
        )
        
        # Build response
        formatted = {
            "message": formatted_message,
            "domain": response.domain,
            "intent": response.intent,
            "status": response.status,
            "trace_id": response.trace_id,
            "avatar": {
                "emoji": preferences.avatar.avatar_emoji,
                "url": preferences.avatar.avatar_url,
                "name": preferences.avatar.custom_name or "Bot",
            },
            "metadata": {
                "tone": preferences.tone.value,
                "style": preferences.style.value,
            },
        }
        
        # Add confidence for KNOWLEDGE intents
        if response.intent_type == "KNOWLEDGE" and response.confidence is not None:
            formatted["confidence"] = response.confidence
        
        return formatted
    
    async def format_domain_response(
        self,
        response: DomainResponse,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Format domain response with personalization.
        
        Args:
            response: Domain response
            user_id: User ID for preferences
            
        Returns:
            Formatted response dict
        """
        preferences = await self.personalization_service.get_preferences(user_id)
        
        # Format message
        formatted_message = self._format_message(
            response.message or "",
            preferences.tone,
            preferences.style
        )
        
        return {
            "status": response.status.value,
            "message": formatted_message,
            "data": response.data,
            "avatar": {
                "emoji": preferences.avatar.avatar_emoji,
                "url": preferences.avatar.avatar_url,
                "name": preferences.avatar.custom_name or "Bot",
            },
        }
    
    async def format_knowledge_response(
        self,
        response: KnowledgeResponse,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Format knowledge response with personalization.
        
        Args:
            response: Knowledge response
            user_id: User ID for preferences
            
        Returns:
            Formatted response dict
        """
        preferences = await self.personalization_service.get_preferences(user_id)
        
        # Format answer
        formatted_answer = self._format_message(
            response.answer,
            preferences.tone,
            preferences.style
        )
        
        return {
            "answer": formatted_answer,
            "citations": response.citations,
            "confidence": response.confidence,
            "sources": [
                {
                    "title": source.title,
                    "url": source.url,
                    "page": source.page,
                }
                for source in (response.sources or [])
            ],
            "avatar": {
                "emoji": preferences.avatar.avatar_emoji,
                "url": preferences.avatar.avatar_url,
                "name": preferences.avatar.custom_name or "Bot",
            },
        }
    
    def _format_message(
        self,
        message: str,
        tone: Tone,
        style: Style
    ) -> str:
        """
        Format message according to tone and style.
        
        Args:
            message: Original message
            tone: Bot tone
            style: Bot style
            
        Returns:
            Formatted message
        """
        if not message:
            return message
        
        formatted = message
        
        # Apply tone transformations
        if tone == Tone.FORMAL:
            # Make more formal
            formatted = self._make_formal(formatted)
        elif tone == Tone.CASUAL:
            # Make more casual
            formatted = self._make_casual(formatted)
        elif tone == Tone.HUMOROUS:
            # Add humor (carefully)
            formatted = self._add_humor(formatted)
        
        # Apply style transformations
        if style == Style.CONCISE:
            formatted = self._make_concise(formatted)
        elif style == Style.DETAILED:
            formatted = self._make_detailed(formatted)
        
        return formatted
    
    def _make_formal(self, message: str) -> str:
        """Make message more formal"""
        # Replace casual phrases with formal ones
        replacements = {
            "bạn": "quý khách",
            "mình": "chúng tôi",
            "ok": "được",
            "okay": "được",
        }
        for casual, formal in replacements.items():
            message = message.replace(casual, formal)
        return message
    
    def _make_casual(self, message: str) -> str:
        """Make message more casual"""
        # Replace formal phrases with casual ones
        replacements = {
            "quý khách": "bạn",
            "chúng tôi": "mình",
        }
        for formal, casual in replacements.items():
            message = message.replace(formal, casual)
        return message
    
    def _add_humor(self, message: str) -> str:
        """Add humor to message (carefully)"""
        # Very conservative - only add emoji or light humor
        # Don't change meaning
        if "!" not in message:
            message = message.replace(".", "! 😊")
        return message
    
    def _make_concise(self, message: str) -> str:
        """Make message more concise"""
        # Remove filler words
        filler_words = ["thực sự", "thật sự", "rất", "cực kỳ"]
        words = message.split()
        filtered = [w for w in words if w not in filler_words]
        return " ".join(filtered)
    
    def _make_detailed(self, message: str) -> str:
        """Make message more detailed"""
        # Add more context (conservative)
        # For now, just return as-is
        # In production, could add explanations
        return message

