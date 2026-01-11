"""
Threshold Policy - Centralized routing decision thresholds
"""
from enum import Enum
from typing import Dict


class RoutingSource(str, Enum):
    """Routing decision source"""
    PATTERN = "PATTERN"
    EMBEDDING = "EMBEDDING"
    LLM = "LLM"


class ThresholdPolicy:
    """
    Centralized threshold policy for all routing decisions.
    
    This is the ONLY place where threshold decisions are made.
    Steps MUST NOT check thresholds independently.
    """
    
    # Default thresholds - can be overridden by config
    DEFAULT_THRESHOLDS: Dict[RoutingSource, float] = {
        RoutingSource.PATTERN: 1.0,      # Pattern must be 100% certain
        RoutingSource.EMBEDDING: 0.8,    # Embedding needs 80%+
        RoutingSource.LLM: 0.65,         # LLM needs 65%+
    }
    
    def __init__(self, thresholds: Dict[RoutingSource, float] = None):
        """
        Initialize policy with optional custom thresholds.
        
        Args:
            thresholds: Optional dict of source -> threshold
        """
        if thresholds is None:
            self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        else:
            # Merge with defaults
            self.thresholds = {
                **self.DEFAULT_THRESHOLDS,
                **thresholds
            }
    
    def should_route(
        self,
        source: RoutingSource,
        confidence: float
    ) -> bool:
        """
        Determine if result meets threshold for routing.
        
        Args:
            source: Where result came from (PATTERN, EMBEDDING, LLM)
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            True if confidence >= threshold for this source
        """
        threshold = self.thresholds.get(source, 0.0)
        meets_threshold = confidence >= threshold
        return meets_threshold
    
    def get_threshold(self, source: RoutingSource) -> float:
        """Get threshold for given source"""
        return self.thresholds.get(source, 0.0)
    
    def set_threshold(self, source: RoutingSource, threshold: float) -> None:
        """Set custom threshold for source"""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        self.thresholds[source] = threshold


# Global policy instance
_global_policy: ThresholdPolicy = None


def init_threshold_policy(thresholds: Dict[RoutingSource, float] = None) -> ThresholdPolicy:
    """Initialize global policy"""
    global _global_policy
    _global_policy = ThresholdPolicy(thresholds)
    return _global_policy


def get_threshold_policy() -> ThresholdPolicy:
    """Get global policy instance"""
    global _global_policy
    if _global_policy is None:
        _global_policy = ThresholdPolicy()
    return _global_policy
