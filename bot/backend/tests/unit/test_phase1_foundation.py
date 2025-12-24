"""
Phase 1 Tests - Foundation: Tenant Service & JWT Infrastructure
Tests for:
- Tenant creation
- JWT generation & verification
- Origin binding
- Token expiration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import jwt as pyjwt
import uuid

from backend.domain.tenant.tenant_service import TenantService
from backend.domain.tenant.jwt_service import JWTService, generate_user_key, generate_session_id
from backend.schemas.multi_tenant_types import TenantConfig, ChannelType, AuthMethod
from backend.shared.exceptions import (
    TenantAlreadyExistsError,
    ValidationError,
    AuthenticationError,
)


# ============================================================================
# FIXTURES
# ============================================================================

class MockDatabase:
    """Mock database for testing (in-memory)"""
    
    def __init__(self):
        self.tenants = {}
        self.api_keys = {}
        self.user_keys = {}
        self.conversations = {}
    
    async def fetchrow(self, query: str, *args):
        """Mock fetchrow"""
        if "SELECT * FROM tenants WHERE id" in query:
            tenant_id = args[0]
            return self.tenants.get(tenant_id)
        
        if "INSERT INTO tenants" in query:
            # Extract values from INSERT
            tenant_id, name, api_key, plan, web_embed_enabled, origins, jwt_secret, expiry = args[:8]
            self.tenants[tenant_id] = {
                'id': tenant_id,
                'name': name,
                'api_key': api_key,
                'plan': plan,
                'web_embed_enabled': web_embed_enabled,
                'web_embed_origins': origins,
                'web_embed_jwt_secret': jwt_secret,
                'web_embed_token_expiry_seconds': expiry,
                'created_at': datetime.now(),
            }
            return self.tenants[tenant_id]
        
        return None
    
    async def fetchval(self, query: str, *args):
        """Mock fetchval (returns single value)"""
        if "SELECT web_embed_jwt_secret FROM tenants WHERE id" in query:
            tenant_id = args[0]
            tenant = self.tenants.get(tenant_id)
            return tenant.get('web_embed_jwt_secret') if tenant else None
        
        return None
    
    async def fetch(self, query: str, *args):
        """Mock fetch (returns multiple rows)"""
        return list(self.tenants.values())
    
    async def execute(self, query: str, *args):
        """Mock execute"""
        return "UPDATE 1"


@pytest.fixture
async def mock_db():
    """Create mock database"""
    return MockDatabase()


@pytest.fixture
async def tenant_service(mock_db):
    """Create tenant service with mock DB"""
    return TenantService(mock_db)


@pytest.fixture
async def jwt_service(mock_db):
    """Create JWT service with mock DB"""
    return JWTService(mock_db)


# ============================================================================
# TENANT SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_tenant_success(tenant_service, mock_db):
    """Test successful tenant creation"""
    result = await tenant_service.create_tenant(
        name="Test Tenant",
        site_id="test-001",
        web_embed_origins=["https://example.com"],
        plan="basic",
    )
    
    assert result['success'] is True
    assert result['data']['tenant_id'] is not None
    assert result['data']['api_key'] is not None
    assert result['data']['jwt_secret'] is not None
    assert result['data']['site_id'] == "test-001"
    assert result['data']['plan'] == "basic"


@pytest.mark.asyncio
async def test_create_tenant_invalid_name(tenant_service):
    """Test tenant creation with invalid name"""
    with pytest.raises(ValidationError):
        await tenant_service.create_tenant(
            name="",  # Invalid
            site_id="test-001",
            web_embed_origins=["https://example.com"],
        )


@pytest.mark.asyncio
async def test_create_tenant_invalid_origins(tenant_service):
    """Test tenant creation with no origins"""
    with pytest.raises(ValidationError):
        await tenant_service.create_tenant(
            name="Test Tenant",
            site_id="test-001",
            web_embed_origins=[],  # Invalid
        )


@pytest.mark.asyncio
async def test_create_tenant_duplicate_site_id(tenant_service, mock_db):
    """Test duplicate site_id prevention"""
    # Create first tenant
    await tenant_service.create_tenant(
        name="Test Tenant 1",
        site_id="test-001",
        web_embed_origins=["https://example.com"],
    )
    
    # Try to create duplicate
    with pytest.raises(TenantAlreadyExistsError):
        await tenant_service.create_tenant(
            name="Test Tenant 2",
            site_id="test-001",  # Duplicate
            web_embed_origins=["https://example.com"],
        )


@pytest.mark.asyncio
async def test_get_tenant_config(tenant_service, mock_db):
    """Test fetching tenant config"""
    # Create tenant
    create_result = await tenant_service.create_tenant(
        name="Test Tenant",
        site_id="test-001",
        web_embed_origins=["https://example.com", "https://example2.com"],
    )
    tenant_id = create_result['data']['tenant_id']
    
    # Fetch config
    config = await tenant_service.get_tenant_config(tenant_id)
    
    assert config is not None
    assert config.id == tenant_id
    assert config.name == "Test Tenant"
    assert "https://example.com" in config.web_embed_origins


# ============================================================================
# JWT SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_jwt(jwt_service, mock_db):
    """Test JWT generation"""
    tenant_id = str(uuid.uuid4())
    user_key = "test_user_123"
    origin = "https://example.com"
    
    # Setup mock DB
    mock_db.tenants[tenant_id] = {
        'web_embed_jwt_secret': 'test_secret_' + 'x' * 32,
    }
    
    # Generate token
    token = await jwt_service.generate_jwt(
        tenant_id=tenant_id,
        user_key=user_key,
        origin=origin,
    )
    
    assert token is not None
    assert len(token) > 0
    
    # Decode and verify
    payload = pyjwt.decode(
        token,
        'test_secret_' + 'x' * 32,
        algorithms=['HS256']
    )
    
    assert payload['tenant_id'] == tenant_id
    assert payload['user_key'] == user_key
    assert payload['origin'] == origin
    assert payload['channel'] == ChannelType.WEB


@pytest.mark.asyncio
async def test_verify_jwt_success(jwt_service, mock_db):
    """Test JWT verification (valid token)"""
    tenant_id = str(uuid.uuid4())
    user_key = "test_user_123"
    origin = "https://example.com"
    jwt_secret = 'test_secret_' + 'x' * 32
    
    # Setup mock DB
    mock_db.tenants[tenant_id] = {
        'web_embed_jwt_secret': jwt_secret,
    }
    
    # Generate token
    token = await jwt_service.generate_jwt(
        tenant_id=tenant_id,
        user_key=user_key,
        origin=origin,
    )
    
    # Verify token
    payload = await jwt_service.verify_jwt(token, tenant_id, origin)
    
    assert payload.tenant_id == tenant_id
    assert payload.user_key == user_key
    assert payload.origin == origin


@pytest.mark.asyncio
async def test_verify_jwt_invalid_signature(jwt_service, mock_db):
    """Test JWT verification (invalid signature)"""
    tenant_id = str(uuid.uuid4())
    jwt_secret = 'test_secret_' + 'x' * 32
    
    # Setup mock DB
    mock_db.tenants[tenant_id] = {
        'web_embed_jwt_secret': jwt_secret,
    }
    
    # Create token with WRONG secret
    wrong_token = pyjwt.encode(
        {
            'tenant_id': tenant_id,
            'user_key': 'test_user',
            'origin': 'https://example.com',
            'channel': ChannelType.WEB,
            'iat': int(datetime.utcnow().timestamp()),
            'exp': int((datetime.utcnow() + timedelta(minutes=5)).timestamp()),
        },
        'wrong_secret_not_matching',
        algorithm='HS256'
    )
    
    # Verify should fail
    with pytest.raises(AuthenticationError):
        await jwt_service.verify_jwt(wrong_token, tenant_id, 'https://example.com')


@pytest.mark.asyncio
async def test_verify_jwt_origin_mismatch(jwt_service, mock_db):
    """Test JWT verification (origin mismatch)"""
    tenant_id = str(uuid.uuid4())
    user_key = "test_user_123"
    origin = "https://example.com"
    jwt_secret = 'test_secret_' + 'x' * 32
    
    # Setup mock DB
    mock_db.tenants[tenant_id] = {
        'web_embed_jwt_secret': jwt_secret,
    }
    
    # Generate token with origin A
    token = await jwt_service.generate_jwt(
        tenant_id=tenant_id,
        user_key=user_key,
        origin=origin,
    )
    
    # Try to verify with different origin
    with pytest.raises(AuthenticationError) as exc_info:
        await jwt_service.verify_jwt(token, tenant_id, "https://attacker.com")
    
    assert "origin mismatch" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_jwt_expiration(jwt_service, mock_db):
    """Test JWT expiration validation"""
    tenant_id = str(uuid.uuid4())
    user_key = "test_user_123"
    origin = "https://example.com"
    jwt_secret = 'test_secret_' + 'x' * 32
    
    # Setup mock DB
    mock_db.tenants[tenant_id] = {
        'web_embed_jwt_secret': jwt_secret,
    }
    
    # Create expired token (exp in past)
    expired_token = pyjwt.encode(
        {
            'tenant_id': tenant_id,
            'user_key': user_key,
            'origin': origin,
            'channel': ChannelType.WEB,
            'iat': int((datetime.utcnow() - timedelta(minutes=10)).timestamp()),
            'exp': int((datetime.utcnow() - timedelta(minutes=5)).timestamp()),  # Expired!
        },
        jwt_secret,
        algorithm='HS256'
    )
    
    # Verify should fail
    with pytest.raises(AuthenticationError) as exc_info:
        await jwt_service.verify_jwt(expired_token, tenant_id, origin)
    
    assert "expired" in str(exc_info.value).lower()


# ============================================================================
# UTILITY TESTS
# ============================================================================

def test_generate_user_key():
    """Test user_key generation"""
    site_id = "test-site-001"
    session_id = "session-abc123"
    
    user_key = generate_user_key(site_id, session_id)
    
    # Should be deterministic (same inputs = same output)
    user_key2 = generate_user_key(site_id, session_id)
    assert user_key == user_key2
    
    # Should be 16 chars (SHA256 truncated)
    assert len(user_key) == 16
    
    # Should be hex (SHA256)
    assert all(c in '0123456789abcdef' for c in user_key)


def test_generate_session_id():
    """Test session_id generation"""
    session_id1 = generate_session_id()
    session_id2 = generate_session_id()
    
    # Should be random (different each time)
    assert session_id1 != session_id2
    
    # Should not be empty
    assert len(session_id1) > 0
    assert len(session_id2) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_tenant_and_generate_jwt(tenant_service, jwt_service, mock_db):
    """Integration: Create tenant and generate JWT"""
    # Create tenant
    create_result = await tenant_service.create_tenant(
        name="Integration Test Tenant",
        site_id="integration-001",
        web_embed_origins=["https://example.com"],
    )
    tenant_id = create_result['data']['tenant_id']
    jwt_secret = create_result['data']['jwt_secret']
    
    # Store secret in mock DB
    mock_db.tenants[tenant_id]['web_embed_jwt_secret'] = jwt_secret
    
    # Generate JWT
    token = await jwt_service.generate_jwt(
        tenant_id=tenant_id,
        user_key="user-123",
        origin="https://example.com",
    )
    
    assert token is not None
    
    # Verify JWT
    payload = await jwt_service.verify_jwt(
        token,
        tenant_id,
        "https://example.com",
    )
    
    assert payload.tenant_id == tenant_id
    assert payload.user_key == "user-123"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

