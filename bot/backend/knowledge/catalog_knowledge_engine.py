"""
Catalog Knowledge Engine - RAG Pipeline with Hybrid Search for catalog domain
"""
from typing import Optional, Dict, Any, List, Tuple

from ..schemas import KnowledgeRequest, KnowledgeResponse, KnowledgeSource
from ..infrastructure.ai_provider import AIProvider
from ..shared.exceptions import ExternalServiceError
from ..shared.logger import logger
from .catalog_retriever import CatalogRetriever, RetrievedProduct
from ..domain.catalog.intent_classifier import CatalogIntentClassifier, CatalogIntentType
from ..domain.catalog.hybrid_search_helper import CatalogHybridSearchHelper


# RAG Prompt Template - Strict Prompting Version
CATALOG_RAG_PROMPT_TEMPLATE_STRICT = """Bạn là một trợ lý hỗ trợ cho một marketplace công cụ/luồng công việc. Nhiệm vụ của bạn là giúp người dùng tìm công cụ/luồng công việc phù hợp dựa trên danh sách sản phẩm có sẵn.

DANH SÁCH SẢN PHẨM CÓ SẴN:
{products_context}

CÂU HỎI CỦA NGƯỜI DÙNG:
{question}

QUY TẮC BẮT BUỘC (STRICT):
1. **CHỈ TRẢ LỜI DỰA TRÊN DANH SÁCH TRÊN** - Bạn PHẢI trả lời dựa HOÀN TOÀN trên các sản phẩm trong danh sách ở trên. 
2. **KHÔNG BỊ ẢO GIÁC** - Không bao giờ tạo ra sản phẩm, tính năng, hoặc giá cả không có trong danh sách.
3. **NẾU KHÔNG CÓ SẢN PHẨM PHÙ HỢP** - Hãy nói rõ ràng: "Tôi không tìm thấy sản phẩm nào trong danh sách phù hợp với yêu cầu của bạn."
4. **KHI GỢI Ý SẢN PHẨM** - Bạn PHẢI bao gồm:
   - Tên sản phẩm
   - Giải thích tại sao nó phù hợp (dựa trên dữ liệu)
   - Product ID (format: product_<id>)
5. **THÔNG TIN THUỘC TÍNH** - Nếu hỏi về giá, tính năng, v.v., CHỈ trả lời những gì CÓ TRONG DANH SÁCH
6. **NGÔN NGỮ** - Trả lời bằng tiếng Việt vì người dùng hỏi bằng tiếng Việt

TRƯỚC KHI TRẢ LỜI:
- Kiểm tra xem câu hỏi có thể được trả lời từ danh sách sản phẩm không
- Nếu CÓ: Trả lời chi tiết dựa trên danh sách
- Nếu KHÔNG: Nói rõ rằng bạn không có thông tin này

TRẢ LỜI:"""


# Alternative prompt for generic searches
CATALOG_RAG_PROMPT_TEMPLATE_GENERIC = """Bạn là một trợ lý hỗ trợ cho một marketplace công cụ/luồng công việc. Nhiệm vụ của bạn là giúp người dùng tìm công cụ/luồng công việc phù hợp dựa trên danh sách sản phẩm có sẵn.

SẢN PHẨM CÓ LIÊN QUAN:
{products_context}

CÂU HỎI CỦA NGƯỜI DÙNG:
{question}

HƯỚNG DẪN:
1. Trả lời câu hỏi dựa trên danh sách sản phẩm ở trên
2. Nếu không tìm thấy sản phẩm phù hợp, hãy nói rõ ràng
3. Khi gợi ý sản phẩm, hãy bao gồm tên, lý do, và Product ID (format: product_<id>)
4. Hãy ngắn gọn và hữu ích

TRẢ LỜI:"""


class CatalogKnowledgeEngine:
    """
    Catalog Knowledge Engine using RAG pipeline with Hybrid Search.
    
    ⚠️ NOTE: This engine is now secondary to the new use-case-based architecture.
    The new CatalogEntryHandler uses use cases (SearchProductUseCase, etc.) instead.
    This engine is kept for backward compatibility and RAG-based responses.
    
    This engine combines:
    - Intent Classification (specific catalog query types)
    - Hybrid Search (vector + DB queries)
    - Strict RAG Prompting (prevents hallucinations)
    
    Responsibilities:
    - Classify catalog queries into specific intent types
    - Route to appropriate retrieval strategy (vector, DB, or hybrid)
    - Generate answers using LLM with strict prompting
    - Format response with citations
    
    Architecture:
    - Application Layer (orchestration)
    - Uses domain layer components (intent_classifier, hybrid_search_helper)
    - Generates LLM-based answers with RAG
    """
    
    def __init__(
        self,
        retriever: Optional[CatalogRetriever] = None,
        intent_classifier: Optional[CatalogIntentClassifier] = None,
        hybrid_helper: Optional[CatalogHybridSearchHelper] = None,
        ai_provider: Optional[AIProvider] = None,
        max_products: int = 5,
        enable_intent_classifier: bool = True,
    ):
        """
        Initialize catalog knowledge engine.
        
        Args:
            retriever: Optional CatalogRetriever instance
            intent_classifier: Optional CatalogIntentClassifier instance
            hybrid_helper: Optional CatalogHybridSearchHelper instance
            ai_provider: Optional AIProvider instance
            max_products: Maximum number of products to include in context
            enable_intent_classifier: Whether to use intent classification (default: True)
        """
        self.retriever = retriever or CatalogRetriever(ai_provider=ai_provider)
        self.intent_classifier = intent_classifier or CatalogIntentClassifier(ai_provider=ai_provider) if enable_intent_classifier else None
        self.hybrid_helper = hybrid_helper or CatalogHybridSearchHelper()
        self.ai_provider = ai_provider or AIProvider()
        self.max_products = max_products
        self.enable_intent_classifier = enable_intent_classifier
        logger.info(
            "CatalogKnowledgeEngine initialized",
            extra={
                "intent_classifier_enabled": enable_intent_classifier,
                "max_products": max_products,
            }
        )
    
    async def answer(
        self,
        request: KnowledgeRequest,
        tenant_id: Optional[str] = None,
        conversation_context: Optional[List[str]] = None,
    ) -> KnowledgeResponse:
        """
        Answer knowledge question using RAG pipeline with Hybrid Search.
        
        Args:
            request: Knowledge request with question
            tenant_id: Tenant UUID (extracted from context if not provided)
            conversation_context: Optional previous messages for context
        
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
                    "has_context": conversation_context is not None,
                }
            )
            
            # Extract tenant_id from context or request
            if not tenant_id:
                tenant_id = request.context.get("tenant_id") if request.context else None
            
            if not tenant_id:
                raise ValueError("tenant_id is required for catalog knowledge queries")
            
            # Step 1: Classify intent (if enabled)
            intent_classification = None
            if self.enable_intent_classifier:
                try:
                    intent_classification = await self.intent_classifier.classify(
                        query=request.question,
                        conversation_context=conversation_context,
                    )
                    logger.info(
                        "Intent classification result",
                        extra={
                            "intent_type": intent_classification.intent_type.value,
                            "confidence": intent_classification.confidence,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Intent classification failed, falling back to vector search: {e}")
                    intent_classification = None
            
            # Step 2: Retrieve products based on intent
            retrieved_products = await self._retrieve_products(
                tenant_id=tenant_id,
                query=request.question,
                intent_classification=intent_classification,
                conversation_context=conversation_context,
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
                        "retrieval_method": self._get_retrieval_method(intent_classification),
                        "products_found": 0,
                        "intent_type": intent_classification.intent_type.value if intent_classification else "unknown",
                    },
                )
            
            # Step 3: Build products context for LLM
            products_context = self._build_products_context(retrieved_products)
            
            # Step 4: Generate answer using LLM with strict prompting
            answer = await self._generate_answer(
                question=request.question,
                products_context=products_context,
                intent_classification=intent_classification,
            )
            
            # Step 5: Extract citations and build sources
            citations, sources = self._extract_citations(retrieved_products)
            
            # Step 6: Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(retrieved_products)
            
            logger.info(
                f"Catalog knowledge response generated",
                extra={
                    "trace_id": request.trace_id,
                    "products_found": len(retrieved_products),
                    "confidence": confidence,
                    "retrieval_method": self._get_retrieval_method(intent_classification),
                }
            )
            
            return KnowledgeResponse(
                answer=answer,
                citations=citations,
                confidence=confidence,
                sources=sources,
                metadata={
                    "retrieval_method": self._get_retrieval_method(intent_classification),
                    "products_found": len(retrieved_products),
                    "top_score": retrieved_products[0].score if retrieved_products else 0.0,
                    "intent_type": intent_classification.intent_type.value if intent_classification else "unknown",
                    "intent_confidence": intent_classification.confidence if intent_classification else 0.0,
                },
            )
            
        except Exception as e:
            logger.error(
                f"Catalog knowledge engine error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Catalog knowledge engine failed: {e}") from e
    
    async def _retrieve_products(
        self,
        tenant_id: str,
        query: str,
        intent_classification: Optional[Any] = None,
        conversation_context: Optional[List[str]] = None,
    ) -> List[RetrievedProduct]:
        """
        Retrieve products based on intent classification.
        Uses Hybrid Search strategy.
        
        Args:
            tenant_id: Tenant UUID
            query: User query
            intent_classification: Optional intent classification result
            conversation_context: Optional conversation context
        
        Returns:
            List of retrieved products
        """
        # Default: use vector search
        if not intent_classification or intent_classification.intent_type == CatalogIntentType.UNKNOWN:
            return await self.retriever.retrieve_with_context(
                tenant_id=tenant_id,
                query=query,
                conversation_context=conversation_context,
                top_k=self.max_products,
            )
        
        # Route based on intent type
        if intent_classification.intent_type == CatalogIntentType.PRODUCT_SEARCH:
            # Generic search: use vector search
            return await self.retriever.retrieve_with_context(
                tenant_id=tenant_id,
                query=query,
                conversation_context=conversation_context,
                top_k=self.max_products,
            )
        
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_SPECIFIC_INFO:
            # Specific attribute search: use DB query + vector search (hybrid)
            attribute = intent_classification.extracted_info.get("attribute")
            
            if attribute:
                # Try DB query for specific attribute
                db_results = await self.hybrid_helper.search_by_specific_attribute(
                    tenant_id=tenant_id,
                    attribute=attribute,
                    limit=self.max_products,
                )
                
                # Also get vector results for context
                vector_results = await self.retriever.retrieve_with_context(
                    tenant_id=tenant_id,
                    query=query,
                    conversation_context=conversation_context,
                    top_k=self.max_products,
                )
                
                # Merge results: prioritize DB results
                merged = self._merge_results(db_results, vector_results, max_results=self.max_products)
                return merged
            else:
                # Fallback: vector search
                return await self.retriever.retrieve_with_context(
                    tenant_id=tenant_id,
                    query=query,
                    conversation_context=conversation_context,
                    top_k=self.max_products,
                )
        
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_COMPARISON:
            # Comparison: retrieve specific products mentioned
            product_names = intent_classification.extracted_info.get("product_names", [])
            
            if product_names:
                comparison_results = await self.hybrid_helper.search_by_comparison_attributes(
                    tenant_id=tenant_id,
                    product_names=product_names,
                    limit=self.max_products // len(product_names) if product_names else self.max_products,
                )
                
                # Flatten comparison results
                all_products = []
                for products in comparison_results.values():
                    all_products.extend(products)
                
                return all_products[:self.max_products]
            else:
                # Fallback: vector search
                return await self.retriever.retrieve_with_context(
                    tenant_id=tenant_id,
                    query=query,
                    conversation_context=conversation_context,
                    top_k=self.max_products,
                )
        
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_COUNT:
            # Count query: use DB count + top products
            count = await self.hybrid_helper.count_products_in_category(
                tenant_id=tenant_id,
            )
            
            # Get top products to show examples
            top_products = await self.retriever.retrieve(
                tenant_id=tenant_id,
                query=query,
                top_k=3,  # Show 3 examples
            )
            
            return top_products
        
        else:
            # Unknown intent: use vector search
            return await self.retriever.retrieve_with_context(
                tenant_id=tenant_id,
                query=query,
                conversation_context=conversation_context,
                top_k=self.max_products,
            )
    
    def _merge_results(
        self,
        db_results: List[RetrievedProduct],
        vector_results: List[RetrievedProduct],
        max_results: int = 5,
    ) -> List[RetrievedProduct]:
        """
        Merge DB and vector search results, avoiding duplicates.
        
        Args:
            db_results: Results from DB query
            vector_results: Results from vector search
            max_results: Maximum results to return
        
        Returns:
            Merged and deduplicated results
        """
        merged = []
        seen_ids = set()
        
        # Add DB results first (exact matches)
        for product in db_results:
            if product.product_id not in seen_ids:
                merged.append(product)
                seen_ids.add(product.product_id)
        
        # Add vector results (ranked by relevance)
        for product in vector_results:
            if product.product_id not in seen_ids and len(merged) < max_results:
                merged.append(product)
                seen_ids.add(product.product_id)
        
        return merged[:max_results]
    
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
            product_text = f"""Sản phẩm {i}:
- Tên: {product.title}
- ID: {product.product_id}
- Mô tả: {product.description}
- Điểm phù hợp: {product.score:.2f}"""
            
            # Add additional metadata if available
            if product.metadata.get("tags"):
                tags = ", ".join(product.metadata.get("tags", []))
                product_text += f"\n- Thẻ: {tags}"
            
            if product.metadata.get("features"):
                features = ", ".join(product.metadata.get("features", [])[:5])
                product_text += f"\n- Tính năng: {features}"
            
            if product.metadata.get("price") or product.metadata.get("pricing"):
                price_info = product.metadata.get("price") or product.metadata.get("pricing")
                product_text += f"\n- Giá: {price_info}"
            
            if product.metadata.get("is_free"):
                product_text += f"\n- Miễn phí: {product.metadata.get('is_free')}"
            
            context_parts.append(product_text.strip())
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(
        self,
        question: str,
        products_context: str,
        intent_classification: Optional[Any] = None,
    ) -> str:
        """
        Generate answer using LLM with strict prompting.
        
        Args:
            question: User question
            products_context: Formatted products context
            intent_classification: Optional intent classification
        
        Returns:
            Generated answer text
        """
        # Use strict prompting for specific queries, generic for searches
        if intent_classification and intent_classification.intent_type in [
            CatalogIntentType.PRODUCT_SPECIFIC_INFO,
            CatalogIntentType.PRODUCT_COMPARISON,
        ]:
            prompt_template = CATALOG_RAG_PROMPT_TEMPLATE_STRICT
        else:
            prompt_template = CATALOG_RAG_PROMPT_TEMPLATE_GENERIC
        
        prompt = prompt_template.format(
            products_context=products_context,
            question=question,
        )
        
        messages = [
            {
                "role": "system",
                "content": "Bạn là một trợ lý hỗ trợ cho một marketplace công cụ/luồng công việc.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        
        # Generate answer using AI provider
        answer = await self.ai_provider.chat(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent, factual responses
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
            citation = f"product_{product.product_id}"
            citations.append(citation)
            
            source = KnowledgeSource(
                title=product.title,
                url=None,
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
    
    def _get_retrieval_method(self, intent_classification: Optional[Any]) -> str:
        """
        Get retrieval method name for logging.
        
        Args:
            intent_classification: Optional intent classification
        
        Returns:
            Retrieval method name
        """
        if not intent_classification or intent_classification.intent_type == CatalogIntentType.UNKNOWN:
            return "vector_search"
        
        if intent_classification.intent_type == CatalogIntentType.PRODUCT_SEARCH:
            return "vector_search"
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_SPECIFIC_INFO:
            return "hybrid_search"
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_COMPARISON:
            return "db_query"
        elif intent_classification.intent_type == CatalogIntentType.PRODUCT_COUNT:
            return "db_count"
        else:
            return "vector_search"
