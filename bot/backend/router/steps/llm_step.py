"""
STEP 5: LLM Classifier (Fallback)
"""
import asyncio
import json
from typing import Dict, Any, List

from ...schemas import SessionState
from ...shared.logger import logger
from ...shared.config import config
from ...shared.exceptions import ExternalServiceError
from ...shared.intent_registry import intent_registry
from ...infrastructure.ai_provider import AIProvider


class LLMClassifierStep:
    """
    LLM-based classification for complex/ambiguous queries.
    
    This is a fallback step when other methods fail.
    """
    
    def __init__(self, provider: AIProvider = None):
        """Initialize LLM classifier step"""
        self.provider = provider or AIProvider()
    
    async def execute(
        self,
        message: str,
        session_state: SessionState
    ) -> Dict[str, Any]:
        """
        Classify using LLM.
        
        Args:
            message: Normalized message
            session_state: Current session state
            
        Returns:
            Dict with classification result
        """
        if not config.ENABLE_LLM_FALLBACK:
            return {"classified": False, "reason": "llm_fallback_disabled"}
        
        try:
            # Build prompt
            prompt = self._build_classification_prompt(message)
            
            # Call LLM with timeout
            response_text = await asyncio.wait_for(
                self.provider.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config.LLM_TEMPERATURE
                ),
                timeout=config.STEP_LLM_TIMEOUT / 1000.0
            )
            
            # Parse response
            result = self._parse_llm_response(response_text)
            
            if result.get("classified"):
                logger.info(
                    "LLM classification successful",
                    extra={
                        "intent": result.get("intent"),
                        "domain": result.get("domain"),
                        "confidence": result.get("confidence"),
                    }
                )
            
            return result
            
        except asyncio.TimeoutError as e:
            logger.warning(f"LLM classification timeout: {e}")
            return {"classified": False, "reason": "timeout"}
        except ExternalServiceError as e:
            logger.error(f"LLM classification error: {e}", exc_info=True)
            return {"classified": False, "reason": "provider_error"}
        except Exception as e:
            logger.error(f"LLM classification failed: {e}", exc_info=True)
            return {"classified": False, "reason": "unknown_error"}
    
    def _build_classification_prompt(self, message: str) -> str:
        """Build classification prompt for LLM"""
        # Get available intents from registry
        intents_info = []
        for intent_name, intent_info in intent_registry.intents.items():
            intents_info.append(
                f"- {intent_name} (domain: {intent_info.domain}, type: {intent_info.intent_type})"
            )
        
        intents_list = "\n".join(intents_info)
        
        prompt = f"""Bạn là một classifier để route câu hỏi của người dùng đến đúng domain và intent.

Các intent khả dụng:
{intents_list}

Câu hỏi của người dùng: "{message}"

Hãy phân tích và trả về JSON với format:
{{
    "domain": "domain_name",
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "reason": "lý do phân loại"
}}

Nếu không thể phân loại chắc chắn, trả về:
{{
    "classified": false,
    "reason": "lý do không phân loại được"
}}
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response JSON"""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                response_text = response_text.strip()
            if response_text.startswith("```json"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate result
            if result.get("classified") is False:
                return {"classified": False, "reason": result.get("reason", "unknown")}
            
            domain = result.get("domain")
            intent = result.get("intent")
            confidence = float(result.get("confidence", 0.0))
            
            if not domain or not intent:
                return {"classified": False, "reason": "missing_domain_or_intent"}
            
            # Validate intent exists
            if not intent_registry.is_valid_intent(intent):
                return {"classified": False, "reason": "invalid_intent"}
            
            # Check confidence threshold
            if confidence < config.LLM_THRESHOLD:
                return {
                    "classified": False,
                    "reason": "confidence_below_threshold",
                    "confidence": confidence,
                }
            
            intent_info = intent_registry.get_intent(intent)
            return {
                "classified": True,
                "domain": domain,
                "intent": intent,
                "intent_type": intent_info.intent_type if intent_info else None,
                "confidence": confidence,
                "source": "LLM",
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return {"classified": False, "reason": "invalid_json_response"}
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return {"classified": False, "reason": "parse_error"}

