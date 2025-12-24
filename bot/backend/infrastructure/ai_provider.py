"""
AI Provider Abstraction - LiteLLM primary, OpenAI fallback
"""
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..shared.config import config
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError, RouterTimeoutError


class ProviderType(str, Enum):
    """AI Provider types"""
    LITELLM = "litellm"
    OPENAI = "openai"


class CircuitBreaker:
    """Simple circuit breaker for provider failures"""
    
    def __init__(self, failure_threshold: int, timeout: int):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "closed":
            return False
        elif self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = "half_open"
                    return False
            return True
        else:  # half_open
            return False


class AIProvider:
    """AI Provider with LiteLLM primary and OpenAI fallback"""
    
    def __init__(self):
        self.primary_provider = config.AI_PROVIDER_PRIMARY
        self.fallback_provider = config.AI_PROVIDER_FALLBACK
        self.primary_circuit_breaker = CircuitBreaker(
            config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            config.CIRCUIT_BREAKER_TIMEOUT
        )
        self.fallback_circuit_breaker = CircuitBreaker(
            config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            config.CIRCUIT_BREAKER_TIMEOUT
        )
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=config.LLM_TIMEOUT)
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def embed(self, text: str) -> List[float]:
        """
        Get embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            ExternalServiceError: If all providers fail
            RouterTimeoutError: If request times out
        """
        # Try primary provider
        if not self.primary_circuit_breaker.is_open():
            try:
                embedding = await self._embed_primary(text)
                self.primary_circuit_breaker.record_success()
                return embedding
            except Exception as e:
                logger.warning(f"Primary provider failed: {e}")
                self.primary_circuit_breaker.record_failure()
        
        # Try fallback provider
        if not self.fallback_circuit_breaker.is_open():
            try:
                embedding = await self._embed_fallback(text)
                self.fallback_circuit_breaker.record_success()
                return embedding
            except Exception as e:
                logger.warning(f"Fallback provider failed: {e}")
                self.fallback_circuit_breaker.record_failure()
        
        # All providers failed
        raise ExternalServiceError("All AI providers failed")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> str:
        """
        Chat completion.
        
        Args:
            messages: List of message dicts with "role" and "content"
            temperature: Temperature for generation
            
        Returns:
            Generated text
            
        Raises:
            ExternalServiceError: If all providers fail
            RouterTimeoutError: If request times out
        """
        temp = temperature or config.LLM_TEMPERATURE
        
        # Try primary provider
        if not self.primary_circuit_breaker.is_open():
            try:
                response = await self._chat_primary(messages, temp)
                self.primary_circuit_breaker.record_success()
                return response
            except Exception as e:
                logger.warning(f"Primary provider failed: {e}")
                self.primary_circuit_breaker.record_failure()
        
        # Try fallback provider
        if not self.fallback_circuit_breaker.is_open():
            try:
                response = await self._chat_fallback(messages, temp)
                self.fallback_circuit_breaker.record_success()
                return response
            except Exception as e:
                logger.warning(f"Fallback provider failed: {e}")
                self.fallback_circuit_breaker.record_failure()
        
        # All providers failed
        raise ExternalServiceError("All AI providers failed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ExternalServiceError, httpx.HTTPError)),
    )
    async def _embed_primary(self, text: str) -> List[float]:
        """Embed using LiteLLM"""
        client = await self._get_client()
        
        url = f"{config.LITELLM_API_BASE}/embeddings"
        payload = {
            "model": config.LITELLM_EMBEDDING_MODEL,
            "input": text,
        }
        headers = {
            "Authorization": f"Bearer {config.LITELLM_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await asyncio.wait_for(
                client.post(url, json=payload, headers=headers),
                timeout=config.LLM_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except asyncio.TimeoutError as e:
            raise RouterTimeoutError(f"LiteLLM embedding timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(f"LiteLLM embedding HTTP error: {e}") from e
        except Exception as e:
            raise ExternalServiceError(f"LiteLLM embedding error: {e}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ExternalServiceError, httpx.HTTPError)),
    )
    async def _embed_fallback(self, text: str) -> List[float]:
        """Embed using OpenAI"""
        if not config.OPENAI_API_KEY:
            raise ExternalServiceError("OpenAI API key not configured")
        
        client = await self._get_client()
        
        url = "https://api.openai.com/v1/embeddings"
        payload = {
            "model": config.OPENAI_EMBEDDING_MODEL,
            "input": text,
        }
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await asyncio.wait_for(
                client.post(url, json=payload, headers=headers),
                timeout=config.OPENAI_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except asyncio.TimeoutError as e:
            raise RouterTimeoutError(f"OpenAI embedding timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(f"OpenAI embedding HTTP error: {e}") from e
        except Exception as e:
            raise ExternalServiceError(f"OpenAI embedding error: {e}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ExternalServiceError, httpx.HTTPError)),
    )
    async def _chat_primary(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Chat using LiteLLM"""
        client = await self._get_client()
        
        url = f"{config.LITELLM_API_BASE}/chat/completions"
        payload = {
            "model": config.LITELLM_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {config.LITELLM_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await asyncio.wait_for(
                client.post(url, json=payload, headers=headers),
                timeout=config.LLM_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except asyncio.TimeoutError as e:
            raise RouterTimeoutError(f"LiteLLM chat timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(f"LiteLLM chat HTTP error: {e}") from e
        except Exception as e:
            raise ExternalServiceError(f"LiteLLM chat error: {e}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ExternalServiceError, httpx.HTTPError)),
    )
    async def _chat_fallback(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Chat using OpenAI"""
        if not config.OPENAI_API_KEY:
            raise ExternalServiceError("OpenAI API key not configured")
        
        client = await self._get_client()
        
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": config.OPENAI_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await asyncio.wait_for(
                client.post(url, json=payload, headers=headers),
                timeout=config.OPENAI_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except asyncio.TimeoutError as e:
            raise RouterTimeoutError(f"OpenAI chat timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(f"OpenAI chat HTTP error: {e}") from e
        except Exception as e:
            raise ExternalServiceError(f"OpenAI chat error: {e}") from e

