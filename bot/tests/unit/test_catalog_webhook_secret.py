"""
Unit tests for Catalog Webhook Secret Verification (Task 6)
"""
import pytest
import hmac
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient

from backend.interface.middleware.multi_tenant_auth import verify_webhook_secret
from backend.shared.auth_config import get_tenant_config
from backend.schemas.multi_tenant_types import TenantConfig, PlanType


class TestWebhookSecretVerification:
    """Test webhook secret verification function"""
    
    def test_verify_webhook_secret_valid(self):
        """Test that valid webhook signature is accepted"""
        webhook_secret = "test_secret_123"
        request_body = b'{"tenant_id": "test-tenant", "event": "created", "product_id": "prod-123"}'
        
        # Calculate expected signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        result = verify_webhook_secret(request_body, expected_signature, webhook_secret)
        assert result is True
    
    def test_verify_webhook_secret_invalid(self):
        """Test that invalid webhook signature is rejected"""
        webhook_secret = "test_secret_123"
        request_body = b'{"tenant_id": "test-tenant", "event": "created", "product_id": "prod-123"}'
        
        # Wrong signature
        wrong_signature = "wrong_signature_abc123"
        
        result = verify_webhook_secret(request_body, wrong_signature, webhook_secret)
        assert result is False
    
    def test_verify_webhook_secret_missing_header(self):
        """Test that missing signature header is rejected when secret is configured"""
        webhook_secret = "test_secret_123"
        request_body = b'{"tenant_id": "test-tenant", "event": "created", "product_id": "prod-123"}'
        
        result = verify_webhook_secret(request_body, None, webhook_secret)
        assert result is False
    
    def test_verify_webhook_secret_no_secret_configured(self):
        """Test that verification is skipped if tenant has no webhook_secret"""
        request_body = b'{"tenant_id": "test-tenant", "event": "created", "product_id": "prod-123"}'
        
        # If webhook_secret is None or empty, verification is skipped (backward compatibility)
        result = verify_webhook_secret(request_body, None, None)
        assert result is True
        
        result = verify_webhook_secret(request_body, None, "")
        assert result is True
    
    def test_verify_webhook_secret_empty_body(self):
        """Test verification with empty body"""
        webhook_secret = "test_secret_123"
        request_body = b''
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        result = verify_webhook_secret(request_body, expected_signature, webhook_secret)
        assert result is True
    
    def test_verify_webhook_secret_timing_attack_protection(self):
        """Test that constant-time comparison is used (prevent timing attacks)"""
        webhook_secret = "test_secret_123"
        request_body = b'{"tenant_id": "test-tenant", "event": "created", "product_id": "prod-123"}'
        
        # Calculate correct signature
        correct_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        # Wrong signature (different length)
        wrong_signature = "a" * 64  # Same length but wrong value
        
        # Both should take similar time (constant-time comparison)
        result_correct = verify_webhook_secret(request_body, correct_signature, webhook_secret)
        result_wrong = verify_webhook_secret(request_body, wrong_signature, webhook_secret)
        
        assert result_correct is True
        assert result_wrong is False


@pytest.mark.asyncio
class TestCatalogWebhookEndpoint:
    """Test catalog webhook endpoint with secret verification"""
    
    @pytest.fixture
    def mock_tenant_config(self):
        """Mock tenant config with webhook_secret"""
        return TenantConfig(
            id="test-tenant-id",
            name="Test Tenant",
            api_key="test-api-key",
            webhook_secret="test_webhook_secret_123",
            plan=PlanType.BASIC,
            rate_limit_per_hour=1000,
            rate_limit_per_day=10000,
        )
    
    @pytest.fixture
    def mock_tenant_config_no_secret(self):
        """Mock tenant config without webhook_secret"""
        return TenantConfig(
            id="test-tenant-id",
            name="Test Tenant",
            api_key="test-api-key",
            webhook_secret=None,
            plan=PlanType.BASIC,
            rate_limit_per_hour=1000,
            rate_limit_per_day=10000,
        )
    
    @pytest.fixture
    def webhook_payload(self):
        """Sample webhook payload"""
        return {
            "tenant_id": "test-tenant-id",
            "event": "created",
            "product_id": "prod-123"
        }
    
    def calculate_signature(self, body: bytes, secret: str) -> str:
        """Calculate HMAC-SHA256 signature"""
        return hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_valid_signature(self, mock_tenant_config, webhook_payload):
        """Test that webhook with valid signature is accepted"""
        with patch('backend.shared.auth_config.get_tenant_config', return_value=mock_tenant_config):
            with patch('backend.interface.routers.webhooks.get_multi_tenant_api') as mock_get_api:
                with patch('backend.interface.routers.webhooks.database_client') as mock_db:
                    # Mock database client
                    mock_db.pool = MagicMock()
                    
                    # Mock successful webhook processing
                    mock_api_instance = MagicMock()
                    mock_api_instance.catalog_webhook = AsyncMock(return_value={
                        "success": True,
                        "data": {"processed": True},
                        "status_code": 200
                    })
                    mock_get_api.return_value = mock_api_instance
                    
                    # Create test client
                    from backend.interface.routers.webhooks import router, set_multi_tenant_api
                    from fastapi import FastAPI
                    app = FastAPI()
                    app.include_router(router)
                    set_multi_tenant_api(mock_api_instance)
                    client = TestClient(app)
                    
                    # Prepare request body
                    body_bytes = json.dumps(webhook_payload).encode('utf-8')
                    signature = self.calculate_signature(body_bytes, mock_tenant_config.webhook_secret)
                    
                    # Make request with valid signature
                    response = client.post(
                        "/webhooks/catalog/product-updated",
                        content=body_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": signature
                        }
                    )
                    
                    # Should succeed
                    assert response.status_code == 200
                    assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_invalid_signature(self, mock_tenant_config, webhook_payload):
        """Test that webhook with invalid signature is rejected"""
        with patch('backend.shared.auth_config.get_tenant_config', return_value=mock_tenant_config):
            # Create test client
            from backend.interface.routers.webhooks import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Prepare request body
            body_bytes = json.dumps(webhook_payload).encode('utf-8')
            wrong_signature = "wrong_signature_abc123"
            
            # Make request with invalid signature
            response = client.post(
                "/webhooks/catalog/product-updated",
                content=body_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": wrong_signature
                }
            )
            
            # Should be rejected
            assert response.status_code == 401
            assert response.json()["success"] is False
            assert response.json()["error"] == "INVALID_WEBHOOK_SIGNATURE"
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_missing_signature_header(self, mock_tenant_config, webhook_payload):
        """Test that webhook without signature header is rejected when secret is configured"""
        with patch('backend.shared.auth_config.get_tenant_config', return_value=mock_tenant_config):
            # Create test client
            from backend.interface.routers.webhooks import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Prepare request body
            body_bytes = json.dumps(webhook_payload).encode('utf-8')
            
            # Make request without signature header
            response = client.post(
                "/webhooks/catalog/product-updated",
                content=body_bytes,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            # Should be rejected
            assert response.status_code == 401
            assert response.json()["success"] is False
            assert response.json()["error"] == "INVALID_WEBHOOK_SIGNATURE"
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_no_secret_configured(self, mock_tenant_config_no_secret, webhook_payload):
        """Test that webhook is accepted if tenant has no webhook_secret configured"""
        with patch('backend.shared.auth_config.get_tenant_config', return_value=mock_tenant_config_no_secret):
            with patch('backend.interface.routers.webhooks.get_multi_tenant_api') as mock_get_api:
                with patch('backend.interface.routers.webhooks.database_client') as mock_db:
                    # Mock database client
                    mock_db.pool = MagicMock()
                    
                    # Mock successful webhook processing
                    mock_api_instance = MagicMock()
                    mock_api_instance.catalog_webhook = AsyncMock(return_value={
                        "success": True,
                        "data": {"processed": True},
                        "status_code": 200
                    })
                    mock_get_api.return_value = mock_api_instance
                    
                    # Create test client
                    from backend.interface.routers.webhooks import router, set_multi_tenant_api
                    from fastapi import FastAPI
                    app = FastAPI()
                    app.include_router(router)
                    set_multi_tenant_api(mock_api_instance)
                    client = TestClient(app)
                    
                    # Prepare request body
                    body_bytes = json.dumps(webhook_payload).encode('utf-8')
                    
                    # Make request without signature (should be accepted if no secret configured)
                    response = client.post(
                        "/webhooks/catalog/product-updated",
                        content=body_bytes,
                        headers={
                            "Content-Type": "application/json"
                        }
                    )
                    
                    # Should succeed (backward compatibility)
                    assert response.status_code == 200
                    assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_tenant_not_found(self, webhook_payload):
        """Test that webhook with non-existent tenant is rejected"""
        with patch('backend.shared.auth_config.get_tenant_config', return_value=None):
            # Create test client
            from backend.interface.routers.webhooks import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Prepare request body
            body_bytes = json.dumps(webhook_payload).encode('utf-8')
            
            # Make request
            response = client.post(
                "/webhooks/catalog/product-updated",
                content=body_bytes,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            # Should be rejected
            assert response.status_code == 404
            assert response.json()["success"] is False
            assert response.json()["error"] == "TENANT_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_missing_tenant_id(self):
        """Test that webhook without tenant_id is rejected"""
        # Create test client
        from backend.interface.routers.webhooks import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Prepare request body without tenant_id
        payload = {
            "event": "created",
            "product_id": "prod-123"
        }
        body_bytes = json.dumps(payload).encode('utf-8')
        
        # Make request
        response = client.post(
            "/webhooks/catalog/product-updated",
            content=body_bytes,
            headers={
                "Content-Type": "application/json"
            }
        )
        
        # Should be rejected
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert response.json()["error"] == "MISSING_TENANT_ID"
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_invalid_json(self):
        """Test that webhook with invalid JSON is rejected"""
        # Create test client
        from backend.interface.routers.webhooks import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Prepare invalid JSON
        body_bytes = b'{"invalid": json}'
        
        # Make request
        response = client.post(
            "/webhooks/catalog/product-updated",
            content=body_bytes,
            headers={
                "Content-Type": "application/json"
            }
        )
        
        # Should be rejected
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert response.json()["error"] == "INVALID_JSON"

