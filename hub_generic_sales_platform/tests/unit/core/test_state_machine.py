"""Integration tests for State Machine & Skill Scoping - Sprint 5"""

import pytest
import json
import uuid
from unittest.mock import patch, AsyncMock
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.core.domain.runtime import LifecycleState
from app.core.domain.state_machine import StateMachine
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.infrastructure.database.repositories import SessionRepository
from app.infrastructure.database.models.knowledge import KnowledgeDomain

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_state_machine_core_logic():
    """Verify primary state machine routing logic"""
    # Test skill scoping
    idle_tools = StateMachine.get_allowed_tools("idle")
    assert "search_offerings" in idle_tools
    # Note: IDLE state allows compare_offerings per STATE_SKILL_MAP definition
    assert "compare_offerings" in idle_tools

    viewing_tools = StateMachine.get_allowed_tools("viewing")
    assert "compare_offerings" in viewing_tools
    assert "get_offering_details" in viewing_tools

    # Test transitions
    assert StateMachine.is_transition_valid("idle", "searching") is True
    assert StateMachine.is_transition_valid("idle", "purchasing") is False

@pytest.mark.asyncio
async def test_skill_scoping_in_orchestrator(db, tenant_1):
    """Ensure Agent only sees allowed tools based on state"""
    
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    session_repo = SessionRepository(db)
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Test")
    db.add(domain)
    await db.flush()
    
    bot = await bot_repo.create({"domain_id": domain.id, "code": "s5-bot", "name": "Sprint 5 Bot"}, tenant_id=tenant_1.id)
    version = await version_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
    
    orchestrator = HybridOrchestrator(db)
    
    # 1. Start in IDLE state (mock session state)
    resp = await orchestrator.handle_message(tenant_1.id, bot.id, "Hello")
    session_id = resp["session_id"]
    
    # Verify starting state is IDLE
    sess = await session_repo.get(session_id, tenant_id=tenant_1.id)
    assert sess.lifecycle_state.lower() == LifecycleState.IDLE.value.lower()

    # 2. Try an action that requires a different state (AI tries to call trigger_web_hook in IDLE - not allowed)
    mock_tool_call = AsyncMock()
    mock_tool_call.function.name = "trigger_web_hook"
    mock_tool_call.function.arguments = '{"url": "https://example.com/webhook", "payload": {}}'
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        # Simulate LLM trying to call trigger_web_hook (only allowed in PURCHASING state)
        mock_gen.return_value = {
            "response": "I will trigger the webhook.",
            "tool_calls": [mock_tool_call],
            "usage": {"total_tokens": 10}
        }
        
        resp_illegal = await orchestrator.handle_message(tenant_1.id, bot.id, "Complete purchase", session_id=session_id)
        
        # Check DB state
        sess = await session_repo.get(session_id, tenant_id=tenant_1.id)
        
        # Should be rejected with a polite explanation
        assert "không được phép thực hiện trong trạng thái hiện tại" in resp_illegal["response"].lower() or "not allowed" in resp_illegal["response"].lower()
        assert sess.lifecycle_state.lower() == LifecycleState.IDLE.value.lower()

@pytest.mark.asyncio
async def test_agent_orchestrator_skill_scoping(db):
    """Verify that AgentOrchestrator correctly filters tools based on state"""
    from app.application.orchestrators.agent_orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator(db)
    
    # IDLE state: allows search_offerings and compare_offerings (per STATE_SKILL_MAP)
    allowed_idle = StateMachine.get_allowed_tools("idle")
    assert "search_offerings" in allowed_idle
    assert "compare_offerings" in allowed_idle
    assert "trigger_web_hook" not in allowed_idle  # Not allowed in IDLE

    # VIEWING state: should allow details and compare
    allowed_viewing = StateMachine.get_allowed_tools("viewing")
    assert "get_offering_details" in allowed_viewing
    assert "compare_offerings" in allowed_viewing
    
    # PURCHASING state: allows trigger_web_hook + search/get_details (Rigidity Fix per plan)
    allowed_purchasing = StateMachine.get_allowed_tools("purchasing")
    assert "trigger_web_hook" in allowed_purchasing
    assert "search_offerings" in allowed_purchasing
    assert "get_offering_details" in allowed_purchasing

@pytest.mark.asyncio
async def test_catalog_handler_transitions(db, tenant_1):
    """Verify that catalog tools return the expected state transitions"""
    from app.application.services.catalog_state_handler import CatalogStateHandler
    handler = CatalogStateHandler(db)
    
    # Mock session
    from app.core.domain.runtime import RuntimeSession
    session = RuntimeSession(id="test-session", tenant_id=tenant_1.id, bot_id="test", bot_version_id="v1", channel_code="WEB")

    # Test Details transition - cần tạo offering trước để search có kết quả
    from app.infrastructure.database.repositories import OfferingRepository, OfferingVersionRepository
    from app.infrastructure.database.models.offering import OfferingStatus
    prod_repo = OfferingRepository(db)
    ver_repo = OfferingVersionRepository(db)
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Test")
    db.add(domain)
    await db.flush()
    
    product = await prod_repo.create({
        "domain_id": domain.id, 
        "code": "p1", 
        "status": "active"
    }, tenant_id=tenant_1.id)
    await ver_repo.create({
        "offering_id": product.id,
        "version": 1,
        "name": "P1",
        "description": "Product P1 for search test",
        "status": OfferingStatus.ACTIVE
    })
    
    # Test Search transition - query phải match product để có kết quả và return SEARCHING
    resp_search = await handler.handle_search_offerings(query="p1", session=session)
    assert resp_search["new_state"] == LifecycleState.SEARCHING
    
    resp_details = await handler.handle_get_offering_details(offering_code="p1", session=session)
    assert resp_details["new_state"] == LifecycleState.VIEWING

@pytest.mark.asyncio
async def test_state_transition_journey(db, tenant_1):
    """Simulate a journey: Greeting -> Search -> Viewing"""
    
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    session_repo = SessionRepository(db)
    
    domain = KnowledgeDomain(code=f"dom-{uuid.uuid4().hex[:4]}", name="Test")
    db.add(domain)
    await db.flush()
    
    bot = await bot_repo.create({
        "domain_id": domain.id, 
        "code": "journey-bot", 
        "name": "Journey Bot"
    }, tenant_id=tenant_1.id)
    await version_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
    
    # Tạo product trước để search "phone" có kết quả -> return SEARCHING
    from app.infrastructure.database.repositories import OfferingRepository, OfferingVersionRepository
    from app.infrastructure.database.models.offering import OfferingStatus
    prod_repo = OfferingRepository(db)
    ver_repo = OfferingVersionRepository(db)
    product = await prod_repo.create({
        "domain_id": domain.id, "code": "iphone15", "status": "active"
    }, tenant_id=tenant_1.id)
    await ver_repo.create({
        "offering_id": product.id, "version": 1, "name": "iPhone 15",
        "description": "Smartphone with phone capabilities",
        "status": OfferingStatus.ACTIVE
    })
    
    orchestrator = HybridOrchestrator(db)
    
    # Step 1: Search (IDLE -> SEARCHING)
    mock_tool_search = AsyncMock()
    mock_tool_search.function.name = "search_offerings"
    mock_tool_search.function.arguments = '{"query": "phone"}'
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            "response": "Found products.",
            "tool_calls": [mock_tool_search],
            "usage": {"total_tokens": 10}
        }
        
        resp_search = await orchestrator.handle_message(tenant_1.id, bot.id, "Find me a phone")
        session_id = resp_search["session_id"]
        
        # Verify state updated to SEARCHING (flow_step có thể lưu "searching" hoặc "SEARCHING")
        sess = await session_repo.get(session_id, tenant_id=tenant_1.id)
        assert sess.lifecycle_state.upper() == LifecycleState.SEARCHING.value.upper()

    # Step 2: Get Details (SEARCHING -> VIEWING) - product đã tạo ở Step 1
    mock_tool_details = AsyncMock()
    mock_tool_details.function.name = "get_offering_details"
    mock_tool_details.function.arguments = '{"offering_code": "iphone15"}'
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            "response": "Here are the details.",
            "tool_calls": [mock_tool_details],
            "usage": {"total_tokens": 10}
        }
        
        await orchestrator.handle_message(tenant_1.id, bot.id, "Show me iPhone 15", session_id=session_id)
        
        # Check state updated to VIEWING (flow_step có thể lowercase)
        sess = await session_repo.get(session_id, tenant_id=tenant_1.id)
        assert sess.lifecycle_state.upper() == LifecycleState.VIEWING.value.upper()
