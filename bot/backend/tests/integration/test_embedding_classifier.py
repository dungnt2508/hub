"""
Integration tests for embedding classifier
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.router.steps.embedding_step import EmbeddingClassifierStep
from backend.infrastructure.ai_provider import AIProvider
from backend.infrastructure.intent_store import IntentStore
from backend.infrastructure.embedding_scorer import EmbeddingScorer


@pytest.fixture
def embedding_step():
    """Create embedding classifier step"""
    return EmbeddingClassifierStep()


class TestEmbeddingClassifier:
    """Test embedding-based intent classification"""
    
    @pytest.mark.asyncio
    async def test_hr_intent_classification(self, embedding_step):
        """Test classification of HR-related message"""
        message = "Tôi muốn xin phép"  # "I want to request leave"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        # Should classify successfully or return not classified
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "hr"
            assert result["intent"] in [
                "create_leave_request",
                "query_leave_balance",
                "approve_leave"
            ]
            assert 0 <= result["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_leave_balance_query(self, embedding_step):
        """Test classification of leave balance query"""
        message = "Tôi còn bao nhiêu ngày phép?"  # "How many leave days do I have?"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "hr"
            assert result["intent"] == "query_leave_balance"
    
    @pytest.mark.asyncio
    async def test_catalog_search(self, embedding_step):
        """Test classification of catalog search"""
        message = "Tìm sản phẩm X cho tôi"  # "Find product X for me"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "catalog"
            assert result["intent"] in ["catalog.search", "catalog.recommend"]
    
    @pytest.mark.asyncio
    async def test_unknown_intent(self, embedding_step):
        """Test classification of unknown intent"""
        message = "xyz abcdef ghijkl"  # Gibberish
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        # Should return not classified or UNKNOWN
        assert "classified" in result
        if result["classified"]:
            assert result["intent"] is not None
    
    @pytest.mark.asyncio
    async def test_with_keyword_boost(self, embedding_step):
        """Test classification with keyword boost"""
        message = "Tôi muốn xin phép"
        boost = {"hr": 0.5, "leave": 0.3}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        # Boost should improve confidence
        if result["classified"]:
            assert result["confidence"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_empty_message(self, embedding_step):
        """Test classification of empty message"""
        message = ""
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        assert result["classified"] is False
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, embedding_step):
        """Test classification of very long message"""
        message = "Tôi muốn xin phép " * 100  # Repeated message
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        # Should still process long messages
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self, embedding_step):
        """Test confidence threshold checking"""
        # Message clearly related to leave
        message = "Xin phép, xin nghỉ, phép năm"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
        if result["classified"]:
            # Confidence should be high for clear intent
            assert result["confidence"] > 0.7
    
    @pytest.mark.asyncio
    async def test_response_structure(self, embedding_step):
        """Test response structure"""
        message = "Tôi muốn xin phép"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        # Verify response structure
        assert "classified" in result
        assert isinstance(result["classified"], bool)
        
        if result["classified"]:
            assert "domain" in result
            assert "intent" in result
            assert "confidence" in result
            assert "source" in result
            assert result["source"] == "EMBEDDING"


class TestEmbeddingClassifierEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_special_characters(self, embedding_step):
        """Test message with special characters"""
        message = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_mixed_language(self, embedding_step):
        """Test message with mixed Vietnamese and English"""
        message = "Tôi want to xin phép"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_repeated_words(self, embedding_step):
        """Test message with repeated words"""
        message = "phép phép phép phép phép"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_numbers_only(self, embedding_step):
        """Test message with only numbers"""
        message = "123 456 789"
        boost = {}
        
        result = await embedding_step.execute(message, boost)
        
        assert "classified" in result

