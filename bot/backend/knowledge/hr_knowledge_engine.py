"""
HR Knowledge Engine - RAG Pipeline for HR domain
"""
from typing import Dict, Any, Optional, List

from ..schemas import KnowledgeRequest, KnowledgeResponse, KnowledgeSource
from ..infrastructure.ai_provider import AIProvider
from ..shared.exceptions import ExternalServiceError
from ..shared.logger import logger
from .rag_orchestrator import RAGOrchestrator


# HR RAG Prompt Template
HR_RAG_PROMPT_TEMPLATE = """Based on the following HR policy documents, please answer the employee's question in Vietnamese.

Available documents:
{products_context}

Employee's question: {question}

Instructions:
1. Answer based only on the provided HR policy documents
2. If the answer is not in the documents, say so clearly
3. Provide a helpful and accurate answer
4. If relevant, mention specific policy details or requirements
5. Respond in Vietnamese

Answer:"""


class HRKnowledgeEngine:
    """
    HR Knowledge Engine using RAG pipeline.
    
    Responsibilities:
    - Retrieve relevant HR policies and FAQs
    - Generate answers using LLM with retrieved context
    - Format response with citations and sources
    
    This engine is read-only and provides knowledge answers
    based on policy documents and FAQs.
    """
    
    def __init__(
        self,
        rag_orchestrator: Optional[RAGOrchestrator] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        """
        Initialize HR knowledge engine.
        
        Args:
            rag_orchestrator: Optional RAGOrchestrator instance
            ai_provider: Optional AIProvider instance
        """
        self.rag_orchestrator = rag_orchestrator or RAGOrchestrator()
        self.ai_provider = ai_provider or AIProvider()
        logger.info("HRKnowledgeEngine initialized")
    
    async def answer(
        self,
        request: KnowledgeRequest,
        tenant_id: Optional[str] = None,
    ) -> KnowledgeResponse:
        """
        Answer knowledge question using RAG pipeline.
        
        Args:
            request: Knowledge request with question
            tenant_id: Tenant UUID (extracted from context if not provided)
            
        Returns:
            Knowledge response with answer and citations
            
        Raises:
            ExternalServiceError: If external services fail
        """
        try:
            logger.info(
                "HR Knowledge request received",
                extra={
                    "trace_id": request.trace_id,
                    "domain": request.domain,
                    "question": request.question[:100],
                }
            )
            
            # Extract tenant_id from context or request
            if not tenant_id:
                tenant_id = request.context.get("tenant_id") if request.context else None
            
            if not tenant_id:
                # Use default tenant for HR policies
                tenant_id = "default"
            
            # Use RAG pipeline to answer question
            rag_result = await self.rag_orchestrator.answer_question(
                question=request.question,
                tenant_id=tenant_id,
                domain="hr",
                context=request.context,
            )
            
            # Convert RAG result to KnowledgeResponse
            response = KnowledgeResponse(
                answer=rag_result["answer"],
                citations=[f"{s['id']}" for s in rag_result.get("sources", [])],
                confidence=rag_result.get("confidence", 0.0),
                sources=[
                    KnowledgeSource(
                        title=s.get("source", "Unknown"),
                        url=None,
                        page=s.get("page"),
                        excerpt=s.get("excerpt"),
                    )
                    for s in rag_result.get("sources", [])
                ],
                metadata={
                    "retrieval_method": rag_result.get("metadata", {}).get("retrieval_method", "vector"),
                    "retrieved_count": rag_result.get("metadata", {}).get("retrieved_count", 0),
                    "top_score": rag_result.get("metadata", {}).get("top_score", 0.0),
                },
            )
            
            logger.info(
                "HR knowledge response generated",
                extra={
                    "trace_id": request.trace_id,
                    "confidence": response.confidence,
                    "sources_count": len(response.sources),
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"HR Knowledge engine error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise ExternalServiceError(f"HR Knowledge engine failed: {e}") from e

