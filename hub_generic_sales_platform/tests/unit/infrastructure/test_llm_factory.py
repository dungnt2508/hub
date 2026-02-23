"""Unit tests for LLM Provider Factory"""

import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.llm.factory import LLMProviderFactory, get_llm_provider
from app.core.interfaces.llm_provider import ILLMProvider


@pytest.mark.unit
def test_factory_returns_openai_provider():
    """Test factory returns OpenAI provider for 'openai' config"""
    
    with patch("app.infrastructure.llm.factory.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider_primary = "openai"
        
        LLMProviderFactory._providers = {}  # Reset cache
        provider = LLMProviderFactory.get_provider()
        
        assert provider is not None
        assert isinstance(provider, ILLMProvider)


@pytest.mark.unit
def test_factory_returns_litellm_provider():
    """Test factory returns LiteLLM provider for 'litellm' config"""
    
    with patch("app.infrastructure.llm.factory.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider_primary = "litellm"
        
        LLMProviderFactory._providers = {}
        provider = LLMProviderFactory.get_provider()
        
        assert provider is not None
        assert isinstance(provider, ILLMProvider)


@pytest.mark.unit
def test_factory_caches_providers():
    """Test that factory caches provider instances"""
    
    with patch("app.infrastructure.llm.factory.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider_primary = "openai"
        
        LLMProviderFactory._providers = {}
        
        provider1 = LLMProviderFactory.get_provider("openai")
        provider2 = LLMProviderFactory.get_provider("openai")
        
        # Should return same instance
        assert provider1 is provider2


@pytest.mark.unit
def test_get_llm_provider_helper():
    """Test helper function get_llm_provider"""
    
    with patch("app.infrastructure.llm.factory.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider_primary = "openai"
        
        LLMProviderFactory._providers = {}
        provider = get_llm_provider()
        
        assert provider is not None
        assert isinstance(provider, ILLMProvider)


@pytest.mark.unit
def test_factory_fallback_for_unknown_provider():
    """Test factory gracefully handles unknown provider by falling back to OpenAI"""
    
    with patch("app.infrastructure.llm.factory.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider_primary = "unknown_provider"
        
        LLMProviderFactory._providers = {}
        provider = LLMProviderFactory.get_provider()
        
        # Should still return a provider (OpenAI fallback)
        assert provider is not None
