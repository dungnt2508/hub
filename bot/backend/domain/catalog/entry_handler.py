"""
Catalog Domain Engine - Entry Handler
"""
from typing import Dict, Any, Optional

from ...schemas import DomainRequest, DomainResponse, DomainResult, KnowledgeRequest
from ...shared.exceptions import DomainError, InvalidInputError
from ...shared.logger import logger
from ...knowledge import CatalogKnowledgeEngine


class CatalogEntryHandler:
    """
    Entry point for catalog domain engine.
    
    Handles product search and recommendation requests using RAG pipeline.
    """
    
    def __init__(self, knowledge_engine: Optional[CatalogKnowledgeEngine] = None):
        """
        Initialize catalog entry handler.
        
        Args:
            knowledge_engine: Optional CatalogKnowledgeEngine instance
        """
        self.knowledge_engine = knowledge_engine or CatalogKnowledgeEngine()
        logger.info("CatalogEntryHandler initialized")
    
    async def handle(self, request: DomainRequest) -> DomainResponse:
        """
        Handle catalog domain request.
        
        Args:
            request: Domain request with intent and slots
        
        Returns:
            Domain response with knowledge answer
        
        Raises:
            DomainError: If handling fails
        """
        try:
            logger.info(
                "Catalog domain request received",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "tenant_id": request.user_context.get("tenant_id"),
                }
            )
            
            # Catalog domain only handles KNOWLEDGE intents
            if request.intent_type != "KNOWLEDGE":
                raise InvalidInputError(
                    f"Catalog domain only handles KNOWLEDGE intents, got: {request.intent_type}"
                )
            
            # Extract question from slots or user message
            question = self._extract_question(request)
            
            if not question:
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message="Không thể xác định câu hỏi từ yêu cầu của bạn. Vui lòng thử lại.",
                    error_code="MISSING_QUESTION",
                )
            
            # Extract tenant_id from user_context
            tenant_id = request.user_context.get("tenant_id")
            if not tenant_id:
                logger.warning(
                    "Missing tenant_id in catalog request",
                    extra={"trace_id": request.trace_id}
                )
                return DomainResponse(
                    status=DomainResult.INVALID_REQUEST,
                    message="Thiếu thông tin tenant. Vui lòng liên hệ admin.",
                    error_code="MISSING_TENANT_ID",
                )
            
            # Create knowledge request
            knowledge_request = KnowledgeRequest(
                question=question,
                domain=request.domain,
                context={
                    "tenant_id": tenant_id,
                    "intent": request.intent,
                    "user_context": request.user_context,
                },
                trace_id=request.trace_id,
            )
            
            # Get answer from knowledge engine
            knowledge_response = await self.knowledge_engine.answer(
                knowledge_request,
                tenant_id=tenant_id,
            )
            
            # Format domain response
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "answer": knowledge_response.answer,
                    "citations": knowledge_response.citations,
                    "sources": [
                        {
                            "title": source.title,
                            "url": source.url,
                            "excerpt": source.excerpt,
                        }
                        for source in (knowledge_response.sources or [])
                    ],
                    "confidence": knowledge_response.confidence,
                    "metadata": knowledge_response.metadata,
                },
                message=knowledge_response.answer,
                audit={
                    "domain": request.domain,
                    "intent": request.intent,
                    "confidence": knowledge_response.confidence,
                    "products_found": knowledge_response.metadata.get("products_found", 0),
                },
            )
            
        except InvalidInputError as e:
            logger.warning(
                f"Invalid catalog request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT",
            )
        except Exception as e:
            logger.error(
                f"Catalog domain error: {e}",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                },
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi tìm kiếm sản phẩm. Vui lòng thử lại sau.",
                error_code="SYSTEM_ERROR",
                error_details={"error": str(e)},
            )
    
    def _extract_question(self, request: DomainRequest) -> Optional[str]:
        """
        Extract question text from domain request.
        
        Args:
            request: Domain request
        
        Returns:
            Question text or None
        """
        # Try to get question from slots
        question = request.slots.get("question") or request.slots.get("query") or request.slots.get("message")
        
        # If not in slots, try to construct from other slots
        if not question and request.slots:
            # Try to build question from available slots
            parts = []
            if request.slots.get("product_type"):
                parts.append(f"loại {request.slots['product_type']}")
            if request.slots.get("feature"):
                parts.append(f"có tính năng {request.slots['feature']}")
            if request.slots.get("tag"):
                parts.append(f"về {request.slots['tag']}")
            
            if parts:
                question = f"Tìm {', '.join(parts)}"
        
        # If still no question, use a default based on intent
        if not question:
            intent_defaults = {
                "catalog.search": "Tìm kiếm sản phẩm",
                "catalog.recommend": "Gợi ý sản phẩm phù hợp",
                "catalog.info": "Thông tin về sản phẩm",
            }
            question = intent_defaults.get(request.intent, "Tìm kiếm sản phẩm")
        
        return question

