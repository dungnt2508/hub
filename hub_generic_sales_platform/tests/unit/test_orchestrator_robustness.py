import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.application.orchestrators.agent_orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_agent_orchestrator_malformed_json_from_llm():
    db = MagicMock()
    db.begin.return_value.__aenter__ = AsyncMock()
    db.begin.return_value.__aexit__ = AsyncMock()
    
    orchestrator = AgentOrchestrator(db)
    
    # Mock repositories
    orchestrator.turn_repo.create = AsyncMock()
    orchestrator.turn_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.slots_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.session_repo.get = AsyncMock(return_value=MagicMock(bot_id="bot-1"))
    
    # Mock Bot object properly
    mock_bot = MagicMock()
    mock_bot.name = "Test Bot"
    mock_bot.capabilities = ["core"]
    mock_bot.domain.name = "Test Domain"
    
    # Mock LLM service directly on the orchestrator
    orchestrator.llm_service = AsyncMock()
    orchestrator.llm_service.generate_response.return_value = {
        "response": "This is a simple message",
        "usage": {"total_tokens": 100}
    }
    
    with patch("app.infrastructure.database.repositories.BotRepository.get", new_callable=AsyncMock) as mock_bot_get:
        mock_bot_get.return_value = mock_bot
        
        result = await orchestrator.run("hello", "sid", "idle", "tid")
        
        assert result["response"] == "This is a simple message"
        assert result["usage"]["total_tokens"] == 100

@pytest.mark.asyncio
async def test_agent_orchestrator_invalid_tool_call_structure():
    db = MagicMock()
    db.begin.return_value.__aenter__ = AsyncMock()
    db.begin.return_value.__aexit__ = AsyncMock()
    
    orchestrator = AgentOrchestrator(db)
    
    orchestrator.turn_repo.create = AsyncMock()
    orchestrator.turn_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.slots_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.session_repo.get = AsyncMock(return_value=MagicMock(bot_id="bot-1"))

    mock_bot = MagicMock()
    mock_bot.name = "Test Bot"
    mock_bot.capabilities = ["core"]
    mock_bot.domain.name = "Test Domain"

    orchestrator.llm_service = AsyncMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search_offerings"
    mock_tool_call.function.arguments = "invalid { json"
    
    orchestrator.llm_service.generate_response.return_value = {
        "tool_calls": [mock_tool_call],
        "usage": {"total_tokens": 50}
    }

    with patch("app.infrastructure.database.repositories.BotRepository.get", new_callable=AsyncMock) as mock_bot_get:
        mock_bot_get.return_value = mock_bot
        
        result = await orchestrator.run("test", "sid", "idle", "tid")
        assert "Lỗi xử lý phản hồi từ AI" in result["response"]

@pytest.mark.asyncio
async def test_agent_orchestrator_empty_response():
    db = MagicMock()
    db.begin.return_value.__aenter__ = AsyncMock()
    db.begin.return_value.__aexit__ = AsyncMock()
    
    orchestrator = AgentOrchestrator(db)
    
    orchestrator.turn_repo.create = AsyncMock()
    orchestrator.turn_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.slots_repo.get_by_session = AsyncMock(return_value=[])
    orchestrator.session_repo.get = AsyncMock(return_value=MagicMock(bot_id="bot-1"))

    mock_bot = MagicMock()
    mock_bot.name = "Test Bot"
    mock_bot.capabilities = ["core"]
    mock_bot.domain.name = "Test Domain"

    orchestrator.llm_service = AsyncMock()
    orchestrator.llm_service.generate_response.return_value = {
        "response": None,
        "usage": {"total_tokens": 0}
    }

    with patch("app.infrastructure.database.repositories.BotRepository.get", new_callable=AsyncMock) as mock_bot_get:
        mock_bot_get.return_value = mock_bot
        
        result = await orchestrator.run("test", "sid", "idle", "tid")
        assert "Tôi không thể xử lý yêu cầu này" in result["response"]
