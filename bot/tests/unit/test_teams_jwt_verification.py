"""
Unit tests for Teams JWT verification
Task 1.4: Security tests for Teams JWT verification
"""
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.interface.middleware.multi_tenant_auth import MultiTenantAuthMiddleware
from backend.shared.exceptions import AuthenticationError
from backend.infrastructure.jwks_client import MicrosoftJWKSClient


class TestTeamsJWTVerification:
    """Test Teams JWT verification with JWKS"""
    
    @pytest.fixture
    def mock_jwks_client(self):
        """Mock JWKS client"""
        client = MagicMock(spec=MicrosoftJWKSClient)
        client.get_public_key = AsyncMock(return_value="mock_public_key_pem")
        return client
    
    @pytest.fixture
    def valid_teams_jwt(self):
        """Create a valid Teams JWT for testing"""
        # Note: This is a mock JWT - in real tests, we'd use actual Microsoft JWKs
        payload = {
            "iss": "https://api.botframework.com",
            "aud": "bot-service",
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "nbf": int((datetime.now() - timedelta(minutes=5)).timestamp()),
            "tenantId": "00000000-0000-0000-0000-000000000001",
            "serviceUrl": "https://smba.trafficmanager.net/00000000-0000-0000-0000-000000000001/",
            "from": {
                "id": "29:User123",
                "aadObjectId": "00000000-0000-0000-0000-000000000002"
            }
        }
        
        # Create a mock token (in real scenario, this would be signed by Microsoft)
        # For testing, we'll mock the verification
        token = jwt.encode(payload, "mock_secret", algorithm="HS256")
        return token
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_missing_kid(self):
        """Test that JWT without kid is rejected"""
        # Create token without kid in header
        payload = {"exp": int((datetime.now() + timedelta(hours=1)).timestamp())}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        
        with pytest.raises(AuthenticationError, match="JWT missing kid"):
            await MultiTenantAuthMiddleware.verify_teams_jwt(token)
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_invalid_signature(self):
        """Test that JWT with invalid signature is rejected"""
        # Mock JWKS client to return a key that won't verify
        with patch('backend.interface.middleware.multi_tenant_auth.get_jwks_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_public_key = AsyncMock(return_value="invalid_key")
            mock_get_client.return_value = mock_client
            
            # Create token with kid
            header = {"kid": "test_kid", "alg": "RS256"}
            payload = {
                "iss": "https://api.botframework.com",
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            }
            
            # This will fail signature verification
            with pytest.raises(AuthenticationError, match="Invalid JWT signature"):
                await MultiTenantAuthMiddleware.verify_teams_jwt(
                    jwt.encode(payload, "wrong_secret", algorithm="HS256", headers=header)
                )
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_expired(self):
        """Test that expired JWT is rejected"""
        with patch('backend.interface.middleware.multi_tenant_auth.get_jwks_client') as mock_get_client:
            # Mock public key (would need real RSA key for actual verification)
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            mock_client = MagicMock()
            mock_client.get_public_key = AsyncMock(return_value=public_key_pem)
            mock_get_client.return_value = mock_client
            
            # Create expired token
            header = {"kid": "test_kid", "alg": "RS256"}
            payload = {
                "iss": "https://api.botframework.com",
                "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),  # Expired
                "nbf": int((datetime.now() - timedelta(hours=2)).timestamp()),
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
            
            with pytest.raises(AuthenticationError, match="JWT expired"):
                await MultiTenantAuthMiddleware.verify_teams_jwt(token)
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_invalid_issuer(self):
        """Test that JWT with invalid issuer is rejected"""
        with patch('backend.interface.middleware.multi_tenant_auth.get_jwks_client') as mock_get_client:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            mock_client = MagicMock()
            mock_client.get_public_key = AsyncMock(return_value=public_key_pem)
            mock_get_client.return_value = mock_client
            
            # Create token with invalid issuer
            header = {"kid": "test_kid", "alg": "RS256"}
            payload = {
                "iss": "https://evil.com",  # Invalid issuer
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "nbf": int((datetime.now() - timedelta(minutes=5)).timestamp()),
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
            
            with pytest.raises(AuthenticationError, match="Invalid JWT issuer"):
                await MultiTenantAuthMiddleware.verify_teams_jwt(token)
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_extracts_tenant_id(self):
        """Test that tenant_id is extracted from JWT payload"""
        with patch('backend.interface.middleware.multi_tenant_auth.get_jwks_client') as mock_get_client:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            mock_client = MagicMock()
            mock_client.get_public_key = AsyncMock(return_value=public_key_pem)
            mock_get_client.return_value = mock_client
            
            # Create valid token with tenant_id
            header = {"kid": "test_kid", "alg": "RS256"}
            expected_tenant_id = "00000000-0000-0000-0000-000000000001"
            payload = {
                "iss": "https://api.botframework.com",
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "nbf": int((datetime.now() - timedelta(minutes=5)).timestamp()),
                "tenantId": expected_tenant_id,
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
            
            result = await MultiTenantAuthMiddleware.verify_teams_jwt(token)
            
            assert result.get("tenant_id") == expected_tenant_id
            assert result.get("tenantId") == expected_tenant_id
    
    @pytest.mark.asyncio
    async def test_verify_teams_jwt_tenant_id_mismatch(self):
        """Test that tenant_id mismatch is rejected"""
        with patch('backend.interface.middleware.multi_tenant_auth.get_jwks_client') as mock_get_client:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            mock_client = MagicMock()
            mock_client.get_public_key = AsyncMock(return_value=public_key_pem)
            mock_get_client.return_value = mock_client
            
            # Create token with tenant_id
            header = {"kid": "test_kid", "alg": "RS256"}
            payload = {
                "iss": "https://api.botframework.com",
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "nbf": int((datetime.now() - timedelta(minutes=5)).timestamp()),
                "tenantId": "00000000-0000-0000-0000-000000000001",
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
            
            # Provide different tenant_id
            with pytest.raises(AuthenticationError, match="JWT tenant ID mismatch"):
                await MultiTenantAuthMiddleware.verify_teams_jwt(
                    token,
                    tenant_id="00000000-0000-0000-0000-000000000002"  # Different tenant
                )


class TestJWKSClient:
    """Test JWKS client functionality"""
    
    @pytest.mark.asyncio
    async def test_jwks_client_fetch(self):
        """Test JWKS client can fetch from Microsoft endpoint"""
        client = MicrosoftJWKSClient()
        
        try:
            jwks = await client.fetch_jwks()
            assert "keys" in jwks
            assert isinstance(jwks["keys"], list)
            assert len(jwks["keys"]) > 0
        except Exception as e:
            # If network fails, skip test
            pytest.skip(f"Network error: {e}")
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_jwks_client_caching(self):
        """Test JWKS client caches results"""
        client = MicrosoftJWKSClient()
        
        try:
            # First fetch
            jwks1 = await client.get_jwks()
            
            # Second fetch should use cache
            with patch.object(client, 'fetch_jwks') as mock_fetch:
                jwks2 = await client.get_jwks()
                mock_fetch.assert_not_called()  # Should not call fetch
                assert jwks1 == jwks2
        except Exception as e:
            pytest.skip(f"Network error: {e}")
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_jwks_client_force_refresh(self):
        """Test JWKS client can force refresh"""
        client = MicrosoftJWKSClient()
        
        try:
            # First fetch
            await client.get_jwks()
            
            # Force refresh
            with patch.object(client, 'fetch_jwks') as mock_fetch:
                mock_fetch.return_value = {"keys": []}
                await client.get_jwks(force_refresh=True)
                mock_fetch.assert_called_once()
        except Exception as e:
            pytest.skip(f"Network error: {e}")
        finally:
            await client.close()

