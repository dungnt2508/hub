"""
STEP 4: Embedding Classifier
"""
import asyncio
from typing import Dict, Any

from ...shared.logger import logger
from ...shared.config import config
from ...shared.exceptions import ExternalServiceError, EmbeddingError, RouterTimeoutError
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
        
        NOTE: This step returns raw confidence scores.
        Threshold checking is done by orchestrator only (see ThresholdPolicy).
        
        Args:
            message: Normalized message
            boost: Keyword boost scores
            
        Returns:
            Dict with classification result (contains raw confidence, not decision)
        """
        if not config.ENABLE_EMBEDDING:
            return {"classified": False, "reason": "embedding_disabled"}
        
        try:
            # Ensure embeddings are loaded
            if not self._embeddings_loaded:
                try:
                    await self.intent_store.load_embeddings(self.provider)
                    self._embeddings_loaded = True
                except Exception as e:
                    logger.error(
                        f"Failed to load embeddings: {e}",
                        exc_info=True
                    )
                    raise EmbeddingError(f"Failed to load intent embeddings: {e}") from e
            
            # Get query embedding with timeout
            try:
                query_vec = await asyncio.wait_for(
                    self.provider.embed(message),
                    timeout=config.STEP_EMBEDDING_TIMEOUT / 1000.0
                )
            except asyncio.TimeoutError as e:
                logger.error(
                    f"Embedding classification timeout: {e}",
                    extra={"message_length": len(message)},
                    exc_info=True
                )
                raise RouterTimeoutError(f"Embedding timeout after {config.STEP_EMBEDDING_TIMEOUT}ms") from e
            except ExternalServiceError as e:
                logger.error(
                    f"Embedding provider error: {e}",
                    exc_info=True
                )
                raise EmbeddingError(f"Embedding provider failed: {e}") from e
            
            # Get all intents
            intents = self.intent_store.get_all()
            
            if not intents:
                logger.warning("No intents in intent store")
                # This is not an error, just no intents available
                return {"classified": False, "reason": "no_intents"}
            
            # Find best match
            try:
                best = self.scorer.best_match(query_vec, intents, boost)
            except Exception as e:
                logger.error(
                    f"Failed to calculate embedding similarity: {e}",
                    exc_info=True
                )
                raise EmbeddingError(f"Similarity calculation failed: {e}") from e
            
            if not best:
                # No match found (shouldn't happen, but handle gracefully)
                return {
                    "classified": False,
                    "reason": "no_match",
                }
            
            logger.info(
                "Embedding classification computed",
                extra={
                    "intent": best.intent,
                    "domain": best.domain,
                    "score": best.score,
                }
            )
            
            # Return raw score - orchestrator will decide based on ThresholdPolicy
            return {
                "classified": True,
                "intent": best.intent,
                "domain": best.domain,
                "confidence": best.score,  # RAW score
                "source": "EMBEDDING",
            }
            
        except (EmbeddingError, RouterTimeoutError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected embedding classification error: {e}",
                exc_info=True
            )
            raise EmbeddingError(f"Unexpected embedding error: {e}") from e