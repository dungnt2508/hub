from typing import Optional
from app.core.config.settings import get_settings
from app.core.interfaces.llm_provider import ILLMProvider
from app.infrastructure.llm.openai_provider import OpenAIProvider

class LLMProviderFactory:
    """
    Factory to create and cache LLM providers based on system settings.
    """
    _providers = {}

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> ILLMProvider:
        settings = get_settings()
        provider_name = name or settings.ai_provider_primary
        
        if provider_name not in cls._providers:
            if provider_name == "openai":
                cls._providers[provider_name] = OpenAIProvider(is_litellm=False)
            elif provider_name == "litellm":
                cls._providers[provider_name] = OpenAIProvider(is_litellm=True)
            # Add other providers here (e.g., gemini, anthropic)
            else:
                # Default fallback
                cls._providers[provider_name] = OpenAIProvider(is_litellm=False)
                
        return cls._providers[provider_name]

def get_llm_provider(name: Optional[str] = None) -> ILLMProvider:
    """Helper function to get the current LLM provider"""
    return LLMProviderFactory.get_provider(name)
