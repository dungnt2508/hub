"""Guardrail policy enforcement"""
from typing import Dict, Any
from backend.domain.catalog import Guardrail


class GuardrailPolicy:
    """Policy for guardrail enforcement"""
    
    @staticmethod
    def check_query(
        guardrail: Guardrail,
        query_text: str
    ) -> Dict[str, Any]:
        """
        Check if query violates guardrails.
        
        Returns:
            {
                "violated": bool,
                "allowed": bool,
                "reason": str (if violated),
                "fallback_message": str (if violated),
                "disclaimers": list (if not violated)
            }
        """
        # Check forbidden topics
        if guardrail.forbidden_topics:
            query_lower = query_text.lower()
            for topic in guardrail.forbidden_topics:
                if topic.lower() in query_lower:
                    return {
                        "violated": True,
                        "allowed": False,
                        "reason": f"Query contains forbidden topic: {topic}",
                        "fallback_message": guardrail.fallback_message or "Xin lỗi, tôi không thể trả lời câu hỏi này.",
                        "disclaimers": None
                    }
        
        # No violation
        return {
            "violated": False,
            "allowed": True,
            "reason": None,
            "fallback_message": None,
            "disclaimers": guardrail.disclaimers or []
        }
