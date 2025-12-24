"""
STEP 2: Global Pattern Match (Hard Rule)
"""
from typing import Dict, Any, Optional

from ...shared.logger import logger


class PatternMatchStep:
    """
    Deterministic pattern matching with priority-based rules.
    
    This step provides high-confidence routing decisions.
    """
    
    def __init__(self):
        # Pattern rules: (pattern, domain, intent, intent_type, priority)
        # Higher priority = checked first
        self.patterns = [
            # HR patterns
            (r"còn.*ngày.*phép", "hr", "query_leave_balance", "OPERATION", 10),
            (r"số.*ngày.*phép", "hr", "query_leave_balance", "OPERATION", 10),
            (r"xin.*nghỉ.*phép", "hr", "create_leave_request", "OPERATION", 10),
            (r"đăng ký.*nghỉ", "hr", "create_leave_request", "OPERATION", 10),
            (r"duyệt.*nghỉ.*phép", "hr", "approve_leave", "OPERATION", 10),
            
            # Knowledge patterns
            (r"chính sách.*nghỉ.*phép", "hr", "knowledge_policy_leave", "KNOWLEDGE", 9),
            (r"quy định.*nghỉ", "hr", "knowledge_policy_leave", "KNOWLEDGE", 9),
        ]
        
        # Compile regex patterns
        import re
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), domain, intent, intent_type, priority)
            for pattern, domain, intent, intent_type, priority in self.patterns
        ]
        # Sort by priority (descending)
        self.compiled_patterns.sort(key=lambda x: x[4], reverse=True)
    
    async def execute(self, message: str) -> Dict[str, Any]:
        """
        Match message against patterns.
        
        Args:
            message: Normalized message
            
        Returns:
            Dict with "matched" flag and routing info if matched
        """
        for pattern, domain, intent, intent_type, _ in self.compiled_patterns:
            if pattern.search(message):
                logger.info(
                    "Pattern matched",
                    extra={
                        "pattern": pattern.pattern,
                        "domain": domain,
                        "intent": intent,
                    }
                )
                return {
                    "matched": True,
                    "domain": domain,
                    "intent": intent,
                    "intent_type": intent_type,
                    "slots": {},
                    "confidence": 1.0,
                    "source": "PATTERN",
                }
        
        return {"matched": False}

