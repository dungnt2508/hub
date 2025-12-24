"""
Example: Personalization Usage
"""
import asyncio
import uuid
from backend.interface import APIHandler
from backend.personalization import PersonalizationService, Tone, Style, AvatarConfig


async def main():
    """Example usage of personalization"""
    user_id = str(uuid.uuid4())
    
    # Initialize services
    personalization_service = PersonalizationService()
    api_handler = APIHandler()
    
    # 1. Set user preferences
    print("=== Setting User Preferences ===")
    preferences = await personalization_service.update_preferences(
        user_id=user_id,
        tone=Tone.FRIENDLY,
        style=Style.CONVERSATIONAL,
        avatar={
            "avatar_emoji": "😊",
            "custom_name": "Trợ lý ảo",
        }
    )
    print(f"Tone: {preferences.tone.value}")
    print(f"Style: {preferences.style.value}")
    print(f"Avatar: {preferences.avatar.avatar_emoji}")
    print()
    
    # 2. Make request with personalization
    print("=== Making Request with Personalization ===")
    response = await api_handler.handle_request(
        raw_message="Tôi còn bao nhiêu ngày phép?",
        user_id=user_id,
    )
    
    print(f"Message: {response.get('message')}")
    print(f"Avatar: {response.get('avatar')}")
    print(f"Tone: {response.get('metadata', {}).get('tone')}")
    print()
    
    # 3. Change tone to formal
    print("=== Changing Tone to Formal ===")
    preferences = await personalization_service.update_preferences(
        user_id=user_id,
        tone=Tone.FORMAL,
    )
    
    response = await api_handler.handle_request(
        raw_message="Tôi còn bao nhiêu ngày phép?",
        user_id=user_id,
    )
    
    print(f"Message (formal): {response.get('message')}")
    print(f"Tone: {response.get('metadata', {}).get('tone')}")


if __name__ == "__main__":
    asyncio.run(main())

