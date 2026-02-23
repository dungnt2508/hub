import pytest
import time
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import BackgroundTasks
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.core import domain
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.infrastructure.database.models.knowledge import KnowledgeDomain
from app.core.shared.exceptions import EntityNotFoundError

@pytest.fixture
async def setup_bot_with_version(db, tenant_1):
    """Fixture to ensure bot has an active version"""
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    
    kd = KnowledgeDomain(code=f"kd-{uuid.uuid4().hex[:4]}", name="Test KD")
    db.add(kd)
    await db.flush()
    
    # Passing tenant_id as kwarg for BaseRepository.create
    bot = await bot_repo.create({
        "code": f"bot-{uuid.uuid4().hex[:4]}", 
        "name": "Test Bot",
        "domain_id": kd.id
    }, tenant_id=tenant_1.id)
    
    version = await version_repo.create({
        "bot_id": bot.id, 
        "version": 1, 
        "is_active": True
    })
    return bot, version

@pytest.mark.asyncio
async def test_handle_message_session_error(db):
    """Test when session service returns an error"""
    orchestrator = HybridOrchestrator(db)
    
    with patch.object(orchestrator.session_service, 'get_or_create_session', new_callable=AsyncMock) as mock_session:
        # Mocking error response from SessionService
        mock_session.side_effect = EntityNotFoundError("Bot", "bot_id")
        
        with pytest.raises(EntityNotFoundError):
            await orchestrator.handle_message("tenant_id", "bot_id", "hello")

@pytest.mark.asyncio
async def test_hybrid_flow_with_background_tasks(db, tenant_1, setup_bot_with_version):
    """Test finalize_response and hits with background tasks enabled"""
    bot, version = setup_bot_with_version
    orchestrator = HybridOrchestrator(db)
    bg_tasks = BackgroundTasks()
    
    # Tier 2 Seed: Mock vector and hits
    mock_vector = [0.1] * 1536
    
    with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.get_embedding = AsyncMock(return_value=mock_vector)
        mock_get_llm.return_value = mock_llm
        
        # Mocking cache hit qua semantic_cache_service.find_match
        mock_cached = MagicMock(id="cache_id", response_text="Cached answer")
        with patch.object(orchestrator.semantic_cache_service, 'find_match', new_callable=AsyncMock) as mock_find:
            mock_find.return_value = mock_cached
            
            resp = await orchestrator.handle_message(
                tenant_1.id, bot.id, "test message", 
                session_id=None, # Ensure session creation happens
                background_tasks=bg_tasks
            )
            
            assert resp["response"] == "Cached answer"
            assert resp["metadata"]["tier"] == "knowledge_path"
            # Verify that tasks were added to background_tasks
            assert len(bg_tasks.tasks) >= 2

@pytest.mark.asyncio
async def test_agent_path_state_transition(db, tenant_1, setup_bot_with_version):
    """Test state transition suggested by agent"""
    bot, version = setup_bot_with_version
    orchestrator = HybridOrchestrator(db)
    
    # Mocking AgentOrchestrator.run
    with patch.object(orchestrator.agent_orchestrator, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "I'll help you search",
            "new_state": domain.LifecycleState.SEARCHING,
            "usage": {"total_tokens": 500}
        }
        
        # We need to bypass Cache and FAQ hits to reach Agentic Path
        with patch.object(orchestrator, '_check_social_patterns', return_value=None):
            with patch.object(orchestrator.semantic_cache_service, 'find_match', new_callable=AsyncMock, return_value=None):
                with patch.object(orchestrator.faq_repo, 'semantic_search', new_callable=AsyncMock, return_value=[]):
                    # We also need to mock get_embedding for Knowledge Path check
                    with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm:
                        mock_llm = AsyncMock()
                        mock_llm.get_embedding = AsyncMock(return_value=[0.1]*1536)
                        mock_get_llm.return_value = mock_llm
                        
                        resp = await orchestrator.handle_message(tenant_1.id, bot.id, "search products")
                        
                        assert resp["response"] == "I'll help you search"
                        assert resp["metadata"]["tier"] == "agentic_path"
                        
                        cost = float(resp["metadata"]["cost"].replace("$", ""))
                        assert cost > 0

@pytest.mark.asyncio
async def test_social_patterns_edge_cases(db):
    """Test _check_social_patterns logic"""
    orchestrator = HybridOrchestrator(db)
    
    # Test multiple patterns
    patterns = {
        r"^(chào|hi)": "Xin chào!",
        r"tạm biệt": "Hẹn gặp lại!"
    }
    with patch.object(orchestrator.settings, 'social_patterns', patterns):
        assert orchestrator._check_social_patterns("Hi there") == "Xin chào!"
        assert orchestrator._check_social_patterns("Chào bạn") == "Xin chào!"
        assert orchestrator._check_social_patterns("Thôi tạm biệt nhá") == "Hẹn gặp lại!"
        assert orchestrator._check_social_patterns("Hỏi cái này tí") is None

@pytest.mark.asyncio
async def test_finalize_response_formatting(db):
    """Test that finalize_response correctly formats metadata"""
    orchestrator = HybridOrchestrator(db)
    
    resp = await orchestrator._finalize_response(
        session_id="session_123",
        bot_version_id="version_456",
        response="Test response",
        tier="test_tier",
        decision_type=domain.DecisionType.PROCEED,
        cost=1.234567,
        start_time=time.time() - 0.5,
        usage={"prompt_tokens": 10}
    )
    
    assert resp["metadata"]["tier"] == "test_tier"
    assert resp["metadata"]["cost"] == "$1.23457"
    assert resp["metadata"]["latency_ms"] >= 500
    assert resp["metadata"]["usage"]["prompt_tokens"] == 10
