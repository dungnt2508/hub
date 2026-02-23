from typing import List, Dict, Any, Optional
import json
from openai import AsyncOpenAI

from app.core.interfaces.llm_provider import ILLMProvider
from app.core.config.settings import get_settings
from app.infrastructure.llm.circuit_breaker import llm_circuit
from circuitbreaker import CircuitBreakerError

class OpenAIProvider(ILLMProvider):
    """
    Adapter: OpenAI implementation of ILLMProvider.
    Supports both native OpenAI and LiteLLM (OpenAI-compatible) backends.
    """
    
    def __init__(self, is_litellm: bool = False):
        settings = get_settings()
        self.is_litellm = is_litellm
        
        if is_litellm:
            self.api_base = settings.litellm_api_base
            self.api_key = settings.litellm_api_key
            self.chat_model = settings.litellm_chat_model
            self.embedding_model = settings.litellm_embedding_model
        else:
            self.api_base = settings.openai_api_base
            self.api_key = settings.openai_api_key
            self.chat_model = settings.openai_chat_model
            self.embedding_model = settings.openai_embedding_model
            
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base if is_litellm else None,
            timeout=settings.llm_timeout
        ) if self.api_key else None

    async def get_embedding(self, text: str) -> List[float]:
        if not self.client: return []
        try:
            resp = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return resp.data[0].embedding
        except Exception:
            return []

    async def generate_response(
        self, 
        system_prompt: str, 
        user_message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        if not self.client: 
            return {"response": "LLM client not configured."}
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Inject history if available
        if messages_history:
            # Validate and filter history to ensure correct format
            valid_roles = {"user", "assistant", "system"}
            for msg in messages_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] in valid_roles:
                         messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            kwargs = {
                "model": self.chat_model,
                "messages": messages,
            }
            if tools:
                openai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["parameters"]
                        }
                    }
                    for t in tools
                ]
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            resp = await self._call_api(**kwargs)
            message = resp.choices[0].message
            
            return {
                "response": message.content or "",
                "tool_calls": message.tool_calls or [],
                "id": resp.id,
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                    "total_tokens": resp.usage.total_tokens
                } if hasattr(resp, 'usage') else None,
                "model": resp.model
            }
        except CircuitBreakerError:
            return {
                "response": "Hệ thống đang quá tải, vui lòng thử lại sau giây lát. (Circuit Breaker Open)",
                "tool_calls": [],
                "usage": None
            }
        except Exception as e:
            print(f"[LLM-ERROR] {str(e)}") # Log internal error
            return {
                "response": "Xin lỗi, tôi đang gặp chút sự cố kết nối. Bạn vui lòng thử lại câu hỏi nhé.", 
                "tool_calls": [], 
                "usage": None
            }

    @llm_circuit
    async def _call_api(self, **kwargs):
        return await self.client.chat.completions.create(**kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "litellm" if self.is_litellm else "openai",
            "model": self.chat_model,
            "embedding_model": self.embedding_model
        }
