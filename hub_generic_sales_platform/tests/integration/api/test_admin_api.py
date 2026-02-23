"""Integration tests for Admin APIs - Sprint 3"""

import pytest
import uuid
from httpx import AsyncClient
from app.main import app
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.knowledge import KnowledgeDomain
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
async def client(db: AsyncSession):
    """Fixture for FastAPI async client override db"""
    from app.infrastructure.database.engine import get_session
    from httpx import ASGITransport
    
    # Override get_session dependency to use the test db fixture
    async def override_get_session():
        yield db
    
    # Mock user for AuthMiddleware
    mock_user = MagicMock()
    mock_user.id = "test_user_id"
    # We set a default tenant_id, but it will be overridden in specific tests
    mock_user.tenant_id = "test_tenant_id" 
    mock_user.role = "admin"
    mock_user.email = "admin@test.com"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    app.dependency_overrides[get_session] = override_get_session
    
    # Patch Auth middleware token validation
    # Use nested patching to ensure all are active during client lifespan
    with patch("app.interfaces.middleware.auth.get_bearer_token", return_value="dummy_token"), \
         patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_get_user:
        
        mock_get_user.return_value = mock_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
            
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_admin_health(client):
    """Test GET /health"""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"


@pytest.mark.asyncio
async def test_tenant_admin_flow(client, db):
    """Test creating and listing tenants - JWT required, user only manages own tenant"""
    from app.infrastructure.database.models.tenant import Tenant, TenantStatus, TenantPlan
    my_tenant = Tenant(id="test_tenant_id", name="My Admin Tenant", status=TenantStatus.ACTIVE, plan=TenantPlan.PRO)
    db.add(my_tenant)
    await db.flush()
    headers = {"Authorization": "Bearer dummy_token"}

    # 1. List - returns only user's tenant
    resp = await client.get("/api/v1/tenants", headers=headers)
    assert resp.status_code == 200
    tenants = resp.json()
    assert len(tenants) >= 1 and any(t["id"] == "test_tenant_id" for t in tenants)

    # 2. Create tenant
    new_tenant = {"name": "New Admin Tenant"}
    resp = await client.post("/api/v1/tenants", json=new_tenant, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Admin Tenant"
    assert "id" in data

    # 3. Update user's own tenant (path id must match mock_user.tenant_id)
    resp = await client.put(
        "/api/v1/tenants/test_tenant_id",
        json={"name": "Updated Admin Tenant"},
        headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Admin Tenant"

    # 4. Update tenant status
    resp = await client.patch(
        "/api/v1/tenants/test_tenant_id/status",
        json={"status": "active"},
        headers=headers
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_tenant_404(client):
    """Test PUT /tenants/{id} - tenant không tồn tại trả 404.
    Path tenant_id phải = current user's tenant_id (403 nếu khác)."""
    # mock_user.tenant_id = "test_tenant_id"; tenant này chưa có trong DB
    resp = await client.put(
        "/api/v1/tenants/test_tenant_id",
        json={"name": "X"},
        headers={"Authorization": "Bearer dummy_token"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bot_admin_flow(client, tenant_1, db):
    """Test creating and listing bots for a specific tenant"""
    headers = {"Authorization": "Bearer dummy_token"}
    
    # Mock user to belong to tenant_1 (request.state.tenant_id from JWT)
    mock_user = MagicMock()
    mock_user.id = "admin_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"
    
    # We need to re-patch get_user_from_token because the fixture's patch is already active
    # and we want to change the return value.
    # The fixture uses `new_callable=AsyncMock`.
    # We can try to access the mock from the fixture? No easy way.
    # We stack another patch on top.
    
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        
        domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Admin Domain")
        db.add(domain)
        await db.flush()

        # 1. Create Bot
        bot_data = {"name": "Test Admin Bot", "code": f"ADMIN_BOT_{uuid.uuid4().hex[:4]}", "domain_id": domain.id}
        resp = await client.post("/api/v1/bots", json=bot_data, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["code"] == bot_data["code"]
        
        # 2. List Bots
        resp = await client.get("/api/v1/bots", headers=headers)
        assert resp.status_code == 200
        bots = resp.json()
        assert any(b["code"] == bot_data["code"] for b in bots)

@pytest.mark.asyncio
async def test_knowledge_base_admin_flow(client, tenant_1, db):
    """Test FAQ and Cache admin APIs"""
    headers = {"Authorization": "Bearer dummy_token"}
    
    mock_user = MagicMock()
    mock_user.id = "admin_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user

        domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="KB Domain")
        db.add(domain)
        await db.flush()

        # 1. Create FAQ
        faq_data = {"question": "How to reset password?", "answer": "Click help.", "domain_id": domain.id}
        resp = await client.post("/api/v1/faqs", json=faq_data, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["question"] == faq_data["question"]
        
        # 2. Create Cache
        cache_data = {"query_text": f"hello-{uuid.uuid4().hex[:4]}", "response_text": "hi there"}
        resp = await client.post("/api/v1/cache", json=cache_data, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["query_text"] == cache_data["query_text"]
        
        # 3. List
        resp = await client.get("/api/v1/faqs", headers=headers)
        assert len(resp.json()) >= 1
        
        resp = await client.get("/api/v1/cache", headers=headers)
        assert len(resp.json()) >= 1

@pytest.mark.asyncio
async def test_session_stats_api(client, tenant_1, db):
    """Test session statistics endpoint"""
    headers = {"Authorization": "Bearer dummy_token"}
    mock_user = MagicMock()
    mock_user.id = "admin_user"
    mock_user.tenant_id = tenant_1.id
    mock_user.role = "admin"
    mock_user.status = "active"
    mock_user.tenant.status = "active"

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user

        # 1. Setup mock data
        from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
        from app.infrastructure.database.repositories import DecisionRepository
        from app.infrastructure.database.models.decision import DecisionType
        
        domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Stats Domain")
        db.add(domain)
        await db.flush()

        bot_repo = BotRepository(db)
        v_repo = BotVersionRepository(db)
        d_repo = DecisionRepository(db)
        
        bot = await bot_repo.create({"domain_id": domain.id, "code": f"stat-bot-{uuid.uuid4().hex[:4]}", "name": "Stat Bot"}, tenant_id=tenant_1.id)
        version = await v_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
        
        session_id = str(uuid.uuid4())
        from app.infrastructure.database.models.runtime import RuntimeSession
        session = RuntimeSession(
            id=session_id, 
            bot_id=bot.id, 
            bot_version_id=version.id, 
            tenant_id=tenant_1.id,
            channel_code="webchat",
            lifecycle_state="idle"
        )
        db.add(session)
        await db.commit()
        
        from app.infrastructure.database.models.decision import RuntimeDecisionEvent
        await d_repo.create({
            "session_id": session_id,
            "bot_version_id": version.id,
            "tier_code": "fast_path",
            "decision_type": DecisionType.PROCEED,
            "estimated_cost": 0.0,
            "latency_ms": 50,
            "decision_reason": "Test turn"
        }, tenant_id=tenant_1.id)
        
        # 2. Call Stats API
        resp = await client.get(f"/api/v1/sessions/{session_id}/stats", headers=headers)
        assert resp.status_code == 200
