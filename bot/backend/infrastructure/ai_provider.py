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
    """
    Simplified circuit breaker for provider failures.
    
    Simple boolean-based circuit breaker (no complex state machine).
    For low-load scenarios, this is sufficient and easier to debug.
    """
    
    def __init__(self, failure_threshold: int, timeout: int):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout: Seconds to wait before attempting to close circuit again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_circuit_open = False  # Simple boolean flag
        
        # Metrics
        self.total_opens = 0  # Total times circuit has been opened
        self.total_rejects = 0  # Total requests rejected when circuit is open
    
    def record_success(self):
        """Record successful request - reset circuit breaker"""
        self.failure_count = 0
        self.is_circuit_open = False
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            if not self.is_circuit_open:
                # Circuit just opened
                self.total_opens += 1
                self.is_circuit_open = True
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures",
                    extra={
                        "failure_count": self.failure_count,
                        "threshold": self.failure_threshold,
                        "total_opens": self.total_opens,
                    }
                )
    
    def is_open(self) -> bool:
        """
        Check if circuit breaker is open.
        
        Returns:
            True if circuit is open, False if closed
        """
        if not self.is_circuit_open:
            return False
        
        # Circuit is open - check if timeout has passed
        if self.last_failure_time:
            time_since_failure = datetime.utcnow() - self.last_failure_time
            if time_since_failure > timedelta(seconds=self.timeout):
                # Timeout passed - allow one request to test (circuit closes on success)
                logger.info(
                    f"Circuit breaker timeout passed, allowing test request",
                    extra={
                        "time_since_failure_seconds": time_since_failure.total_seconds(),
                        "timeout_seconds": self.timeout,
                    }
                )
                return False
        
        # Circuit still open - reject request
        self.total_rejects += 1
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.
        
        Returns:
            Dict with metrics
        """
        return {
            "is_open": self.is_circuit_open,
            "failure_count": self.failure_count,
            "total_opens": self.total_opens,
            "total_rejects": self.total_rejects,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


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
        errors = []
        
        # Try primary provider
        if not self.primary_circuit_breaker.is_open():
            try:
                logger.debug(f"🔹 Trying primary provider (LiteLLM) for embedding...")
                embedding = await self._embed_primary(text)
                self.primary_circuit_breaker.record_success()
                logger.debug(f"✅ Primary provider embedding succeeded")
                return embedding
            except Exception as e:
                error_msg = f"Primary provider (LiteLLM) embedding failed: {str(e)}"
                logger.warning(error_msg, exc_info=True)
                errors.append(error_msg)
                self.primary_circuit_breaker.record_failure()
        else:
            error_msg = f"Primary provider circuit breaker is open"
            logger.warning(error_msg)
            errors.append(error_msg)
        
        # Try fallback provider
        if not self.fallback_circuit_breaker.is_open():
            try:
                logger.debug(f"🔹 Trying fallback provider (OpenAI) for embedding...")
                embedding = await self._embed_fallback(text)
                self.fallback_circuit_breaker.record_success()
                logger.debug(f"✅ Fallback provider embedding succeeded")
                return embedding
            except Exception as e:
                error_msg = f"Fallback provider (OpenAI) embedding failed: {str(e)}"
                logger.warning(error_msg, exc_info=True)
                errors.append(error_msg)
                self.fallback_circuit_breaker.record_failure()
        else:
            error_msg = f"Fallback provider circuit breaker is open"
            logger.warning(error_msg)
            errors.append(error_msg)
        
        # All providers failed
        full_error = "All AI providers failed for embedding:\n" + "\n".join(errors)
        logger.error(full_error)
        raise ExternalServiceError(full_error)
    
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
        
        errors = []
        
        # Try primary provider
        if not self.primary_circuit_breaker.is_open():
            try:
                logger.debug(f"🔹 Trying primary provider (LiteLLM)...")
                response = await self._chat_primary(messages, temp)
                self.primary_circuit_breaker.record_success()
                logger.debug(f"✅ Primary provider succeeded")
                return response
            except Exception as e:
                error_msg = f"Primary provider (LiteLLM) failed: {str(e)}"
                logger.warning(error_msg, exc_info=True)
                errors.append(error_msg)
                self.primary_circuit_breaker.record_failure()
        else:
            error_msg = f"Primary provider circuit breaker is open"
            logger.warning(error_msg)
            errors.append(error_msg)
        
        # Try fallback provider
        if not self.fallback_circuit_breaker.is_open():
            try:
                logger.debug(f"🔹 Trying fallback provider (OpenAI)...")
                response = await self._chat_fallback(messages, temp)
                self.fallback_circuit_breaker.record_success()
                logger.debug(f"✅ Fallback provider succeeded")
                return response
            except Exception as e:
                error_msg = f"Fallback provider (OpenAI) failed: {str(e)}"
                logger.warning(error_msg, exc_info=True)
                errors.append(error_msg)
                self.fallback_circuit_breaker.record_failure()
        else:
            error_msg = f"Fallback provider circuit breaker is open"
            logger.warning(error_msg)
            errors.append(error_msg)
        
        # All providers failed
        full_error = "All AI providers failed:\n" + "\n".join(errors)
        logger.error(full_error)
        raise ExternalServiceError(full_error)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ExternalServiceError, httpx.HTTPError)),
    )
    async def _embed_primary(self, text: str) -> List[float]:
        """Embed using LiteLLM"""
        # Check LiteLLM config
        if not config.LITELLM_API_KEY or config.LITELLM_API_KEY == "litellm-proxy-key":
            raise ExternalServiceError(
                f"❌ LiteLLM API key not configured properly. "
                f"Set LITELLM_API_KEY env var"
            )
        
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
        # Check LiteLLM config
        if not config.LITELLM_API_KEY or config.LITELLM_API_KEY == "litellm-proxy-key":
            raise ExternalServiceError(
                f"❌ LiteLLM API key not configured properly. "
                f"Set LITELLM_API_KEY env var. "
                f"Currently: LITELLM_API_BASE={config.LITELLM_API_BASE}"
            )
        
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
            raise ExternalServiceError(
                f"❌ OpenAI API key not configured. "
                f"Set OPENAI_API_KEY env var in .env file"
            )
        
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

