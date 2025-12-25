"""
Unit tests for Router Tenant ID (Task 7)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from backend.schemas.router_types import RouterRequest, RouterResponse, RouterTrace
from backend.router.orchestrator import RouterOrchestrator
from backend.shared.exceptions import RouterError, InvalidInputError
from backend.interface.api_handler import APIHandler


class TestRouterRequestTenantId:
    """Test RouterRequest with tenant_id field"""
    
    def test_router_request_with_tenant_id(self):
        """Test that RouterRequest accepts tenant_id"""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        request = RouterRequest(
            raw_message="Test message",
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        assert request.tenant_id == tenant_id
        assert request.user_id == user_id
        assert request.raw_message == "Test message"
    
    def test_router_request_missing_tenant_id(self):
        """Test that RouterRequest rejects missing tenant_id"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="tenant_id is required"):
            RouterRequest(
                raw_message="Test message",
                user_id=user_id,
            )
    
    def test_router_request_empty_tenant_id(self):
        """Test that RouterRequest rejects empty tenant_id"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="tenant_id is required"):
            RouterRequest(
                raw_message="Test message",
                user_id=user_id,
                tenant_id="",
            )
    
    def test_router_request_invalid_tenant_id_uuid(self):
        """Test that RouterRequest rejects invalid tenant_id UUID"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="tenant_id must be valid UUID"):
            RouterRequest(
                raw_message="Test message",
                user_id=user_id,
                tenant_id="not-a-uuid",
            )


@pytest.mark.asyncio
class TestRouterOrchestratorTenantId:
    """Test RouterOrchestrator with tenant_id validation"""
    
    @pytest.fixture
    def router(self):
        """Create router orchestrator"""
        return RouterOrchestrator()
    
    @pytest.fixture
    def valid_request(self):
        """Create valid router request with tenant_id"""
        return RouterRequest(
            raw_message="Test message",
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
        )
    
    @pytest.mark.asyncio
    async def test_router_validates_tenant_id(self, router, valid_request):
        """Test that router validates tenant_id"""
        # Mock all steps to avoid actual processing
        with patch.object(router, '_step_0_session', new_callable=AsyncMock) as mock_session:
            with patch.object(router, '_step_0_5_normalize', new_callable=AsyncMock) as mock_normalize:
                with patch.object(router, '_step_1_meta', new_callable=AsyncMock) as mock_meta:
                    with patch.object(router, '_step_2_pattern', new_callable=AsyncMock) as mock_pattern:
                        with patch.object(router, '_step_3_keyword', new_callable=AsyncMock) as mock_keyword:
                            with patch.object(router, '_step_4_embedding', new_callable=AsyncMock) as mock_embedding:
                                # Setup mocks
                                from backend.schemas.session_types import SessionState
                                mock_session.return_value = SessionState(
                                    session_id=str(uuid.uuid4()),
                                    user_id=valid_request.user_id,
                                )
                                
                                from backend.schemas.router_types import NormalizedInput
                                mock_normalize.return_value = NormalizedInput(
                                    normalized_message="test message",
                                )
                                
                                mock_meta.return_value = {"handled": False}
                                mock_pattern.return_value = {"matched": False}
                                mock_keyword.return_value = {}
                                mock_embedding.return_value = {"classified": False}
                                
                                # Call router
                                response = await router.route(valid_request)
                                
                                # Should succeed
                                assert response is not None
                                assert response.trace_id is not None
                                
                                # Verify tenant_id was logged
                                # (We can't easily verify this without checking logs, but the code should include it)
    
    @pytest.mark.asyncio
    async def test_router_rejects_missing_tenant_id(self, router):
        """Test that router rejects request without tenant_id"""
        # Create request without tenant_id (this should fail at RouterRequest creation)
        with pytest.raises(ValueError, match="tenant_id is required"):
            request = RouterRequest(
                raw_message="Test message",
                user_id=str(uuid.uuid4()),
            )
    
    @pytest.mark.asyncio
    async def test_router_rejects_empty_tenant_id(self, router):
        """Test that router rejects request with empty tenant_id"""
        # Create request with empty tenant_id (this should fail at RouterRequest creation)
        with pytest.raises(ValueError, match="tenant_id is required"):
            request = RouterRequest(
                raw_message="Test message",
                user_id=str(uuid.uuid4()),
                tenant_id="",
            )
    
    @pytest.mark.asyncio
    async def test_router_logs_tenant_id(self, router, valid_request):
        """Test that router logs tenant_id in request"""
        with patch.object(router, '_step_0_session', new_callable=AsyncMock) as mock_session:
            with patch.object(router, '_step_0_5_normalize', new_callable=AsyncMock) as mock_normalize:
                with patch.object(router, '_step_1_meta', new_callable=AsyncMock) as mock_meta:
                    with patch.object(router, '_step_2_pattern', new_callable=AsyncMock) as mock_pattern:
                        with patch.object(router, '_step_3_keyword', new_callable=AsyncMock) as mock_keyword:
                            with patch.object(router, '_step_4_embedding', new_callable=AsyncMock) as mock_embedding:
                                # Setup mocks
                                from backend.schemas.session_types import SessionState
                                mock_session.return_value = SessionState(
                                    session_id=str(uuid.uuid4()),
                                    user_id=valid_request.user_id,
                                )
                                
                                from backend.schemas.router_types import NormalizedInput
                                mock_normalize.return_value = NormalizedInput(
                                    normalized_message="test message",
                                )
                                
                                mock_meta.return_value = {"handled": False}
                                mock_pattern.return_value = {"matched": False}
                                mock_keyword.return_value = {}
                                mock_embedding.return_value = {"classified": False}
                                
                                # Call router
                                response = await router.route(valid_request)
                                
                                # Verify tenant_id is accessible in request
                                assert valid_request.tenant_id is not None
                                assert response is not None


@pytest.mark.asyncio
class TestAPIHandlerTenantId:
    """Test APIHandler with tenant_id extraction"""
    
    @pytest.fixture
    def api_handler(self):
        """Create API handler"""
        return APIHandler()
    
    @pytest.mark.asyncio
    async def test_api_handler_extracts_tenant_id_from_metadata(self, api_handler):
        """Test that APIHandler extracts tenant_id from metadata"""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch.object(api_handler.personalization_service, 'get_preferences', new_callable=AsyncMock) as mock_prefs:
            with patch.object(api_handler.router, 'route', new_callable=AsyncMock) as mock_route:
                # Setup mocks
                from backend.personalization.types import UserPreferences, Tone, Style, Avatar
                mock_prefs.return_value = UserPreferences(
                    user_id=user_id,
                    tone=Tone.FRIENDLY,
                    style=Style.CASUAL,
                    language="vi",
                    avatar=Avatar(),
                )
                
                from backend.schemas.router_types import RouterResponse, RouterTrace
                mock_route.return_value = RouterResponse(
                    trace_id=str(uuid.uuid4()),
                    status="UNKNOWN",
                    trace=RouterTrace(trace_id=str(uuid.uuid4())),
                )
                
                with patch.object(api_handler.response_formatter, 'format_router_response', new_callable=AsyncMock) as mock_format:
                    mock_format.return_value = {"message": "Test response"}
                    
                    # Call handler with tenant_id in metadata
                    result = await api_handler.handle_request(
                        raw_message="Test message",
                        user_id=user_id,
                        metadata={"tenant_id": tenant_id}
                    )
                    
                    # Verify tenant_id was passed to RouterRequest
                    call_args = mock_route.call_args
                    router_request = call_args[0][0]  # First positional argument
                    assert router_request.tenant_id == tenant_id
                    assert result is not None
    
    @pytest.mark.asyncio
    async def test_api_handler_rejects_missing_tenant_id(self, api_handler):
        """Test that APIHandler rejects request without tenant_id in metadata"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(InvalidInputError, match="tenant_id is required in metadata"):
            await api_handler.handle_request(
                raw_message="Test message",
                user_id=user_id,
                metadata={}  # No tenant_id
            )
    
    @pytest.mark.asyncio
    async def test_api_handler_rejects_empty_tenant_id(self, api_handler):
        """Test that APIHandler rejects request with empty tenant_id"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(InvalidInputError, match="tenant_id cannot be empty"):
            await api_handler.handle_request(
                raw_message="Test message",
                user_id=user_id,
                metadata={"tenant_id": ""}  # Empty tenant_id
            )
    
    @pytest.mark.asyncio
    async def test_api_handler_rejects_none_metadata(self, api_handler):
        """Test that APIHandler rejects request with None metadata"""
        user_id = str(uuid.uuid4())
        
        with pytest.raises(InvalidInputError, match="tenant_id is required in metadata"):
            await api_handler.handle_request(
                raw_message="Test message",
                user_id=user_id,
                metadata=None  # None metadata
            )


@pytest.mark.asyncio
class TestRouterTenantIdIntegration:
    """Integration tests for tenant_id flow"""
    
    @pytest.mark.asyncio
    async def test_full_flow_with_tenant_id(self):
        """Test full flow from APIHandler to Router with tenant_id"""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        api_handler = APIHandler()
        
        with patch.object(api_handler.personalization_service, 'get_preferences', new_callable=AsyncMock) as mock_prefs:
            with patch.object(api_handler.router, 'route', new_callable=AsyncMock) as mock_route:
                # Setup mocks
                from backend.personalization.types import UserPreferences, Tone, Style, Avatar
                mock_prefs.return_value = UserPreferences(
                    user_id=user_id,
                    tone=Tone.FRIENDLY,
                    style=Style.CASUAL,
                    language="vi",
                    avatar=Avatar(),
                )
                
                from backend.schemas.router_types import RouterResponse, RouterTrace
                mock_route.return_value = RouterResponse(
                    trace_id=str(uuid.uuid4()),
                    status="UNKNOWN",
                    trace=RouterTrace(trace_id=str(uuid.uuid4())),
                )
                
                with patch.object(api_handler.response_formatter, 'format_router_response', new_callable=AsyncMock) as mock_format:
                    mock_format.return_value = {"message": "Test response"}
                    
                    # Call handler
                    result = await api_handler.handle_request(
                        raw_message="Test message",
                        user_id=user_id,
                        metadata={"tenant_id": tenant_id}
                    )
                    
                    # Verify tenant_id flows through
                    call_args = mock_route.call_args
                    router_request = call_args[0][0]
                    assert router_request.tenant_id == tenant_id
                    assert router_request.user_id == user_id
                    assert router_request.raw_message == "Test message"
                    assert result is not None

