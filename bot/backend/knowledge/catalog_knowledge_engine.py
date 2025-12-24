"""
Catalog Knowledge Engine - RAG Pipeline for catalog domain
"""
from typing import Optional, Dict, Any, List, Tuple

from ..schemas import KnowledgeRequest, KnowledgeResponse, KnowledgeSource
from ..infrastructure.ai_provider import AIProvider
from ..shared.exceptions import ExternalServiceError
from ..shared.logger import logger
from .catalog_retriever import CatalogRetriever, RetrievedProduct


# RAG Prompt Template
CATALOG_RAG_PROMPT_TEMPLATE = """You are a helpful assistant for a workflow marketplace. Your task is to help users find the right workflows, tools, or integrations based on their needs.

Available products from the catalog:
{products_context}

User question: {question}

Instructions:
1. Answer the question based on the available products above
2. If no relevant products are found or the question is not about products, politely say so
3. When recommending products, include:
   - Product title
   - Brief description of why it matches
   - Product ID (format: product_<id>)
4. Be concise and helpful
5. If the user asks about features or capabilities, reference specific products that have those features
6. Respond in Vietnamese if the user asks in Vietnamese, otherwise respond in English

Answer:"""


class CatalogKnowledgeEngine:
    """
    Catalog Knowledge Engine using RAG pipeline.
    
    Responsibilities:
    - Retrieve relevant products using semantic search
    - Generate answer using LLM with retrieved context
    - Format response with citations
    """
    
    def __init__(
        self,
        retriever: Optional[CatalogRetriever] = None,
        ai_provider: Optional[AIProvider] = None,
        max_products: int = 5,
    ):
        """
        Initialize catalog knowledge engine.
        
        Args:
            retriever: Optional CatalogRetriever instance
            ai_provider: Optional AIProvider instance
            max_products: Maximum number of products to include in context
        """
        self.retriever = retriever or CatalogRetriever(ai_provider=ai_provider)
        self.ai_provider = ai_provider or AIProvider()
        self.max_products = max_products
        logger.info("CatalogKnowledgeEngine initialized")
    
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
                "Catalog knowledge request received",
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
                raise ValueError("tenant_id is required for catalog knowledge queries")
            
            # Step 1: Retrieve relevant products
            retrieved_products = await self.retriever.retrieve(
                tenant_id=tenant_id,
                query=request.question,
                top_k=self.max_products,
            )
            
            if not retrieved_products:
                # No products found
                return KnowledgeResponse(
                    answer=(
                        "Xin lỗi, tôi không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn. "
                        "Bạn có thể thử tìm kiếm với các từ khóa khác hoặc mô tả rõ hơn về nhu cầu của mình."
                    ),
                    citations=[],
                    confidence=0.0,
                    sources=[],
                    metadata={
                        "retrieval_method": "vector",
                        "products_found": 0,
                    },
                )
            
            # Step 2: Build products context for LLM
            products_context = self._build_products_context(retrieved_products)
            
            # Step 3: Generate answer using LLM
            answer = await self._generate_answer(
                question=request.question,
                products_context=products_context,
            )
            
            # Step 4: Extract citations and build sources
            citations, sources = self._extract_citations(retrieved_products)
            
            # Step 5: Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(retrieved_products)
            
            logger.info(
                f"Catalog knowledge response generated",
                extra={
                    "trace_id": request.trace_id,
                    "products_found": len(retrieved_products),
                    "confidence": confidence,
                }
            )
            
            return KnowledgeResponse(
                answer=answer,
                citations=citations,
                confidence=confidence,
                sources=sources,
                metadata={
                    "retrieval_method": "vector",
                    "products_found": len(retrieved_products),
                    "top_score": retrieved_products[0].score if retrieved_products else 0.0,
                },
            )
            
        except Exception as e:
            logger.error(
                f"Catalog knowledge engine error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Catalog knowledge engine failed: {e}") from e
    
    def _build_products_context(self, products: List[RetrievedProduct]) -> str:
        """
        Build formatted context string from retrieved products.
        
        Args:
            products: List of retrieved products
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, product in enumerate(products, 1):
            product_text = f"""
Product {i}:
- Title: {product.title}
- ID: {product.product_id}
- Description: {product.description}
- Match Score: {product.score:.2f}
"""
            
            # Add additional metadata if available
            if product.metadata.get("tags"):
                tags = ", ".join(product.metadata.get("tags", []))
                product_text += f"- Tags: {tags}\n"
            
            if product.metadata.get("features"):
                features = ", ".join(product.metadata.get("features", [])[:5])  # Limit features
                product_text += f"- Features: {features}\n"
            
            context_parts.append(product_text.strip())
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(
        self,
        question: str,
        products_context: str,
    ) -> str:
        """
        Generate answer using LLM with products context.
        
        Args:
            question: User question
            products_context: Formatted products context
        
        Returns:
            Generated answer text
        """
        prompt = CATALOG_RAG_PROMPT_TEMPLATE.format(
            products_context=products_context,
            question=question,
        )
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for a workflow marketplace.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        
        # Generate answer using AI provider
        answer = await self.ai_provider.chat(
            messages=messages,
            temperature=0.7,  # Higher temperature for more natural responses
        )
        
        return answer.strip()
    
    def _extract_citations(
        self,
        products: List[RetrievedProduct],
    ) -> Tuple[List[str], List[KnowledgeSource]]:
        """
        Extract citations and build sources from retrieved products.
        
        Args:
            products: List of retrieved products
        
        Returns:
            Tuple of (citations list, sources list)
        """
        citations = []
        sources = []
        
        for product in products:
            # Citation format: product_<product_id>
            citation = f"product_{product.product_id}"
            citations.append(citation)
            
            # Build source
            source = KnowledgeSource(
                title=product.title,
                url=None,  # Can be constructed from product_id if needed
                excerpt=product.description[:200] if product.description else None,
            )
            sources.append(source)
        
        return citations, sources
    
    def _calculate_confidence(self, products: List[RetrievedProduct]) -> float:
        """
        Calculate confidence score based on retrieval results.
        
        Args:
            products: List of retrieved products with scores
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not products:
            return 0.0
        
        # Use top result score as base confidence
        top_score = products[0].score
        
        # Boost confidence if multiple good matches
        if len(products) >= 3 and top_score > 0.8:
            confidence = min(top_score + 0.1, 1.0)
        else:
            confidence = top_score
        
        # Cap at reasonable maximum
        return min(confidence, 0.95)

