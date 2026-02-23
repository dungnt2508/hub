import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.services.tool_executor import ToolExecutor, ToolResult
from app.core.domain.runtime import LifecycleState

@pytest.mark.asyncio
async def test_tool_executor_allowed_tool():
    db = AsyncMock()
    mock_handler = MagicMock()
    tool_handlers = {"search_offerings": mock_handler}
    
    executor = ToolExecutor(db, tool_handlers)
    session = MagicMock(id="session-1")
    allowed_tools = ["search_offerings"]
    
    # Mock tool registry
    with patch("app.core.services.tool_executor.agent_tools") as mock_registry:
        mock_func = AsyncMock(return_value={"success": True, "data": "found"})
        mock_registry.tools = {"search_offerings": {"func": mock_func}}
        
        # Mock idempotency (no cache)
        with patch.object(executor.idempotency_service, "get_cached_result", new_callable=AsyncMock) as mock_get, \
             patch.object(executor.idempotency_service, "cache_result", new_callable=AsyncMock) as mock_cache:
            mock_get.return_value = None
            
            result = await executor.execute(
                tool_name="search_offerings",
                tool_args={"query": "laptop"},
                session=session,
                allowed_tools=allowed_tools
            )
            
            assert result.success is True
            assert result.data["data"] == "found"
            mock_func.assert_called_once()
            mock_cache.assert_called_once()

@pytest.mark.asyncio
async def test_tool_executor_disallowed_tool():
    db = AsyncMock()
    executor = ToolExecutor(db, {})
    session = MagicMock(id="session-1")
    allowed_tools = ["other_tool"]
    
    result = await executor.execute(
        tool_name="forbidden_tool",
        tool_args={},
        session=session,
        allowed_tools=allowed_tools
    )
    
    assert result.success is False
    assert "not allowed" in result.error

@pytest.mark.asyncio
async def test_tool_executor_idempotency_hit():
    db = AsyncMock()
    executor = ToolExecutor(db, {"some_tool": MagicMock()})
    session = MagicMock(id="session-1")
    allowed_tools = ["some_tool"]
    
    cached_data = {"success": True, "data": "cached", "new_state": "viewing"}
    with patch.object(executor.idempotency_service, "get_cached_result", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = cached_data
        
        result = await executor.execute(
            tool_name="some_tool",
            tool_args={"id": 123},
            session=session,
            allowed_tools=allowed_tools
        )
        
        assert result.success is True
        assert result.data["data"] == "cached"
        assert result.new_state == "viewing"

@pytest.mark.asyncio
async def test_tool_executor_handler_error():
    db = AsyncMock()
    mock_handler = MagicMock()
    tool_handlers = {"error_tool": mock_handler}
    
    executor = ToolExecutor(db, tool_handlers)
    session = MagicMock(id="session-1")
    allowed_tools = ["error_tool"]
    
    with patch("app.core.services.tool_executor.agent_tools") as mock_registry:
        mock_func = AsyncMock(side_effect=Exception("Handler Crash"))
        mock_registry.tools = {"error_tool": {"func": mock_func}}
        executor.idempotency_service.get_cached_result = AsyncMock(return_value=None)
        
        result = await executor.execute(
            tool_name="error_tool",
            tool_args={},
            session=session,
            allowed_tools=allowed_tools
        )
        
        assert result.success is False
        assert "Handler Crash" in result.error


@pytest.mark.asyncio
async def test_tool_executor_context_slots_fallback():
    """Sprint 3: Fallback thiếu argument từ context_slots"""
    from app.core.services.tool_executor import _resolve_args_from_slots

    class MockSlot:
        def __init__(self, k, v):
            self.key = k
            self.value = v
        def is_active(self):
            return True

    slots = [MockSlot("offering_code", "Mazda3")]
    tool_args = {}
    with patch("app.core.services.tool_executor.agent_tools") as mock_reg:
        mock_reg.tools = {"test_tool": {"parameters": {"required": ["offering_code"]}}}
        resolved = _resolve_args_from_slots("test_tool", tool_args, slots)
    assert resolved["offering_code"] == "Mazda3"


@pytest.mark.asyncio
async def test_tool_executor_context_slots_fallback_via_param_map():
    """Sprint 3: offering_id lấy từ slot product_id (PARAM_SLOT_MAP)"""
    from app.core.services.tool_executor import _resolve_args_from_slots

    class MockSlot:
        def __init__(self, k, v):
            self.key = k
            self.value = v
        def is_active(self):
            return True

    slots = [MockSlot("product_id", "uuid-123")]
    tool_args = {}
    with patch("app.core.services.tool_executor.agent_tools") as mock_reg:
        mock_reg.tools = {"test_tool": {"parameters": {"required": ["offering_id"]}}}
        resolved = _resolve_args_from_slots("test_tool", tool_args, slots)
    assert resolved["offering_id"] == "uuid-123"
