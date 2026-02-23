import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.core.domain.runtime import LifecycleState

@pytest.mark.asyncio
async def test_multi_turn_state_progression():
    db = MagicMock()
    # Mock db.begin() context manager (AsyncContextManager)
    db.begin.return_value = AsyncMock()
    db.begin.return_value.__aenter__ = AsyncMock()
    db.begin.return_value.__aexit__ = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    
    orchestrator = HybridOrchestrator(db)
    
    tenant_id = str(uuid.uuid4())
    bot_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    bot_version_id = str(uuid.uuid4())
    
    # Mock _finalize_response to avoid repo calls
    orchestrator._finalize_response = AsyncMock(side_effect=lambda sid, bvid, resp, tier, **kwargs: {
        "response": resp,
        "session_id": sid,
        "tier": tier
    })
    
    # Mock Session Service
    orchestrator.session_service.get_or_create_session = AsyncMock(return_value={
        "session_id": session_id,
        "bot_version_id": bot_version_id
    })
    orchestrator.session_service.log_user_message = AsyncMock()
    
    # Mock Session State Handler (Current state IDLE)
    mock_session_obj = MagicMock()
    mock_session_obj.lifecycle_state = LifecycleState.IDLE
    orchestrator.session_state_handler.read_session_state = AsyncMock(return_value=mock_session_obj)
    orchestrator.session_state_handler.update_lifecycle_state = AsyncMock()
    orchestrator.session_state_handler.update_flow_step = orchestrator.session_state_handler.update_lifecycle_state
    
    # Mock Semantic Cache & FAQ (Miss)
    orchestrator.semantic_cache_service.find_match = AsyncMock(return_value=None)
    orchestrator.faq_repo.semantic_search = AsyncMock(return_value=[])
    
    # Turn 1: User asks to search -> Agent recommends BROWSING
    orchestrator.agent_orchestrator.run = AsyncMock(return_value={
        "response": "Here are some cars",
        "new_state": LifecycleState.BROWSING,
        "usage": {"total_tokens": 100}
    })
    
    # Patch get_llm_provider for the embedding call in HybridOrchestrator
    with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.get_embedding.return_value = [0.1] * 1536
        mock_llm_factory.return_value = mock_llm
        
        # Execute message
        result = await orchestrator.handle_message(tenant_id, bot_id, "Find me a car", session_id)
        
        # Verify Turn 1
        assert "cars" in result["response"]
        # Verify background task or sync call for state update
        orchestrator.session_state_handler.update_lifecycle_state.assert_called_with(session_id, LifecycleState.BROWSING, tenant_id)
        
        # Turn 2: State is now BROWSING, user asks for details -> Agent recommends VIEWING
        mock_session_obj.lifecycle_state = LifecycleState.BROWSING
        orchestrator.agent_orchestrator.run.return_value = {
            "response": "This car is great",
            "new_state": LifecycleState.VIEWING,
            "usage": {"total_tokens": 100}
        }
        
        result = await orchestrator.handle_message(tenant_id, bot_id, "Tell me more about the first one", session_id)
        
        # Verify Turn 2
        assert "great" in result["response"]
        orchestrator.session_state_handler.update_lifecycle_state.assert_called_with(session_id, LifecycleState.VIEWING, tenant_id)
