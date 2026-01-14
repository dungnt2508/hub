"""
Catalog Intent Classifier - Detect specific catalog query intents
"""
import json
import asyncio
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum

from ...infrastructure.ai_provider import AIProvider
from ...shared.logger import logger
from ...shared.exceptions import ExternalServiceError, LLMError, RouterTimeoutError
from ...shared.config import config


class CatalogIntentType(str, Enum):
    """Specific intent types within catalog domain"""
    PRODUCT_SEARCH = "PRODUCT_SEARCH"  # General product search (e.g., "Tìm công cụ AI")
    PRODUCT_SPECIFIC_INFO = "PRODUCT_SPECIFIC_INFO"  # Query specific attribute (e.g., "Giá bao nhiêu?", "Tính năng gì?")
    PRODUCT_COMPARISON = "PRODUCT_COMPARISON"  # Compare products (e.g., "So sánh hai công cụ")
    PRODUCT_COUNT = "PRODUCT_COUNT"  # Count products (e.g., "Có bao nhiêu sản phẩm?")
    UNKNOWN = "UNKNOWN"  # Cannot classify


@dataclass
class ClassificationResult:
    """Catalog intent classification result"""
    intent_type: CatalogIntentType
    confidence: float  # 0.0 - 1.0
    reason: str
    extracted_info: Dict[str, Any]  # e.g., {"attribute": "price"}, {"product_names": ["tool1", "tool2"]}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "extracted_info": self.extracted_info,
        }


class CatalogIntentClassifier:
    """
    Classify catalog queries into specific intent types for Hybrid Search strategy.
    
    This is a secondary classifier after the routing orchestrator determines
    the message is for 'catalog' domain. This classifier decides HOW to search:
    - Vector-only search (generic product search)
    - Exact DB query (for specific attributes like price, features)
    - Comparison logic (for product comparison)
    - Count logic (for counting products)
    
    Responsibilities:
    - Classify user intent into specific catalog intent types
    - Extract relevant information (e.g., which attribute is being queried)
    - Provide confidence score
    - Return classification result with extracted info
    """
    
    def __init__(self, ai_provider: Optional[AIProvider] = None):
        """
        Initialize catalog intent classifier.
        
        Args:
            ai_provider: Optional AIProvider instance
        """
        self.ai_provider = ai_provider or AIProvider()
        logger.info("CatalogIntentClassifier initialized")
    
    async def classify(
        self,
        query: str,
        conversation_context: Optional[list[str]] = None,
    ) -> ClassificationResult:
        """
        Classify catalog query into specific intent type.
        
        Args:
            query: User query text
            conversation_context: Optional previous messages for context
        
        Returns:
            ClassificationResult with intent type and extracted info
        
        Raises:
            LLMError: If classification fails
            RouterTimeoutError: If classification times out
        """
        try:
            logger.info(
                "Classifying catalog query",
                extra={
                    "query_length": len(query),
                    "has_context": conversation_context is not None,
                }
            )
            
            # Build enriched query with context if available
            enriched_query = self._build_enriched_query(query, conversation_context)
            
            # Build classification prompt
            prompt = self._build_classification_prompt(enriched_query)
            
            # Call LLM with timeout
            try:
                response_text = await asyncio.wait_for(
                    self.ai_provider.chat(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,  # Lower temperature for more consistent classification
                    ),
                    timeout=config.STEP_LLM_TIMEOUT / 1000.0 if hasattr(config, 'STEP_LLM_TIMEOUT') else 5.0
                )
            except asyncio.TimeoutError as e:
                logger.error(
                    f"Catalog classification timeout: {e}",
                    extra={"query_length": len(query)},
                    exc_info=True
                )
                raise RouterTimeoutError(f"Catalog classification timeout after 5s") from e
            except ExternalServiceError as e:
                logger.error(
                    f"LLM provider error during catalog classification: {e}",
                    exc_info=True
                )
                raise LLMError(f"LLM provider failed: {e}") from e
            
            # Parse response
            result = self._parse_classification_response(response_text, query)
            
            logger.info(
                "Catalog query classified",
                extra={
                    "intent_type": result.intent_type.value,
                    "confidence": result.confidence,
                    "reason": result.reason,
                }
            )
            
            return result
            
        except (LLMError, RouterTimeoutError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected catalog classification error: {e}",
                exc_info=True
            )
            raise LLMError(f"Unexpected catalog classification error: {e}") from e
    
    def _build_enriched_query(
        self,
        query: str,
        conversation_context: Optional[list[str]] = None,
    ) -> str:
        """
        Build enriched query with conversation context.
        
        Args:
            query: Current user query
            conversation_context: Optional previous messages
        
        Returns:
            Enriched query text
        """
        if not conversation_context or len(conversation_context) == 0:
            return query
        
        # Use last 2 messages for context (user + bot response)
        context_text = "\n".join(conversation_context[-2:])
        return f"Conversation context:\n{context_text}\n\nCurrent question: {query}"
    
    def _build_classification_prompt(self, query: str) -> str:
        """
        Build classification prompt for LLM.
        
        Args:
            query: User query (possibly enriched with context)
        
        Returns:
            Prompt text
        """
        prompt = """Bạn là một classifier để xác định loại ý định của câu hỏi về sản phẩm/công cụ.

Các loại ý định (intent types):
1. PRODUCT_SEARCH - Tìm kiếm chung sản phẩm (ví dụ: "Tìm công cụ AI", "Công cụ nào có tính năng X?")
2. PRODUCT_SPECIFIC_INFO - Hỏi thông tin cụ thể của sản phẩm (ví dụ: "Giá bao nhiêu?", "Tính năng nào?", "Có miễn phí không?")
3. PRODUCT_COMPARISON - So sánh các sản phẩm (ví dụ: "So sánh công cụ A và B", "Khác biệt gì giữa...?")
4. PRODUCT_COUNT - Đếm số lượng sản phẩm (ví dụ: "Có bao nhiêu sản phẩm?", "Bao nhiêu công cụ...?")

Hướng dẫn phân loại:
- PRODUCT_SEARCH: Câu hỏi chung về tìm kiếm/khám phá sản phẩm mà không hỏi chi tiết cụ thể
- PRODUCT_SPECIFIC_INFO: Câu hỏi về một thuộc tính cụ thể (giá, tính năng, trạng thái, miễn phí, v.v.)
- PRODUCT_COMPARISON: Câu hỏi so sánh/phân biệt giữa 2 hay nhiều sản phẩm
- PRODUCT_COUNT: Câu hỏi về số lượng/đếm sản phẩm

Câu hỏi cần phân loại:
"{query}"

Trả về JSON với format:
{{
    "intent_type": "PRODUCT_SEARCH|PRODUCT_SPECIFIC_INFO|PRODUCT_COMPARISON|PRODUCT_COUNT",
    "confidence": 0.0-1.0,
    "reason": "lý do phân loại",
    "extracted_info": {{
        "attribute": "price|feature|status|free|availability|..." (nếu PRODUCT_SPECIFIC_INFO),
        "product_names": [...] (nếu PRODUCT_COMPARISON - những sản phẩm được đề cập)
    }}
}}

IMPORTANT:
- Chỉ trả về JSON, không có text khác
- confidence phải là số từ 0.0 đến 1.0
- extracted_info là object rỗng {{}} nếu không cần thêm info
"""
        return prompt
    
    def _parse_classification_response(
        self,
        response_text: str,
        original_query: str,
    ) -> ClassificationResult:
        """
        Parse LLM classification response.
        
        Args:
            response_text: LLM response text
            original_query: Original user query (for fallback)
        
        Returns:
            ClassificationResult
        """
        try:
            # Clean response text
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
            
            # Extract fields
            intent_type_str = result.get("intent_type", "UNKNOWN").upper()
            confidence = float(result.get("confidence", 0.0))
            reason = result.get("reason", "")
            extracted_info = result.get("extracted_info", {})
            
            # Validate intent_type
            try:
                intent_type = CatalogIntentType(intent_type_str)
            except ValueError:
                logger.warning(f"Invalid intent_type from LLM: {intent_type_str}")
                intent_type = CatalogIntentType.UNKNOWN
                confidence = 0.0
                reason = f"Invalid intent_type: {intent_type_str}"
            
            # Validate confidence
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                confidence = max(0.0, min(float(confidence), 1.0)) if isinstance(confidence, (int, float)) else 0.0
            
            return ClassificationResult(
                intent_type=intent_type,
                confidence=confidence,
                reason=reason,
                extracted_info=extracted_info or {},
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse catalog classification response as JSON: {e}")
            return ClassificationResult(
                intent_type=CatalogIntentType.UNKNOWN,
                confidence=0.0,
                reason=f"Failed to parse LLM response: {e}",
                extracted_info={},
            )
        except Exception as e:
            logger.warning(f"Failed to parse catalog classification response: {e}")
            return ClassificationResult(
                intent_type=CatalogIntentType.UNKNOWN,
                confidence=0.0,
                reason=f"Parse error: {e}",
                extracted_info={},
            )

