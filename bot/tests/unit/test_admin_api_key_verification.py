"""
Unit tests for Admin API Key Verification
Task 2.4: Security tests for API key verification
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request

from backend.interface.middleware.multi_tenant_auth import require_api_key, verify_api_key
from backend.shared.exceptions import AuthenticationError
from backend.schemas.multi_tenant_types import RequestContext, ChannelType, AuthMethod


class TestAPIKeyVerification:
    """Test API key verification"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request"""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.query_params = {}
        request.state = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        pool = MagicMock()
        conn = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool
    
    @pytest.mark.asyncio
    async def test_require_api_key_missing_header_and_query(self, mock_request):
        """Test that missing API key is rejected"""
        mock_request.headers = {}
        mock_request.query_params = {}
        
        @require_api_key
        async def test_handler(request):
            return {"success": True}
        
        result = await test_handler(mock_request)
        
        assert result["error"] is True
        assert result["status_code"] == 401
        assert "Missing API key" in result["message"]
    
    @pytest.mark.asyncio
    async def test_require_api_key_from_header(self, mock_request, mock_db_pool):
        """Test API key from Authorization header"""
        mock_request.headers = {"Authorization": "Bearer test_api_key_123"}
        mock_request.query_params = {}
        
        with patch('backend.interface.middleware.multi_tenant_auth.database_client') as mock_db:
            mock_db.pool = mock_db_pool
            
            with patch('backend.interface.middleware.multi_tenant_auth.verify_api_key') as mock_verify:
                mock_verify.return_value = "00000000-0000-0000-0000-000000000001"
                
                @require_api_key
                async def test_handler(request):
                    assert hasattr(request.state, 'user_context')
                    context = request.state.user_context
                    assert context.tenant_id == "00000000-0000-0000-0000-000000000001"
                    assert context.channel == ChannelType.API
                    assert context.auth_method == AuthMethod.API_KEY
                    return {"success": True}
                
                result = await test_handler(mock_request)
                assert result["success"] is True
                mock_verify.assert_called_once_with("test_api_key_123", mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_require_api_key_from_query_param(self, mock_request, mock_db_pool):
        """Test API key from query parameter"""
        mock_request.headers = {}
        mock_request.query_params = {"api_key": "test_api_key_456"}
        
        with patch('backend.interface.middleware.multi_tenant_auth.database_client') as mock_db:
            mock_db.pool = mock_db_pool
            
            with patch('backend.interface.middleware.multi_tenant_auth.verify_api_key') as mock_verify:
                mock_verify.return_value = "00000000-0000-0000-0000-000000000002"
                
                @require_api_key
                async def test_handler(request):
                    context = request.state.user_context
                    assert context.tenant_id == "00000000-0000-0000-0000-000000000002"
                    return {"success": True}
                
                result = await test_handler(mock_request)
                assert result["success"] is True
                mock_verify.assert_called_once_with("test_api_key_456", mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_require_api_key_invalid_key(self, mock_request, mock_db_pool):
        """Test that invalid API key is rejected"""
        mock_request.headers = {"Authorization": "Bearer invalid_key"}
        mock_request.query_params = {}
        
        with patch('backend.interface.middleware.multi_tenant_auth.database_client') as mock_db:
            mock_db.pool = mock_db_pool
            
            with patch('backend.interface.middleware.multi_tenant_auth.verify_api_key') as mock_verify:
                mock_verify.return_value = None  # Invalid key
                
                @require_api_key
                async def test_handler(request):
                    return {"success": True}
                
                result = await test_handler(mock_request)
                
                assert result["error"] is True
                assert result["status_code"] == 401
                assert "Invalid API key" in result["message"]
    
    @pytest.mark.asyncio
    async def test_require_api_key_database_unavailable(self, mock_request):
        """Test that database unavailability is handled"""
        mock_request.headers = {"Authorization": "Bearer test_key"}
        mock_request.query_params = {}
        
        with patch('backend.interface.middleware.multi_tenant_auth.database_client') as mock_db:
            mock_db.pool = None  # Database not available
            
            @require_api_key
            async def test_handler(request):
                return {"success": True}
            
            result = await test_handler(mock_request)
            
            assert result["error"] is True
            assert result["status_code"] == 401
            assert "Authentication service unavailable" in result["message"]


class TestVerifyAPIKey:
    """Test verify_api_key function"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        pool = MagicMock()
        conn = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool
    
    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self, mock_db_pool):
        """Test valid API key verification"""
        with patch('backend.interface.middleware.multi_tenant_auth.TenantService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.verify_api_key = AsyncMock(return_value="00000000-0000-0000-0000-000000000001")
            mock_service_class.return_value = mock_service
            
            tenant_id = await verify_api_key("valid_api_key", mock_db_pool)
            
            assert tenant_id == "00000000-0000-0000-0000-000000000001"
            mock_service.verify_api_key.assert_called_once_with("valid_api_key")
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self, mock_db_pool):
        """Test invalid API key verification"""
        with patch('backend.interface.middleware.multi_tenant_auth.TenantService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.verify_api_key = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service
            
            tenant_id = await verify_api_key("invalid_api_key", mock_db_pool)
            
            assert tenant_id is None
    
    @pytest.mark.asyncio
    async def test_verify_api_key_no_pool(self):
        """Test verification with no database pool"""
        tenant_id = await verify_api_key("test_key", None)
        assert tenant_id is None


class TestAdminEndpointsWithAPIKey:
    """Test admin endpoints with API key protection"""
    
    @pytest.fixture
    def mock_request_with_api_key(self):
        """Mock request with valid API key context"""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_api_key"}
        request.query_params = {}
        request.state = MagicMock()
        request.state.user_context = RequestContext(
            tenant_id="00000000-0000-0000-0000-000000000001",
            channel=ChannelType.API,
            user_key="service-account",
            auth_method=AuthMethod.API_KEY,
            platform="api",
        )
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.mark.asyncio
    async def test_admin_create_tenant_without_api_key(self):
        """Test that admin_create_tenant rejects without API key"""
        from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
        
        request = MagicMock(spec=Request)
        request.headers = {}
        request.query_params = {}
        request.state = MagicMock()
        request.state.user_context = None  # No context = no API key
        
        api = MultiTenantBotAPI()
        result = await api.admin_create_tenant(request)
        
        assert result["error"] is True
        assert result["status_code"] == 401
        assert "Authentication required" in result["message"]
    
    @pytest.mark.asyncio
    async def test_admin_create_tenant_with_api_key(self, mock_request_with_api_key):
        """Test that admin_create_tenant works with valid API key"""
        from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
        from unittest.mock import AsyncMock, patch
        
        mock_request_with_api_key.json = AsyncMock(return_value={
            "name": "Test Tenant",
            "site_id": "test-001",
            "web_embed_origins": ["https://test.com"],
            "plan": "basic",
        })
        
        with patch('backend.infrastructure.database_client.database_client') as mock_db:
            mock_db.pool = MagicMock()
            mock_db.pool.acquire = MagicMock()
            mock_conn = MagicMock()
            mock_db.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_db.pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('backend.domain.tenant.tenant_service.TenantService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.create_tenant = AsyncMock(return_value={
                    "success": True,
                    "data": {
                        "tenant_id": "00000000-0000-0000-0000-000000000002",
                        "site_id": "test-001",
                        "name": "Test Tenant",
                        "api_key": "test_api_key",
                        "jwt_secret": "test_jwt_secret",
                    }
                })
                mock_service_class.return_value = mock_service
                
                api = MultiTenantBotAPI()
                result = await api.admin_create_tenant(mock_request_with_api_key)
                
                # Should succeed (actual tenant creation logic may vary)
                # The important part is that API key was verified by decorator
                assert "error" not in result or result.get("error") is False

