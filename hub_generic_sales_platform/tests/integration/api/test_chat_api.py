"""Integration tests for Chat API"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.api
@pytest.mark.asyncio
async def test_chat_message_success(client, tenant_1, db):
    """Test successful chat message through hybrid orchestrator"""
    
    # Setup test data
    from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Chat Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    v_repo = BotVersionRepository(db)
    
    bot = await bot_repo.create({
        "tenant_id": tenant_1.id,
        "domain_id": domain.id,
        "code": f"chat-bot-{uuid.uuid4().hex[:4]}",
        "name": "Test Chat Bot"
    }, tenant_id=tenant_1.id)
    
    version = await v_repo.create({
        "bot_id": bot.id,
        "version": 1,
        "is_active": True
    })
    
   # Mock user with correct tenant
    mock_user = MagicMock()
    mock_user.id = "test_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "user"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        # Call chat API
        headers = {"X-Tenant-ID": tenant_1.id}
        payload = {
            "bot_id": bot.id,
            "message": "Hello, how are you?",
            "session_id": None
        }
        
        resp = await client.post("/api/v1/chat/message", json=payload, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify response structure
        assert "response" in data
        assert "session_id" in data
        assert "tier" in data["metadata"]
        assert data["metadata"]["tier"] in ["fast_path", "knowledge_path", "agentic_path"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_chat_message_missing_bot(client, tenant_1):
    """Test chat with non-existent bot_id"""
    
    mock_user = MagicMock()
    mock_user.id = "test_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "user"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        payload = {
            "bot_id": "non-existent-bot-id",
            "message": "Hello",
            "session_id": None
        }
        
        resp = await client.post("/api/v1/chat/message", json=payload, headers=headers)
        
        # Should return error (404 or 500 depending on implementation)
        assert resp.status_code in [404, 500]


@pytest.mark.api
@pytest.mark.asyncio
async def test_chat_tenant_isolation(client, tenant_1, tenant_2, db):
    """Verify tenant cannot access another tenant's bot"""
    
    from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Isolation Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    v_repo = BotVersionRepository(db)
    
    # Create bot for tenant_2
    bot = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"isolated-bot-{uuid.uuid4().hex[:4]}",
        "name": "Tenant 2 Bot"
    }, tenant_id=tenant_2.id)
    
    version = await v_repo.create({
        "bot_id": bot.id,
        "version": 1,
        "is_active": True
    })
    
    # Mock user as tenant_1
    mock_user = MagicMock()
    mock_user.id = "tenant1_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "user"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        payload = {
            "bot_id": bot.id,  # Tenant 2's bot
            "message": "Trying to access other tenant's bot",
            "session_id": None
        }
        
        resp = await client.post("/api/v1/chat/message", json=payload, headers=headers)
        
        # Should fail (404 or 403)
        assert resp.status_code in [403, 404, 500]
