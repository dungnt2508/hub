"""
Embedding Scorer - Cosine similarity with boost
"""
import math
from typing import List, Dict, Optional
from dataclasses import dataclass

from .intent_store import IntentEmbedding


@dataclass
class ScoredIntent:
    """Intent with similarity score"""
    intent: str
    domain: str
    score: float


class EmbeddingScorer:
    """Score intent embeddings using cosine similarity"""
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same length")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def apply_boost(self, score: float, domain: str, boost: Dict[str, float]) -> float:
        """Apply keyword boost to score"""
        if domain in boost:
            # Boost formula: score + (1 - score) * boost_value
            # This ensures boost doesn't exceed 1.0
            boost_value = boost[domain]
            boosted_score = score + (1.0 - score) * boost_value * 0.2  # Scale boost to 20% max
            return min(boosted_score, 1.0)
        return score
    
    def best_match(
        self,
        query_embedding: List[float],
        intents: List[IntentEmbedding],
        boost: Dict[str, float]
    ) -> Optional[ScoredIntent]:
        """
        Find best matching intent.
        
        Args:
            query_embedding: Query embedding vector
            intents: List of intent embeddings
            boost: Domain boost scores
            
        Returns:
            ScoredIntent with highest score, or None if no intents
        """
        if not intents:
            return None
        
        best_score = -1.0
        best_intent: Optional[ScoredIntent] = None
        
        for intent_emb in intents:
            # Calculate cosine similarity
            similarity = self.cosine_similarity(query_embedding, intent_emb.embedding)
            
            # Apply boost
            boosted_score = self.apply_boost(similarity, intent_emb.domain, boost)
            
            if boosted_score > best_score:
                best_score = boosted_score
                best_intent = ScoredIntent(
                    intent=intent_emb.intent,
                    domain=intent_emb.domain,
                    score=boosted_score,
                )
        
        return best_intent

