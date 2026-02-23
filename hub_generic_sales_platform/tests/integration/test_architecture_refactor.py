import pytest
import uuid
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.runtime import RuntimeSession, RuntimeTurn
from app.infrastructure.database.repositories.session_repo import SessionRepository
from app.core.shared.exceptions import ConcurrentUpdateError
from app.application.orchestrators.agent_orchestrator import AgentOrchestrator
from unittest.mock import AsyncMock, patch
from app.core import domain

@pytest.mark.asyncio
async def test_optimistic_locking(db: AsyncSession, tenant_1, bot_1):
    """Verify that concurrent updates trigger ConcurrentUpdateError"""
    # 1. Create a session
    session_id = str(uuid.uuid4())
    db_session = RuntimeSession(
        id=session_id,
        tenant_id=tenant_1.id,
        bot_id=bot_1.id,
        bot_version_id=str(uuid.uuid4()),
        channel_code="webchat",
        lifecycle_state="idle",
        version=0
    )
    db.add(db_session)
    await db.commit() # Commit to make it available for refresh
    
    # 2. Get two copies of the same session
    repo1 = SessionRepository(db)
    session1 = await repo1.get(session_id, tenant_id=tenant_1.id)
    
    # We need another session object with same data to simulate concurrent update
    session2 = await repo1.get(session_id, tenant_id=tenant_1.id)
    
    # 3. Update 1st copy
    await repo1.update(session1, {"lifecycle_state": "step_1"}, tenant_id=tenant_1.id)
    await db.commit()
    
    # 4. Try updating 2nd copy (which still has version 0)
    with pytest.raises(ConcurrentUpdateError):
        await repo1.update(session2, {"lifecycle_state": "step_2"}, tenant_id=tenant_1.id)
        await db.commit()

@pytest.mark.asyncio
async def test_transaction_rollback_on_orchestration_failure(db: AsyncSession, tenant_1, bot_1):
    """Verify that failure in orchestration rolls back user turn creation"""
    orchestrator = AgentOrchestrator(db)
    session_id = str(uuid.uuid4())
    
    # Create the session first
    session = RuntimeSession(
        id=session_id,
        tenant_id=tenant_1.id,
        bot_id=bot_1.id,
        bot_version_id=str(uuid.uuid4()),
        channel_code="webchat"
    )
    db.add(session)
    await db.commit()
    
    message = "trigger failure"
    
    # Mock _execute_orchestration to raise error
    with patch.object(AgentOrchestrator, "_execute_orchestration", side_effect=Exception("Orchestration Failed")):
        with pytest.raises(Exception, match="Orchestration Failed"):
            await orchestrator.run(message, session_id, "IDLE", tenant_1.id)
            
    # Check if turns were saved (using fresh session to ensure we check DB state)
    from sqlalchemy import select
    stmt = select(RuntimeTurn).where(RuntimeTurn.session_id == session_id)
    result = await db.execute(stmt)
    turns = result.scalars().all()
    
    assert len(turns) == 0, "No turns should be saved if orchestration failed"

@pytest.mark.asyncio
async def test_tool_idempotency(db: AsyncSession, tenant_1, bot_1):
    """Verify tool idempotency returns cached result"""
    # Create dummy session
    session_id = str(uuid.uuid4())
    session = RuntimeSession(
        id=session_id,
        tenant_id=tenant_1.id,
        bot_id=bot_1.id,
        bot_version_id=str(uuid.uuid4()),
        channel_code="webchat",
        lifecycle_state="idle"
    )
    db.add(session)
    await db.commit()
    
    # Mock tool registry and llm service
    with patch("app.application.orchestrators.agent_orchestrator.agent_tools") as mock_tools_orch, \
         patch("app.core.services.tool_executor.agent_tools") as mock_tools_exec:
        with patch("app.application.orchestrators.agent_orchestrator.get_llm_provider") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm_factory.return_value = mock_llm
            
            # Instantiate AFTER patching get_llm_provider
            orchestrator = AgentOrchestrator(db)
            
            # Clear idempotency cache to avoid interference
            from app.core.services.idempotency import get_idempotency_service
            await get_idempotency_service().clear_cache()
            
            # Setup LLM to call a tool
            from unittest.mock import MagicMock
            tool_call = MagicMock()
            tool_call.function.name = "search_offerings"
            tool_call.function.arguments = json.dumps({"query": "laptop"})
            
            mock_llm.generate_response.side_effect = [
                {"tool_calls": [tool_call], "usage": {}}, # 1st call triggers tool
                {"response": "Here is what I found", "usage": {}} # 2nd call finishes
            ]
            
            # Setup tool function
            tool_func = AsyncMock(return_value={"results": ["laptop 1"]})
            
            # Configure Executor's view of tools (for execution)
            mock_tools_exec.tools = {"search_offerings": {"func": tool_func}}
            
            # Configure Orchestrator's view of tools (for filtering)
            mock_tools_orch.get_tool_metadata.return_value = [{"name": "search_offerings"}]
            
            # Run orchestrator
            await orchestrator.run("looking for laptop", session_id, "idle", tenant_1.id)
            
            assert tool_func.call_count == 1
            
            # Reset mocks for 2nd run with SAME arguments in SAME session
            tool_func.reset_mock()
            mock_llm.generate_response.side_effect = [
                {"tool_calls": [tool_call], "usage": {}},
                {"response": "Cached response", "usage": {}}
            ]
            
            await orchestrator.run("looking for laptop again", session_id, "idle", tenant_1.id)
            
            # Tool should NOT be called again because of idempotency (cached result used)
            assert tool_func.call_count == 0
