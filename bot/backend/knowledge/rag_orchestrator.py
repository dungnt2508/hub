"""
RAG Orchestrator - Main orchestration for RAG pipeline
Coordinates retrieval, context building, and LLM generation
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio

from ..infrastructure.ai_provider import AIProvider
from ..infrastructure.vector_store import QdrantVectorStore
from ..schemas import KnowledgeRequest, KnowledgeResponse, KnowledgeSource
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


class RetrievedDocument:
    """Retrieved document with metadata and score"""
    
    def __init__(
        self,
        id: str,
        content: str,
        source: str,
        score: float,
        metadata: Dict[str, Any],
    ):
        self.id = id
        self.content = content
        self.source = source
        self.score = score
        self.metadata = metadata


class RAGOrchestrator:
    """
    Orchestrate RAG (Retrieval-Augmented Generation) pipeline.
    
    Pipeline:
    1. Embed query
    2. Retrieve similar documents
    3. Build context from retrieved documents
    4. Generate answer using LLM with context
    5. Extract sources and citations
    """
    
    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        ai_provider: Optional[AIProvider] = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ):
        """
        Initialize RAG orchestrator.
        
        Args:
            vector_store: Vector store for retrieval
            ai_provider: AI provider for embeddings and generation
            top_k: Number of documents to retrieve
            score_threshold: Minimum similarity score for retrieval
        """
        self.vector_store = vector_store or QdrantVectorStore()
        self.ai_provider = ai_provider or AIProvider()
        self.top_k = top_k
        self.score_threshold = score_threshold
        
        logger.info(
            "RAGOrchestrator initialized",
            extra={"top_k": top_k, "score_threshold": score_threshold}
        )
    
    async def answer_question(
        self,
        question: str,
        tenant_id: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Answer question using RAG pipeline.
        
        Args:
            question: User question
            tenant_id: Tenant UUID
            domain: Domain filter (optional)
            context: Additional context
        
        Returns:
            Answer dict with:
            - answer: Generated answer text
            - sources: List of source documents
            - confidence: Confidence score (0-1)
            - metadata: Metadata about the RAG process
        
        Raises:
            ExternalServiceError: If RAG process fails
        """
        try:
            logger.info(
                "RAG answer_question started",
                extra={
                    "question": question[:100],
                    "tenant_id": tenant_id,
                    "domain": domain,
                }
            )
            
            # Step 1: Embed the question
            query_embedding = await self._embed_query(question)
            
            # Step 2: Retrieve relevant documents
            retrieved_docs = await self._retrieve_documents(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                domain_filter=domain,
            )
            
            if not retrieved_docs:
                logger.warning(
                    "No relevant documents found",
                    extra={"tenant_id": tenant_id, "question": question[:50]}
                )
                return {
                    "answer": (
                        "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn. "
                        "Vui lòng thử lại với câu hỏi khác hoặc mô tả chi tiết hơn."
                    ),
                    "sources": [],
                    "confidence": 0.0,
                    "metadata": {
                        "retrieval_method": "vector",
                        "retrieved_count": 0,
                        "used_count": 0,
                    }
                }
            
            logger.info(
                f"Retrieved {len(retrieved_docs)} documents",
                extra={
                    "tenant_id": tenant_id,
                    "count": len(retrieved_docs),
                    "avg_score": sum(d.score for d in retrieved_docs) / len(retrieved_docs),
                }
            )
            
            # Step 3: Build context from retrieved documents
            context_text = self._build_context(retrieved_docs)
            
            # Step 4: Generate answer using LLM
            answer = await self._generate_answer(
                question=question,
                context=context_text,
            )
            
            # Step 5: Extract sources
            sources = self._extract_sources(retrieved_docs)
            
            # Step 6: Calculate confidence
            confidence = self._calculate_confidence(retrieved_docs)
            
            logger.info(
                "RAG answer_question completed",
                extra={
                    "tenant_id": tenant_id,
                    "confidence": confidence,
                    "sources_count": len(sources),
                }
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "metadata": {
                    "retrieval_method": "vector",
                    "retrieved_count": len(retrieved_docs),
                    "used_count": len(sources),
                    "top_score": retrieved_docs[0].score if retrieved_docs else 0.0,
                }
            }
        
        except Exception as e:
            logger.error(
                f"RAG answer_question failed: {e}",
                extra={"tenant_id": tenant_id},
                exc_info=True
            )
            raise ExternalServiceError(f"RAG pipeline failed: {e}") from e
    
    async def _embed_query(self, question: str) -> List[float]:
        """
        Embed user question.
        
        Args:
            question: User question text
        
        Returns:
            Embedding vector
        """
        try:
            logger.debug(f"Embedding query: {question[:50]}...")
            embedding = await self.ai_provider.embed(question)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}", exc_info=True)
            raise
    
    async def _retrieve_documents(
        self,
        tenant_id: str,
        query_embedding: List[float],
        domain_filter: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents from vector store.
        
        Args:
            tenant_id: Tenant UUID
            query_embedding: Query embedding vector
            domain_filter: Optional domain filter
        
        Returns:
            List of retrieved documents
        """
        try:
            # Build metadata filter if domain specified
            metadata_filter = None
            if domain_filter:
                metadata_filter = {"domain": domain_filter}
            
            # Search in vector store
            search_results = await self.vector_store.search(
                tenant_id=tenant_id,
                query_vector=query_embedding,
                top_k=self.top_k,
                score_threshold=self.score_threshold,
            )
            
            # Convert to RetrievedDocument objects
            retrieved_docs = []
            for result in search_results:
                doc = RetrievedDocument(
                    id=result.id,
                    content=result.metadata.get("content", ""),
                    source=result.metadata.get("source", "unknown"),
                    score=result.score,
                    metadata=result.metadata,
                )
                retrieved_docs.append(doc)
            
            return retrieved_docs
        
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}", exc_info=True)
            raise
    
    def _build_context(self, documents: List[RetrievedDocument]) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            documents: List of retrieved documents
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # Extract first part of content for context
            content_preview = doc.content[:300]
            if len(doc.content) > 300:
                content_preview += "..."
            
            source_info = f"Source: {doc.source}"
            if doc.metadata.get("page"):
                source_info += f" (Page {doc.metadata['page']})"
            
            context_part = f"""
Document {i}: {source_info}
Relevance Score: {doc.score:.2f}
Content:
{content_preview}
"""
            context_parts.append(context_part.strip())
        
        context = "\n\n".join(context_parts)
        
        logger.debug(f"Built context from {len(documents)} documents")
        
        return context
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate answer using LLM with context.
        
        Args:
            question: User question
            context: Context from retrieved documents
        
        Returns:
            Generated answer
        """
        try:
            prompt = f"""Based on the following documents, please answer the user's question in Vietnamese.

Available documents:
{context}

User's question: {question}

Instructions:
1. Answer based only on the provided documents
2. If the answer is not in the documents, say so clearly
3. Provide a comprehensive but concise answer
4. Respond in Vietnamese

Answer:"""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided documents. Always respond in Vietnamese."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
            
            logger.debug("Generating answer with LLM...")
            answer = await self.ai_provider.chat(
                messages=messages,
                temperature=0.7,
            )
            
            return answer.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}", exc_info=True)
            raise
    
    def _extract_sources(
        self,
        documents: List[RetrievedDocument],
    ) -> List[Dict[str, Any]]:
        """
        Extract source information from retrieved documents.
        
        Args:
            documents: List of retrieved documents
        
        Returns:
            List of source dicts
        """
        sources = []
        
        for doc in documents:
            source = {
                "id": doc.id,
                "source": doc.source,
                "score": doc.score,
                "page": doc.metadata.get("page"),
                "domain": doc.metadata.get("domain"),
                "excerpt": doc.content[:200] if doc.content else None,
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(
        self,
        documents: List[RetrievedDocument],
    ) -> float:
        """
        Calculate confidence score based on retrieval results.
        
        Args:
            documents: List of retrieved documents with scores
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not documents:
            return 0.0
        
        # Use top result score as base confidence
        top_score = documents[0].score
        
        # Adjust based on number of good matches
        good_matches = len([d for d in documents if d.score > 0.7])
        
        if good_matches >= 3:
            # Multiple good matches boost confidence
            confidence = min(top_score + 0.15, 1.0)
        elif good_matches >= 1:
            # At least one good match
            confidence = top_score
        else:
            # Low-quality matches reduce confidence
            confidence = top_score * 0.8
        
        # Cap at reasonable maximum
        return min(confidence, 0.95)

