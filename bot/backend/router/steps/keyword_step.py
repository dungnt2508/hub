"""
STEP 3: Keyword Hint (Soft Boost)
"""
import json
from typing import Dict, Any, Optional
from uuid import UUID

from ...shared.logger import logger
from ...infrastructure.config_loader import config_loader
from ...shared.config_cache import get_config_cache


class KeywordHintStep:
    """
    Provide keyword-based hints for domain scoring.
    
    This step does NOT make final routing decisions.
    It only provides boost scores for other classifiers.
    Loads keywords from cache (ConfigCache handles DB loading and caching).
    
    NOTE: Internal caching has been REMOVED. Use ConfigCache for caching.
    """
    
    def __init__(self):
        self.config_cache = get_config_cache()
    
    def _parse_keywords(self, hint: Dict[str, Any]) -> Dict[str, float]:
        """
        Parse keywords from hint (handle JSON string or dict).
        
        Args:
            hint: Keyword hint from DB
            
        Returns:
            Dict mapping keyword -> weight
        """
        keywords = hint.get("keywords", {})
        
        # Ensure keywords is a dict (parse JSON if it's a string)
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse keywords JSON for hint {hint.get('id')}: {e}"
                )
                keywords = {}
        elif not isinstance(keywords, dict):
            logger.warning(
                f"Keywords is not a dict for hint {hint.get('id')}: "
                f"type={type(keywords)}, value={keywords}"
            )
            keywords = {}
        
        return keywords
    
    async def execute(self, message: str, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Calculate keyword-based boost scores.
        
        Args:
            message: Normalized message
            tenant_id: Optional tenant ID for tenant-specific keywords
            
        Returns:
            Dict with "boost" scores per domain
        """
        try:
            # Load keywords from cache (ConfigCache handles caching)
            hints = await self.config_cache.get_keyword_hints(
                tenant_id,
                lambda tid: config_loader.get_keyword_hints(tid, enabled_only=True)
            )
            
            if not hints:
                return {"boost": {}}
            
            # Build domain_keywords dict
            domain_keywords = {}
            for hint in hints:
                domain = hint.get("domain")
                if not domain:
                    logger.warning(f"Keyword hint missing domain: {hint.get('id', 'unknown')}")
                    continue
                
                keywords = self._parse_keywords(hint)
                
                if domain not in domain_keywords:
                    domain_keywords[domain] = {}
                
                # Merge keywords (if multiple hints for same domain, combine)
                domain_keywords[domain].update(keywords)
            
            # Calculate boost scores
            boost = {}
            message_lower = message.lower()
            
            for domain, keywords in domain_keywords.items():
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
            
        except Exception as e:
            logger.error(
                f"Keyword hint failed: {e}",
                extra={"tenant_id": str(tenant_id) if tenant_id else None},
                exc_info=True
            )
            # Return empty boost on error (not critical path)
            return {"boost": {}}

