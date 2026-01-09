"""
Integration tests for LLM classifier (fallback)
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.router.steps.llm_step import LLMClassifierStep
from backend.schemas import SessionState
from backend.infrastructure.ai_provider import AIProvider


@pytest.fixture
def llm_step():
    """Create LLM classifier step"""
    return LLMClassifierStep()


@pytest.fixture
def sample_session():
    """Create sample session"""
    return SessionState(
        session_id=str(uuid4()),
        user_id=str(uuid4()),
        last_domain=None,
        slots_memory={},
    )


class TestLLMClassifier:
    """Test LLM-based fallback classification"""
    
    @pytest.mark.asyncio
    async def test_hr_leave_request(self, llm_step, sample_session):
        """Test LLM classification of leave request"""
        message = "Tôi muốn xin phép từ ngày 1/2 đến 5/2"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
        # LLM should classify this
        if result["classified"]:
            assert result["domain"] == "hr"
            assert result["intent"] in [
                "create_leave_request",
                "query_leave_balance"
            ]
            assert result["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_hr_leave_balance_query(self, llm_step, sample_session):
        """Test LLM classification of leave balance query"""
        message = "Bao nhiêu ngày phép còn lại?"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "hr"
            assert result["intent"] == "query_leave_balance"
    
    @pytest.mark.asyncio
    async def test_catalog_product_search(self, llm_step, sample_session):
        """Test LLM classification of product search"""
        message = "Tôi cần tìm sản phẩm điện thoại tốt"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "catalog"
    
    @pytest.mark.asyncio
    async def test_ambiguous_intent(self, llm_step, sample_session):
        """Test LLM handling ambiguous intent"""
        message = "Xin chào"  # Generic greeting
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
        # LLM should decide whether to classify or not
    
    @pytest.mark.asyncio
    async def test_low_confidence(self, llm_step, sample_session):
        """Test LLM handling low confidence"""
        message = "xyz abc def"  # Gibberish
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
        if result["classified"]:
            # Should be below threshold
            assert result["confidence"] < 0.65
    
    @pytest.mark.asyncio
    async def test_response_structure(self, llm_step, sample_session):
        """Test LLM response structure"""
        message = "Tôi muốn xin phép"
        
        result = await llm_step.execute(message, sample_session)
        
        # Verify response has required fields
        assert "classified" in result
        assert "reason" in result or ("domain" in result and "intent" in result)
        
        if result["classified"]:
            assert "domain" in result
            assert "intent" in result
            assert "confidence" in result
            assert 0 <= result["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_vietnamese_language(self, llm_step, sample_session):
        """Test LLM with Vietnamese language"""
        messages = [
            "Tôi muốn xin phép",
            "Bao nhiêu ngày phép?",
            "Tìm sản phẩm nào đó",
            "Xin chào",
        ]
        
        for message in messages:
            result = await llm_step.execute(message, sample_session)
            assert "classified" in result


class TestLLMClassifierEdgeCases:
    """Test LLM classifier edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_message(self, llm_step, sample_session):
        """Test LLM with empty message"""
        message = ""
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, llm_step, sample_session):
        """Test LLM with very long message"""
        message = "Tôi muốn xin phép " * 50  # Long message
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_special_characters(self, llm_step, sample_session):
        """Test LLM with special characters"""
        message = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_mixed_language(self, llm_step, sample_session):
        """Test LLM with mixed Vietnamese and English"""
        message = "I want to xin phép please"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_numbers_only(self, llm_step, sample_session):
        """Test LLM with numbers only"""
        message = "123 456 789"
        
        result = await llm_step.execute(message, sample_session)
        
        assert "classified" in result


class TestLLMClassifierSessionContext:
    """Test LLM classifier with session context"""
    
    @pytest.mark.asyncio
    async def test_with_previous_domain(self, llm_step):
        """Test LLM classification with previous domain in session"""
        session = SessionState(
            session_id=str(uuid4()),
            user_id=str(uuid4()),
            last_domain="hr",
            slots_memory={"previous_intent": "query_leave_balance"},
        )
        
        message = "và anh ấy?"  # Follow-up question
        result = await llm_step.execute(message, session)
        
        assert "classified" in result
    
    @pytest.mark.asyncio
    async def test_with_conversation_context(self, llm_step):
        """Test LLM classification with conversation context"""
        session = SessionState(
            session_id=str(uuid4()),
            user_id=str(uuid4()),
            last_domain="hr",
            slots_memory={
                "previous_intent": "query_leave_balance",
                "user_type": "employee",
                "department": "engineering"
            },
        )
        
        message = "Tôi muốn xin phép"
        result = await llm_step.execute(message, session)
        
        assert "classified" in result
        if result["classified"]:
            assert result["domain"] == "hr"

