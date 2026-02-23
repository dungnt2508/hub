from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ILLMProvider(ABC):
    """
    Port: Interface for LLM Providers.
    Defines the contract for all AI provider adapters (OpenAI, Gemini, etc.)
    """
    
    @abstractmethod
    async def generate_response(
        self, 
        system_prompt: str, 
        user_message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """General reasoning with tool support"""
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text"""
        pass
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata (model name, provider, etc.)"""
        pass
