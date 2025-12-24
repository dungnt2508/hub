"""
STEP 4: Embedding Classifier
"""
import asyncio
from typing import Dict, Any

from ...shared.logger import logger
from ...shared.config import config
from ...shared.exceptions import ExternalServiceError
from ...infrastructure.ai_provider import AIProvider
from ...infrastructure.intent_store import IntentStore
from ...infrastructure.embedding_scorer import EmbeddingScorer


class EmbeddingClassifierStep:
    """
    Semantic routing using embedding similarity.
    
    Uses vector embeddings to match user intent to domain/intent.
    """
    
    def __init__(
        self,
        provider: AIProvider = None,
        intent_store: IntentStore = None,
        scorer: EmbeddingScorer = None
    ):
        """Initialize embedding classifier step"""
        self.provider = provider or AIProvider()
        self.intent_store = intent_store or IntentStore()
        self.scorer = scorer or EmbeddingScorer()
        self.threshold = config.EMBEDDING_THRESHOLD
        self._embeddings_loaded = False
    
    async def execute(self, message: str, boost: Dict[str, float]) -> Dict[str, Any]:
        """
        Classify using embedding similarity.
        
        Args:
            message: Normalized message
            boost: Keyword boost scores
            
        Returns:
            Dict with classification result
        """
        if not config.ENABLE_EMBEDDING:
            return {"classified": False, "reason": "embedding_disabled"}
        
        try:
            # Ensure embeddings are loaded
            if not self._embeddings_loaded:
                await self.intent_store.load_embeddings(self.provider)
                self._embeddings_loaded = True
            
            # Get query embedding with timeout
            query_vec = await asyncio.wait_for(
                self.provider.embed(message),
                timeout=config.STEP_EMBEDDING_TIMEOUT / 1000.0
            )
            
            # Get all intents
            intents = self.intent_store.get_all()
            
            if not intents:
                logger.warning("No intents in intent store")
                return {"classified": False, "reason": "no_intents"}
            
            # Find best match
            best = self.scorer.best_match(query_vec, intents, boost)
            
            if not best or best.score < self.threshold:
                return {
                    "classified": False,
                    "reason": "score_below_threshold",
                    "score": best.score if best else None,
                }
            
            logger.info(
                "Embedding classification successful",
                extra={
                    "intent": best.intent,
                    "domain": best.domain,
                    "score": best.score,
                }
            )
            
            return {
                "classified": True,
                "intent": best.intent,
                "domain": best.domain,
                "confidence": best.score,
                "source": "EMBEDDING",
            }
            
        except asyncio.TimeoutError as e:
            logger.warning(f"Embedding classification timeout: {e}")
            return {"classified": False, "reason": "timeout"}
        except ExternalServiceError as e:
            logger.error(f"Embedding classification error: {e}", exc_info=True)
            return {"classified": False, "reason": "provider_error"}
        except Exception as e:
            logger.error(f"Embedding classification failed: {e}", exc_info=True)
            return {"classified": False, "reason": "unknown_error"}