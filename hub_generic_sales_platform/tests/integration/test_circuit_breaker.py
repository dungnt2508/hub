import pytest
from unittest.mock import AsyncMock, patch
from app.infrastructure.llm.openai_provider import OpenAIProvider
from app.infrastructure.llm.circuit_breaker import llm_circuit
from circuitbreaker import CircuitBreakerError

@pytest.mark.asyncio
async def test_llm_circuit_breaker():
    """Verify circuit breaker opens after failures"""
    
    # 1. Setup Provider
    provider = OpenAIProvider(is_litellm=False)
    
    # Mock the client to avoid real API calls
    provider.client = AsyncMock()
    
    # Reset circuit breaker state
    llm_circuit.reset()
    
    # 2. Mock _call_api to fail
    # We patch the METHOD on the CLASS or INSTANCE? 
    # Since we use @llm_circuit decorator, the circuit state is global/shared by default instance of decorator.
    
    # The decorator wraps _call_api. 
    # If we mock _call_api directly, we might bypass the decorator if we are not careful.
    # But we want to fail the *inner* call.
    
    # Actually, we should mock `provider.client.chat.completions.create` causing exception.
    provider.client.chat.completions.create.side_effect = Exception("API Error")
    
    # 3. Trigger failures (Threshold = 5)
    # Provider trả về message thân thiện thay vì raw error (per runtime_fix_plan)
    for _ in range(5):
        resp = await provider.generate_response("prompt", "msg")
        assert "sự cố" in resp["response"] or "gặp" in resp["response"]
        
    # 4. Next call should trigger CircuitBreakerError
    resp = await provider.generate_response("prompt", "msg")
    assert "Circuit Breaker Open" in resp["response"]
    
    # 5. Reset for other tests
    llm_circuit.reset()
