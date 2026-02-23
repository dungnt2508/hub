"""Integration tests for Bot Management API"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_bot(client, tenant_1, db):
    """Test creating a new bot"""
    
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Bot Domain")
    db.add(domain)
    await db.flush()
    
    mock_user = MagicMock()
    mock_user.id = "admin_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        payload = {
            "code": f"BOT_{uuid.uuid4().hex[:6]}".upper(),
            "name": "Test Bot",
            "domain_id": domain.id
        }
        
        resp = await client.post("/api/v1/bots", json=payload, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == payload["code"]
        assert data["name"] == payload["name"]
        assert "id" in data


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_bots_tenant_scoped(client, tenant_1, tenant_2, db):
    """Test that list_bots only returns bots for current tenant"""
    
    from app.infrastructure.database.repositories import BotRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Multi Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    
    # Create bot for tenant_1
    bot1 = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"T1BOT_{uuid.uuid4().hex[:4]}",
        "name": "Tenant 1 Bot"
    }, tenant_id=tenant_1.id)
    
    # Create bot for tenant_2
    bot2 = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"T2BOT_{uuid.uuid4().hex[:4]}",
        "name": "Tenant 2 Bot"
    }, tenant_id=tenant_2.id)
    
    # Query as tenant_1
    mock_user = MagicMock()
    mock_user.id = "t1_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        resp = await client.get("/api/v1/bots", headers=headers)
        
        assert resp.status_code == 200
        bots = resp.json()
        
        # Should only see tenant_1's bots
        bot_codes = [b["code"] for b in bots]
        assert bot1.code in bot_codes
        assert bot2.code not in bot_codes


@pytest.mark.api
@pytest.mark.asyncio
async def test_update_bot(client, tenant_1, db):
    """Test updating bot metadata"""
    
    from app.infrastructure.database.repositories import BotRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Update Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    bot = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"UPDATE_BOT_{uuid.uuid4().hex[:4]}",
        "name": "Original Name"
    }, tenant_id=tenant_1.id)
    
    mock_user = MagicMock()
    mock_user.id = "admin"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        payload = {"name": "Updated Name"}
        
        resp = await client.put(f"/api/v1/bots/{bot.id}", json=payload, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"


@pytest.mark.api
@pytest.mark.asyncio
async def test_delete_bot(client, tenant_1, db):
    """Test deleting a bot"""
    
    from app.infrastructure.database.repositories import BotRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Delete Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    bot = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"DELETE_BOT_{uuid.uuid4().hex[:4]}",
        "name": "To Be Deleted"
    }, tenant_id=tenant_1.id)
    
    mock_user = MagicMock()
    mock_user.id = "admin"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        
        resp = await client.delete(f"/api/v1/bots/{bot.id}", headers=headers)
        
        assert resp.status_code == 200
        
        # Verify it's gone
        check = await bot_repo.get(bot.id, tenant_id=tenant_1.id)
        assert check is None


@pytest.mark.api
@pytest.mark.asyncio
async def test_bot_version_management(client, tenant_1, db):
    """Test creating and publishing bot versions"""
    
    from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Version Domain")
    db.add(domain)
    await db.flush()
    
    bot_repo = BotRepository(db)
    bot = await bot_repo.create({
        "domain_id": domain.id,
        "code": f"VER_BOT_{uuid.uuid4().hex[:4]}",
        "name": "Version Bot"
    }, tenant_id=tenant_1.id)
    
    mock_user = MagicMock()
    mock_user.id = "admin"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_user
        
        headers = {"X-Tenant-ID": tenant_1.id}
        
        # Create version
        resp = await client.post(f"/api/v1/bots/{bot.id}/versions", headers=headers)
        assert resp.status_code == 200
        version_data = resp.json()
        assert "id" in version_data
        assert version_data["version"] == 1
        
        # List versions
        resp = await client.get(f"/api/v1/bots/{bot.id}/versions", headers=headers)
        assert resp.status_code == 200
        versions = resp.json()
        assert len(versions) >= 1
