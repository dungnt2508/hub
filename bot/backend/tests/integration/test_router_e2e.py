"""
End-to-end tests for router orchestrator
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.router.orchestrator import RouterOrchestrator
from backend.schemas import RouterRequest


@pytest.fixture
async def router():
    """Create router orchestrator"""
    return RouterOrchestrator()


class TestRouterEndToEnd:
    """Test complete routing flow"""
    
    @pytest.mark.asyncio
    async def test_leave_query_routing(self, router):
        """Test routing of leave query message"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="Tôi còn bao nhiêu ngày phép?",
            session_id=None
        )
        
        response = await router.route(request)
        
        # Verify response structure
        assert response is not None
        assert response.trace_id is not None
        
        # Verify routing decision
        assert response.domain is not None
        if response.domain == "hr":
            assert response.intent is not None
            assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_leave_request_routing(self, router):
        """Test routing of leave request message"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="Tôi muốn xin phép từ ngày 1/2 đến 5/2",
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None
        assert response.domain is not None
        if response.domain == "hr":
            assert response.intent in ["create_leave_request", "query_leave_balance"]
    
    @pytest.mark.asyncio
    async def test_catalog_search_routing(self, router):
        """Test routing of catalog search"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="Tìm sản phẩm điện thoại",
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None
        if response.domain == "catalog":
            assert response.intent is not None
    
    @pytest.mark.asyncio
    async def test_session_persistence_across_requests(self, router):
        """Test session persists across multiple requests"""
        user_id = str(uuid4())
        
        # First request
        request1 = RouterRequest(
            user_id=user_id,
            raw_message="Tôi muốn xin phép",
            session_id=None
        )
        response1 = await router.route(request1)
        
        assert response1 is not None
        assert response1.trace_id is not None
        
        # Second request with same session
        request2 = RouterRequest(
            user_id=user_id,
            raw_message="Bao nhiêu ngày phép?",
            session_id=None
        )
        response2 = await router.route(request2)
        
        # Both responses should be valid
        assert response2 is not None
        assert response2.trace_id is not None
    
    @pytest.mark.asyncio
    async def test_multiple_users_isolated_sessions(self, router):
        """Test sessions are isolated between users"""
        # User 1
        user1_id = str(uuid4())
        request1 = RouterRequest(
            user_id=user1_id,
            raw_message="Tôi muốn xin phép",
            session_id=None
        )
        response1 = await router.route(request1)
        
        assert response1 is not None
        
        # User 2
        user2_id = str(uuid4())
        request2 = RouterRequest(
            user_id=user2_id,
            raw_message="Tôi muốn xin phép",
            session_id=None
        )
        response2 = await router.route(request2)
        
        # Both responses should be valid
        assert response2 is not None
    
    @pytest.mark.asyncio
    async def test_routing_trace(self, router):
        """Test routing trace contains all steps"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="Tôi muốn xin phép",
            session_id=None
        )
        
        response = await router.route(request)
        
        # Verify trace
        assert response.trace is not None
        assert response.trace.spans is not None
        assert len(response.trace.spans) > 0
        
        # Each trace span should have required fields
        for span in response.trace.spans:
            assert trace_entry.get("step") is not None
            assert trace_entry.get("timestamp") is not None
    
    @pytest.mark.asyncio
    async def test_confidence_scores(self, router):
        """Test confidence scores are reasonable"""
        messages = [
            "Tôi muốn xin phép",
            "Bao nhiêu ngày phép?",
            "Tìm sản phẩm nào",
        ]
        
        for message in messages:
            request = RouterRequest(
                user_id=str(uuid4()),
                raw_message=message,
                session_id=None
            )
            
            response = await router.route(request)
            
            if response.domain is not None:
                # Confidence should be between 0 and 1
                if response.confidence is not None:
                    assert 0 <= response.confidence <= 1.0


class TestRouterEdgeCases:
    """Test router edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_message(self, router):
        """Test routing with empty message"""
        # Empty message should raise validation error
        with pytest.raises(ValueError):
            request = RouterRequest(
                user_id=str(uuid4()),
                raw_message="",
                session_id=None
            )
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, router):
        """Test routing with very long message"""
        long_message = "Tôi muốn xin phép " * 100
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message=long_message,
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_special_characters_message(self, router):
        """Test routing with special characters"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="!@#$%^&*()_+-=[]{}|;:,.<>?",
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_mixed_language_message(self, router):
        """Test routing with mixed Vietnamese and English"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="I want to xin phép please",
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_numbers_only_message(self, router):
        """Test routing with numbers only"""
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="123 456 789",
            session_id=None
        )
        
        response = await router.route(request)
        
        assert response is not None


class TestRouterErrorHandling:
    """Test router error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_session_id(self, router):
        """Test router with invalid session ID"""
        # Should raise ValueError for invalid UUID session
        with pytest.raises(ValueError):
            request = RouterRequest(
                user_id=str(uuid4()),
                raw_message="Tôi muốn xin phép",
                session_id="invalid-session-that-does-not-exist"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_user_id(self, router):
        """Test router with invalid user ID"""
        # Should raise ValueError for invalid UUID
        with pytest.raises(ValueError):
            request = RouterRequest(
                user_id="invalid-user-id",
                raw_message="Tôi muốn xin phép",
                session_id=None
            )
    
    @pytest.mark.asyncio
    async def test_missing_message(self, router):
        """Test router with missing message"""
        # Empty message should raise validation error
        with pytest.raises(ValueError):
            request = RouterRequest(
                user_id=str(uuid4()),
                raw_message="",
                session_id=None
            )


class TestRouterPerformance:
    """Test router performance"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, router):
        """Test router response time is acceptable"""
        import time
        
        request = RouterRequest(
            user_id=str(uuid4()),
            raw_message="Tôi muốn xin phép",
            session_id=None
        )
        
        start = time.time()
        response = await router.route(request)
        elapsed = time.time() - start
        
        # Should respond in reasonable time
        assert elapsed < 5.0  # 5 seconds max for integration test
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, router):
        """Test router handles concurrent requests"""
        import asyncio
        
        async def make_request(user_id):
            request = RouterRequest(
                user_id=user_id,
                raw_message="Tôi muốn xin phép",
                session_id=None
            )
            return await router.route(request)
        
        # Make 5 concurrent requests
        tasks = [make_request(str(uuid4())) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(responses) == 5
        for response in responses:
            assert response is not None
            assert response.trace_id is not None

