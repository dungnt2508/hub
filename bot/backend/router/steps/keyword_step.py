"""
STEP 3: Keyword Hint (Soft Boost)
"""
from typing import Dict, Any

from ...shared.logger import logger


class KeywordHintStep:
    """
    Provide keyword-based hints for domain scoring.
    
    This step does NOT make final routing decisions.
    It only provides boost scores for other classifiers.
    """
    
    def __init__(self):
        # Domain keywords with weights
        self.domain_keywords = {
            "hr": {
                "nghỉ phép": 0.5,
                "phép năm": 0.5,
                "nhân sự": 0.4,
                "lương": 0.3,
                "chấm công": 0.3,
            },
            "operations": {
                "vận hành": 0.4,
                "sản xuất": 0.4,
                "kho": 0.3,
            },
        }
    
    async def execute(self, message: str) -> Dict[str, Any]:
        """
        Calculate keyword-based boost scores.
        
        Args:
            message: Normalized message
            
        Returns:
            Dict with "boost" scores per domain
        """
        boost = {}
        message_lower = message.lower()
        
        for domain, keywords in self.domain_keywords.items():
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
            extra={"boost": boost}
        )
        
        return {"boost": boost}

