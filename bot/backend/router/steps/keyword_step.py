"""
STEP 3: Keyword Hint (Soft Boost)
"""
import time
import json
from typing import Dict, Any, Optional
from uuid import UUID

from ...shared.logger import logger
from ...infrastructure.config_loader import config_loader


class KeywordHintStep:
    """
    Provide keyword-based hints for domain scoring.
    
    This step does NOT make final routing decisions.
    It only provides boost scores for other classifiers.
    Loads keywords from database via config_loader.
    """
    
    def __init__(self):
        self._domain_keywords: Optional[Dict[str, Dict[str, float]]] = None
        self._last_tenant_id: Optional[UUID] = None
        self._last_refresh_time: float = 0
        self._refresh_interval = 300  # 5 minutes
    
    async def _load_keywords(self, tenant_id: Optional[UUID] = None):
        """Load keyword hints from config"""
        current_time = time.time()
        
        # Check if we need to refresh
        if (
            self._domain_keywords is None
            or tenant_id != self._last_tenant_id
            or (current_time - self._last_refresh_time) > self._refresh_interval
        ):
            # Load from config loader
            hints = await config_loader.get_keyword_hints(tenant_id, enabled_only=True)
            
            # Build domain_keywords dict
            domain_keywords = {}
            for hint in hints:
                domain = hint.get("domain")
                if not domain:
                    logger.warning(f"Keyword hint missing domain: {hint.get('id', 'unknown')}")
                    continue
                
                keywords = hint.get("keywords", {})
                
                # Ensure keywords is a dict (parse JSON if it's a string)
                if isinstance(keywords, str):
                    try:
                        keywords = json.loads(keywords)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse keywords JSON for hint {hint.get('id')}: {e}")
                        keywords = {}
                elif not isinstance(keywords, dict):
                    logger.warning(
                        f"Keywords is not a dict for hint {hint.get('id')}: "
                        f"type={type(keywords)}, value={keywords}"
                    )
                    keywords = {}
                
                if domain not in domain_keywords:
                    domain_keywords[domain] = {}
                
                # Merge keywords (if multiple hints for same domain, combine)
                domain_keywords[domain].update(keywords)
            
            self._domain_keywords = domain_keywords
            self._last_tenant_id = tenant_id
            self._last_refresh_time = current_time
    
    async def execute(self, message: str, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Calculate keyword-based boost scores.
        
        Args:
            message: Normalized message
            tenant_id: Optional tenant ID for tenant-specific keywords
            
        Returns:
            Dict with "boost" scores per domain
        """
        await self._load_keywords(tenant_id)
        
        if not self._domain_keywords:
            return {"boost": {}}
        
        boost = {}
        message_lower = message.lower()
        
        for domain, keywords in self._domain_keywords.items():
            score = 0.0
            for keyword, weight in keywords.items():
                if keyword in message_lower:
                    score += weight
            
            # Normalize to 0-1 range
            score = min(score, 1.0)
            if score > 0:
                boost[domain] = score
        
        logger.debug(
            "Keyword boost calculated",
            extra={"boost": boost, "tenant_id": str(tenant_id) if tenant_id else None}
        )
        
        return {"boost": boost}

