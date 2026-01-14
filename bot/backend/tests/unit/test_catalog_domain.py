"""
Unit Tests for Catalog Domain - Intent Classifier, Hybrid Search, and Knowledge Engine
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# Import classes to test
from bot.backend.domain.catalog.intent_classifier import (
    CatalogIntentClassifier,
    CatalogIntentType,
    ClassificationResult,
)
from bot.backend.domain.catalog.hybrid_search_helper import (
    CatalogHybridSearchHelper,
    SearchStrategy,
)
from bot.backend.knowledge.catalog_knowledge_engine import CatalogKnowledgeEngine
from bot.backend.knowledge.catalog_retriever import RetrievedProduct
from bot.backend.schemas import KnowledgeRequest


# ============================================================================
# Test CatalogIntentClassifier
# ============================================================================

class TestCatalogIntentClassifier:
    """Test suite for CatalogIntentClassifier"""
    
    @pytest.fixture
    def mock_ai_provider(self):
        """Mock AI provider"""
        provider = AsyncMock()
        return provider
    
    @pytest.fixture
    def classifier(self, mock_ai_provider):
        """Create classifier instance with mock"""
        return CatalogIntentClassifier(ai_provider=mock_ai_provider)
    
    @pytest.mark.asyncio
    async def test_classify_product_search(self, classifier, mock_ai_provider):
        """Test classifying a generic product search query"""
        mock_ai_provider.chat.return_value = """{
            "intent_type": "PRODUCT_SEARCH",
            "confidence": 0.95,
            "reason": "Người dùng đang tìm kiếm chung công cụ AI",
            "extracted_info": {}
        }"""
        
        result = await classifier.classify("Tìm công cụ AI nào tốt?")
        
        assert result.intent_type == CatalogIntentType.PRODUCT_SEARCH
        assert result.confidence == 0.95
        assert isinstance(result, ClassificationResult)
    
    @pytest.mark.asyncio
    async def test_classify_product_specific_info(self, classifier, mock_ai_provider):
        """Test classifying a specific attribute query"""
        mock_ai_provider.chat.return_value = """{
            "intent_type": "PRODUCT_SPECIFIC_INFO",
            "confidence": 0.88,
            "reason": "Hỏi về giá sản phẩm",
            "extracted_info": {"attribute": "price"}
        }"""
        
        result = await classifier.classify("Giá của công cụ này bao nhiêu?")
        
        assert result.intent_type == CatalogIntentType.PRODUCT_SPECIFIC_INFO
        assert result.confidence == 0.88
        assert result.extracted_info.get("attribute") == "price"
    
    @pytest.mark.asyncio
    async def test_classify_product_comparison(self, classifier, mock_ai_provider):
        """Test classifying a comparison query"""
        mock_ai_provider.chat.return_value = """{
            "intent_type": "PRODUCT_COMPARISON",
            "confidence": 0.92,
            "reason": "So sánh hai công cụ",
            "extracted_info": {"product_names": ["Tool A", "Tool B"]}
        }"""
        
        result = await classifier.classify("So sánh Tool A và Tool B")
        
        assert result.intent_type == CatalogIntentType.PRODUCT_COMPARISON
        assert result.confidence == 0.92
        assert "product_names" in result.extracted_info
    
    @pytest.mark.asyncio
    async def test_classify_product_count(self, classifier, mock_ai_provider):
        """Test classifying a count query"""
        mock_ai_provider.chat.return_value = """{
            "intent_type": "PRODUCT_COUNT",
            "confidence": 0.85,
            "reason": "Đếm số lượng sản phẩm",
            "extracted_info": {}
        }"""
        
        result = await classifier.classify("Có bao nhiêu công cụ trong catalog?")
        
        assert result.intent_type == CatalogIntentType.PRODUCT_COUNT
        assert result.confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_classify_with_context(self, classifier, mock_ai_provider):
        """Test classification with conversation context"""
        mock_ai_provider.chat.return_value = """{
            "intent_type": "PRODUCT_SPECIFIC_INFO",
            "confidence": 0.90,
            "reason": "Theo context, hỏi về tính năng",
            "extracted_info": {"attribute": "features"}
        }"""
        
        context = [
            "Người dùng: Công cụ AI nào tốt?",
            "Bot: Có Tool A, Tool B, Tool C...",
        ]
        
        result = await classifier.classify(
            "Tính năng nào tốt nhất?",
            conversation_context=context
        )
        
        assert result.intent_type == CatalogIntentType.PRODUCT_SPECIFIC_INFO
        assert result.extracted_info.get("attribute") == "features"
    
    def test_parse_invalid_json(self, classifier):
        """Test handling invalid JSON response"""
        result = classifier._parse_classification_response("invalid json", "test query")
        
        assert result.intent_type == CatalogIntentType.UNKNOWN
        assert result.confidence == 0.0
    
    def test_invalid_intent_type(self, classifier):
        """Test handling invalid intent type"""
        response = '{"intent_type": "INVALID_TYPE", "confidence": 0.5, "reason": "test"}'
        result = classifier._parse_classification_response(response, "test query")
        
        assert result.intent_type == CatalogIntentType.UNKNOWN


# ============================================================================
# Test CatalogHybridSearchHelper
# ============================================================================

class TestCatalogHybridSearchHelper:
    """Test suite for CatalogHybridSearchHelper"""
    
    @pytest.fixture
    def mock_db_client(self):
        """Mock database client"""
        db_client = AsyncMock()
        return db_client
    
    @pytest.fixture
    def helper(self, mock_db_client):
        """Create helper instance with mock"""
        return CatalogHybridSearchHelper(db_client=mock_db_client)
    
    @pytest.mark.asyncio
    async def test_search_by_price_attribute(self, helper, mock_db_client):
        """Test searching products by price attribute"""
        mock_db_client.fetch.return_value = [
            {
                "id": "1",
                "product_id": "prod1",
                "title": "Tool A",
                "description": "A tool",
                "metadata": {"price": "$99"},
            },
            {
                "id": "2",
                "product_id": "prod2",
                "title": "Tool B",
                "description": "B tool",
                "metadata": {"price": "$199"},
            },
        ]
        
        tenant_id = "test-tenant-123"
        results = await helper.search_by_specific_attribute(
            tenant_id=tenant_id,
            attribute="price",
            limit=10,
        )
        
        assert len(results) == 2
        assert results[0].title == "Tool A"
        assert results[1].title == "Tool B"
        mock_db_client.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_products(self, helper, mock_db_client):
        """Test counting products"""
        mock_db_client.fetchval.return_value = 42
        
        count = await helper.count_products_in_category(
            tenant_id="test-tenant",
            category="ai_tools",
        )
        
        assert count == 42
        mock_db_client.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_comparison_attributes(self, helper, mock_db_client):
        """Test searching products for comparison"""
        mock_db_client.fetch.side_effect = [
            [
                {
                    "id": "1",
                    "product_id": "tool_a",
                    "title": "Tool A",
                    "description": "AI Tool A",
                    "metadata": {},
                }
            ],
            [
                {
                    "id": "2",
                    "product_id": "tool_b",
                    "title": "Tool B",
                    "description": "AI Tool B",
                    "metadata": {},
                }
            ],
        ]
        
        results = await helper.search_by_comparison_attributes(
            tenant_id="test-tenant",
            product_names=["Tool A", "Tool B"],
        )
        
        assert len(results) == 2
        assert "Tool A" in results
        assert "Tool B" in results
    
    def test_build_attribute_query_price(self, helper):
        """Test SQL query building for price attribute"""
        query = helper._build_attribute_query(
            tenant_id="test",
            attribute="price",
            limit=10,
        )
        
        assert "price" in query.lower()
        assert "products" in query.lower()
        assert "test" in query
    
    def test_build_attribute_query_free(self, helper):
        """Test SQL query building for free attribute"""
        query = helper._build_attribute_query(
            tenant_id="test",
            attribute="free",
            limit=10,
        )
        
        assert "is_free" in query or "free" in query
        assert "test" in query


# ============================================================================
# Test CatalogKnowledgeEngine with Hybrid Search
# ============================================================================

class TestCatalogKnowledgeEngine:
    """Test suite for CatalogKnowledgeEngine with Hybrid Search"""
    
    @pytest.fixture
    def mock_retriever(self):
        """Mock retriever"""
        retriever = AsyncMock()
        return retriever
    
    @pytest.fixture
    def mock_classifier(self):
        """Mock intent classifier"""
        classifier = AsyncMock()
        return classifier
    
    @pytest.fixture
    def mock_hybrid_helper(self):
        """Mock hybrid search helper"""
        helper = AsyncMock()
        return helper
    
    @pytest.fixture
    def mock_ai_provider(self):
        """Mock AI provider"""
        provider = AsyncMock()
        return provider
    
    @pytest.fixture
    def engine(self, mock_retriever, mock_classifier, mock_hybrid_helper, mock_ai_provider):
        """Create engine instance with mocks"""
        engine = CatalogKnowledgeEngine(
            retriever=mock_retriever,
            intent_classifier=mock_classifier,
            hybrid_helper=mock_hybrid_helper,
            ai_provider=mock_ai_provider,
            enable_intent_classifier=True,
        )
        return engine
    
    def create_mock_product(self, product_id: str, title: str, score: float = 0.8) -> RetrievedProduct:
        """Helper to create mock product"""
        return RetrievedProduct(
            product_id=product_id,
            title=title,
            description=f"Description of {title}",
            score=score,
            metadata={"tags": ["tag1", "tag2"]},
        )
    
    @pytest.mark.asyncio
    async def test_answer_generic_search(self, engine, mock_retriever, mock_classifier, mock_ai_provider):
        """Test answering generic product search"""
        # Setup mocks
        mock_classifier.classify.return_value = ClassificationResult(
            intent_type=CatalogIntentType.PRODUCT_SEARCH,
            confidence=0.9,
            reason="Generic search",
            extracted_info={},
        )
        
        mock_retriever.retrieve_with_context.return_value = [
            self.create_mock_product("1", "Tool A", 0.95),
            self.create_mock_product("2", "Tool B", 0.85),
        ]
        
        mock_ai_provider.chat.return_value = "Tool A và Tool B là những lựa chọn tốt."
        
        # Execute
        request = KnowledgeRequest(
            question="Công cụ nào tốt?",
            domain="catalog",
            context={"tenant_id": "test-tenant"},
            trace_id="trace-123",
        )
        
        response = await engine.answer(request, tenant_id="test-tenant")
        
        # Assertions
        assert response.answer is not None
        assert response.confidence > 0.0
        assert len(response.citations) == 2
        assert response.metadata["products_found"] == 2
    
    @pytest.mark.asyncio
    async def test_answer_specific_info_query(
        self, engine, mock_classifier, mock_hybrid_helper, mock_ai_provider
    ):
        """Test answering specific attribute query with hybrid search"""
        # Setup mocks
        mock_classifier.classify.return_value = ClassificationResult(
            intent_type=CatalogIntentType.PRODUCT_SPECIFIC_INFO,
            confidence=0.92,
            reason="Asking about price",
            extracted_info={"attribute": "price"},
        )
        
        mock_hybrid_helper.search_by_specific_attribute.return_value = [
            self.create_mock_product("1", "Cheap Tool", 1.0),
            self.create_mock_product("2", "Affordable Tool", 1.0),
        ]
        
        mock_ai_provider.chat.return_value = "Giá của công cụ từ $99 đến $199."
        
        # Execute
        request = KnowledgeRequest(
            question="Giá bao nhiêu?",
            domain="catalog",
            context={"tenant_id": "test-tenant"},
            trace_id="trace-123",
        )
        
        response = await engine.answer(request, tenant_id="test-tenant")
        
        # Assertions
        assert response.answer is not None
        assert response.metadata["intent_type"] == "PRODUCT_SPECIFIC_INFO"
        assert response.metadata["retrieval_method"] == "hybrid_search"
        mock_hybrid_helper.search_by_specific_attribute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_products_found(self, engine, mock_retriever, mock_classifier):
        """Test handling when no products found"""
        mock_classifier.classify.return_value = ClassificationResult(
            intent_type=CatalogIntentType.PRODUCT_SEARCH,
            confidence=0.8,
            reason="Generic search",
            extracted_info={},
        )
        
        mock_retriever.retrieve_with_context.return_value = []
        
        # Execute
        request = KnowledgeRequest(
            question="Tìm sản phẩm không tồn tại",
            domain="catalog",
            context={"tenant_id": "test-tenant"},
            trace_id="trace-123",
        )
        
        response = await engine.answer(request, tenant_id="test-tenant")
        
        # Assertions
        assert response.answer is not None
        assert "không tìm thấy" in response.answer.lower()
        assert response.confidence == 0.0
        assert response.metadata["products_found"] == 0
    
    def test_merge_results_deduplication(self, engine):
        """Test merging and deduplicating results"""
        db_results = [
            self.create_mock_product("1", "Tool A", 1.0),
            self.create_mock_product("2", "Tool B", 1.0),
        ]
        
        vector_results = [
            self.create_mock_product("2", "Tool B", 0.9),  # Duplicate
            self.create_mock_product("3", "Tool C", 0.8),
        ]
        
        merged = engine._merge_results(db_results, vector_results, max_results=3)
        
        assert len(merged) == 3
        # Check that no duplicates exist
        product_ids = [p.product_id for p in merged]
        assert len(product_ids) == len(set(product_ids))


# ============================================================================
# Integration Tests
# ============================================================================

class TestCatalogDomainIntegration:
    """Integration tests for catalog domain components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_product_search_flow(self):
        """Test complete flow from intent classification to answer generation"""
        # This would require more setup but shows the pattern
        pass
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_fallback(self):
        """Test hybrid search with fallback to vector search"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

