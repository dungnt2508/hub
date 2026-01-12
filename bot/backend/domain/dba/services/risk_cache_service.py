"""
Risk Assessment Cache Service - Cache risk assessment results
"""
import uuid
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ....shared.logger import logger
from ..risk_assessment_service import RiskAssessmentResult


class RiskCacheService:
    """
    In-memory cache for risk assessment results.
    
    Cache TTL: 5 minutes
    Used to avoid duplicate risk assessment runs.
    """
    
    _cache: Dict[str, tuple] = {}  # {risk_id: (result, expiry_time)}
    _ttl_seconds = 300  # 5 minutes
    
    @classmethod
    def store(cls, result: RiskAssessmentResult) -> str:
        """
        Store risk assessment result in cache.
        
        Returns:
            risk_id: UUID string for this risk assessment
        """
        risk_id = str(uuid.uuid4())
        expiry_time = time.time() + cls._ttl_seconds
        
        cls._cache[risk_id] = (result, expiry_time)
        
        logger.debug(
            f"Stored risk assessment in cache",
            extra={"risk_id": risk_id, "ttl_seconds": cls._ttl_seconds}
        )
        
        # Cleanup expired entries (simple cleanup, not perfect but good enough)
        cls._cleanup_expired()
        
        return risk_id
    
    @classmethod
    def get(cls, risk_id: str) -> Optional[RiskAssessmentResult]:
        """
        Get risk assessment result from cache.
        
        Returns:
            RiskAssessmentResult if found and not expired, None otherwise
        """
        if risk_id not in cls._cache:
            return None
        
        result, expiry_time = cls._cache[risk_id]
        
        if time.time() > expiry_time:
            # Expired
            del cls._cache[risk_id]
            logger.debug(f"Risk assessment cache expired", extra={"risk_id": risk_id})
            return None
        
        logger.debug(f"Retrieved risk assessment from cache", extra={"risk_id": risk_id})
        return result
    
    @classmethod
    def _cleanup_expired(cls):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in cls._cache.items()
            if current_time > expiry_time
        ]
        for key in expired_keys:
            del cls._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired risk assessments")


# Global instance
risk_cache_service = RiskCacheService()

