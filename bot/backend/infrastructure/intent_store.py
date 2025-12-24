"""
Intent Store for Embedding Classifier
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..shared.logger import logger
from ..shared.intent_registry import IntentRegistry, intent_registry


@dataclass
class IntentEmbedding:
    """Intent with its embedding vector"""
    intent: str
    domain: str
    intent_type: str
    description: str
    embedding: List[float]


class IntentStore:
    """Store for intent embeddings"""
    
    def __init__(self, registry: IntentRegistry = None):
        """Initialize intent store"""
        self.registry = registry or intent_registry
        self.intents: Dict[str, IntentEmbedding] = {}
        self._embeddings_loaded = False
    
    async def load_embeddings(self, provider) -> None:
        """
        Generate and load embeddings for all intents.
        
        Args:
            provider: AIProvider instance for generating embeddings
        """
        if self._embeddings_loaded:
            return
        
        logger.info("Generating embeddings for intents...")
        
        for intent_name, intent_info in self.registry.intents.items():
            try:
                # Create text representation for embedding
                text = f"{intent_info.description}. Domain: {intent_info.domain}. Type: {intent_info.intent_type}."
                
                # Generate embedding
                embedding = await provider.embed(text)
                
                # Store intent with embedding
                self.intents[intent_name] = IntentEmbedding(
                    intent=intent_name,
                    domain=intent_info.domain,
                    intent_type=intent_info.intent_type,
                    description=intent_info.description,
                    embedding=embedding,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to generate embedding for intent {intent_name}: {e}",
                    exc_info=True
                )
        
        self._embeddings_loaded = True
        logger.info(f"Loaded embeddings for {len(self.intents)} intents")
    
    def add_intent_embedding(
        self,
        intent: str,
        embedding: List[float]
    ):
        """Add intent with embedding"""
        intent_info = self.registry.get_intent(intent)
        if not intent_info:
            return
        
        self.intents[intent] = IntentEmbedding(
            intent=intent,
            domain=intent_info.domain,
            intent_type=intent_info.intent_type,
            description=intent_info.description,
            embedding=embedding,
        )
    
    def get_intent_embedding(self, intent: str) -> Optional[IntentEmbedding]:
        """Get intent embedding"""
        return self.intents.get(intent)
    
    def get_all(self) -> List[IntentEmbedding]:
        """Get all intent embeddings"""
        return list(self.intents.values())
    
    def get_by_domain(self, domain: str) -> List[IntentEmbedding]:
        """Get intents by domain"""
        return [
            intent_emb
            for intent_emb in self.intents.values()
            if intent_emb.domain == domain
        ]

