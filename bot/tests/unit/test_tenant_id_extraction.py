"""
Unit tests for Tenant ID Extraction
Task 3.4: Security tests for tenant_id extraction and validation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.shared.auth_config import validate_tenant_id, is_tenant_active
from backend.domain.tenant.tenant_service import TenantService
from backend.shared.exceptions import AuthenticationError


class TestTenantIDValidation:
    """Test tenant_id validation"""
    
    @pytest.mark.asyncio
    async def test_validate_tenant_id_empty(self):
        """Test that empty tenant_id is rejected"""
        result = await validate_tenant_id("")
        assert result is False
        
        result = await validate_tenant_id(None)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_tenant_id_not_found(self):
        """Test that non-existent tenant_id is rejected"""
        with patch('backend.shared.auth_config.is_tenant_active') as mock_is_active:
            mock_is_active.return_value = False
            
            result = await validate_tenant_id("00000000-0000-0000-0000-000000000999")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_tenant_id_valid(self):
        """Test that valid tenant_id passes validation"""
        with patch('backend.shared.auth_config.is_tenant_active') as mock_is_active:
            mock_is_active.return_value = True
            
            result = await validate_tenant_id("00000000-0000-0000-0000-000000000001")
            assert result is True


class TestTelegramTenantIDResolution:
    """Test Telegram bot token to tenant_id resolution"""
    
    @pytest.fixture
    def mock_db_conn(self):
        """Mock database connection"""
        conn = MagicMock()
        return conn
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_id_from_bot_token_valid(self, mock_db_conn):
        """Test valid bot token resolves to tenant_id"""
        mock_row = {
            'id': '00000000-0000-0000-0000-000000000001',
            'is_active': True,
            'telegram_enabled': True,
        }
        mock_db_conn.fetchrow = AsyncMock(return_value=mock_row)
        
        tenant_service = TenantService(mock_db_conn)
        tenant_id = await tenant_service.resolve_tenant_id_from_telegram_bot_token("valid_bot_token")
        
        assert tenant_id == "00000000-0000-0000-0000-000000000001"
        mock_db_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_id_from_bot_token_not_found(self, mock_db_conn):
        """Test invalid bot token returns None"""
        mock_db_conn.fetchrow = AsyncMock(return_value=None)
        
        tenant_service = TenantService(mock_db_conn)
        tenant_id = await tenant_service.resolve_tenant_id_from_telegram_bot_token("invalid_bot_token")
        
        assert tenant_id is None
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_id_from_bot_token_inactive_tenant(self, mock_db_conn):
        """Test inactive tenant returns None"""
        mock_row = {
            'id': '00000000-0000-0000-0000-000000000001',
            'is_active': False,  # Inactive
            'telegram_enabled': True,
        }
        mock_db_conn.fetchrow = AsyncMock(return_value=None)  # Query returns None for inactive
        
        tenant_service = TenantService(mock_db_conn)
        tenant_id = await tenant_service.resolve_tenant_id_from_telegram_bot_token("valid_bot_token")
        
        assert tenant_id is None
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_id_from_bot_token_telegram_disabled(self, mock_db_conn):
        """Test tenant with telegram disabled returns None"""
        mock_row = {
            'id': '00000000-0000-0000-0000-000000000001',
            'is_active': True,
            'telegram_enabled': False,  # Telegram disabled
        }
        mock_db_conn.fetchrow = AsyncMock(return_value=None)  # Query returns None
        
        tenant_service = TenantService(mock_db_conn)
        tenant_id = await tenant_service.resolve_tenant_id_from_telegram_bot_token("valid_bot_token")
        
        assert tenant_id is None


class TestJWTDecoratorTenantIDExtraction:
    """Test require_jwt_auth decorator tenant_id extraction"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request"""
        request = MagicMock()
        request.headers = {
            "Authorization": "Bearer test_token",
            "Origin": "https://example.com"
        }
        request.query_params = {}  # No query param
        request.state = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.mark.asyncio
    async def test_require_jwt_auth_extracts_tenant_id_from_jwt(self, mock_request):
        """Test that tenant_id is extracted from JWT payload, not query param"""
        from backend.interface.middleware.multi_tenant_auth import require_jwt_auth
        
        # Mock JWT payload with tenant_id
        mock_payload = {
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "channel": "web",
            "user_key": "test_user",
            "origin": "https://example.com",
            "exp": 9999999999,
        }
        
        with patch('jwt.decode') as mock_jwt_decode:
            # First call: unverified decode to get tenant_id
            mock_jwt_decode.side_effect = [
                mock_payload,  # Unverified decode
                mock_payload,  # Verified decode in resolve_context_from_jwt
            ]
            
            with patch('backend.interface.middleware.multi_tenant_auth.MultiTenantAuthMiddleware.resolve_context_from_jwt') as mock_resolve:
                mock_context = MagicMock()
                mock_context.tenant_id = "00000000-0000-0000-0000-000000000001"
                mock_resolve.return_value = mock_context
                
                @require_jwt_auth
                async def test_handler(request):
                    assert hasattr(request.state, 'user_context')
                    context = request.state.user_context
                    assert context.tenant_id == "00000000-0000-0000-0000-000000000001"
                    return {"success": True}
                
                result = await test_handler(mock_request)
                
                # Should succeed - tenant_id from JWT, not query param
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_require_jwt_auth_rejects_missing_tenant_id_in_jwt(self, mock_request):
        """Test that JWT without tenant_id is rejected"""
        from backend.interface.middleware.multi_tenant_auth import require_jwt_auth
        
        # Mock JWT payload WITHOUT tenant_id
        mock_payload = {
            "channel": "web",
            "user_key": "test_user",
            "exp": 9999999999,
        }
        
        with patch('jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.return_value = mock_payload
            
            @require_jwt_auth
            async def test_handler(request):
                return {"success": True}
            
            result = await test_handler(mock_request)
            
            # Should reject
            assert result["error"] is True
            assert result["status_code"] == 401
            assert "missing tenant_id" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_require_jwt_auth_ignores_query_param_tenant_id(self, mock_request):
        """Test that query param tenant_id is ignored (security)"""
        from backend.interface.middleware.multi_tenant_auth import require_jwt_auth
        
        # Add tenant_id to query params (should be ignored)
        mock_request.query_params = {"tenant_id": "00000000-0000-0000-0000-000000000999"}
        
        # Mock JWT payload with different tenant_id
        mock_payload = {
            "tenant_id": "00000000-0000-0000-0000-000000000001",  # Different from query param
            "channel": "web",
            "user_key": "test_user",
            "origin": "https://example.com",
            "exp": 9999999999,
        }
        
        with patch('jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.side_effect = [
                mock_payload,  # Unverified decode
                mock_payload,  # Verified decode
            ]
            
            with patch('backend.interface.middleware.multi_tenant_auth.MultiTenantAuthMiddleware.resolve_context_from_jwt') as mock_resolve:
                mock_context = MagicMock()
                mock_context.tenant_id = "00000000-0000-0000-0000-000000000001"  # From JWT
                mock_resolve.return_value = mock_context
                
                @require_jwt_auth
                async def test_handler(request):
                    context = request.state.user_context
                    # Should use tenant_id from JWT, not query param
                    assert context.tenant_id == "00000000-0000-0000-0000-000000000001"
                    assert context.tenant_id != "00000000-0000-0000-0000-000000000999"
                    return {"success": True}
                
                result = await test_handler(mock_request)
                assert result["success"] is True


class TestTelegramWebhookTenantIDExtraction:
    """Test Telegram webhook tenant_id extraction"""
    
    @pytest.mark.asyncio
    async def test_telegram_webhook_rejects_header_tenant_id(self):
        """Test that Telegram webhook rejects tenant_id from header"""
        from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
        
        request = MagicMock()
        request.query_params = {"token": "test_bot_token"}
        request.headers = {"X-Telegram-Bot-Id": "00000000-0000-0000-0000-000000000999"}  # Should be ignored
        request.body = AsyncMock(return_value=b'{"update_id": 1, "message": {"text": "test"}}')
        request.json = MagicMock(return_value={"update_id": 1, "message": {"from": {"id": 123}, "text": "test"}})
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        
        with patch('backend.infrastructure.database_client.database_client') as mock_db:
            mock_db.pool = MagicMock()
            mock_conn = MagicMock()
            mock_db.pool.acquire = MagicMock()
            mock_db.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_db.pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('backend.domain.tenant.tenant_service.TenantService.resolve_tenant_id_from_telegram_bot_token') as mock_resolve:
                # Resolve from bot token (not header)
                mock_resolve.return_value = "00000000-0000-0000-0000-000000000001"
                
                with patch('backend.shared.auth_config.validate_tenant_id') as mock_validate:
                    mock_validate.return_value = True
                    
                    with patch('backend.interface.middleware.multi_tenant_auth.MultiTenantAuthMiddleware.verify_telegram_webhook') as mock_verify:
                        mock_verify.return_value = True
                        
                        api = MultiTenantBotAPI()
                        result = await api.telegram_webhook(request)
                        
                        # Should use tenant_id from bot token resolution, not header
                        mock_resolve.assert_called_once_with("test_bot_token")
                        # Header should be ignored
                        assert "X-Telegram-Bot-Id" not in str(mock_resolve.call_args)
    
    @pytest.mark.asyncio
    async def test_telegram_webhook_rejects_invalid_bot_token(self):
        """Test that invalid bot token is rejected"""
        from backend.interface.multi_tenant_bot_api import MultiTenantBotAPI
        
        request = MagicMock()
        request.query_params = {"token": "invalid_bot_token"}
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        
        with patch('backend.infrastructure.database_client.database_client') as mock_db:
            mock_db.pool = MagicMock()
            mock_conn = MagicMock()
            mock_db.pool.acquire = MagicMock()
            mock_db.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_db.pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('backend.domain.tenant.tenant_service.TenantService.resolve_tenant_id_from_telegram_bot_token') as mock_resolve:
                mock_resolve.return_value = None  # Invalid token
                
                api = MultiTenantBotAPI()
                result = await api.telegram_webhook(request)
                
                # Should reject
                assert result["error"] is True
                assert result["status_code"] == 401
                assert "Invalid bot token" in result["message"] or "not found" in result["message"]

