from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import json
import hashlib
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.domain.runtime import LifecycleState
from app.application.services.agent_tool_registry import agent_tools
from app.core.services.idempotency import get_idempotency_service

logger = logging.getLogger(__name__)

# Map tool param names -> context_slot keys (fallback khi LLM không truyền đủ)
PARAM_SLOT_MAP: Dict[str, List[str]] = {
    "offering_id": ["offering_id", "product_id"],
    "offering_code": ["offering_code", "product_code"],
    "product_id": ["product_id", "offering_id"],
    "product_code": ["product_code", "offering_code"],
    "query": ["last_search_query", "offering_code"],
}


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None
    ui_data: Optional[Dict] = None
    new_state: Optional[Any] = None


def _resolve_args_from_slots(
    tool_name: str,
    tool_args: Dict[str, Any],
    context_slots: List[Any],
) -> Dict[str, Any]:
    """
    Bổ sung tool_args từ context_slots khi thiếu argument.
    Tool mới khi khai báo nên dùng @agent_tools.register_tool và rely on fallback này.
    """
    slots_dict: Dict[str, str] = {}
    for slot in context_slots or []:
        key = getattr(slot, "key", None) or getattr(slot, "slot_key", None)
        value = getattr(slot, "value", None) or getattr(slot, "slot_value", None)
        if key and value and getattr(slot, "is_active", lambda: True)():
            slots_dict[str(key)] = str(value)

    merged = dict(tool_args)
    tool_info = agent_tools.tools.get(tool_name, {})
    required = tool_info.get("parameters", {}).get("required", [])

    for param in required:
        val = merged.get(param)
        if val is not None and str(val).strip():
            continue
        # Thử từ slot trực tiếp
        val = slots_dict.get(param)
        if not val and param in PARAM_SLOT_MAP:
            for slot_key in PARAM_SLOT_MAP[param]:
                val = slots_dict.get(slot_key)
                if val:
                    break
        if val:
            merged[param] = val
            logger.debug(f"Tool {tool_name}: filled {param} from context_slots")

    return merged


class ToolExecutor:
    """
    Handles tool validation, idempotency, and execution.
    Fallback: thiếu argument → lấy từ context_slots.
    """
    def __init__(self, db: AsyncSession, tool_handlers: Dict[str, Any]):
        self.db = db
        self.tool_handlers = tool_handlers
        self.idempotency_service = get_idempotency_service()

    async def execute(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        session: Any,
        allowed_tools: List[str],
        context_data: Dict[str, Any] = None
    ) -> ToolResult:
        # 1. Validation
        if tool_name not in allowed_tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' is not allowed in current state."
            )

        # 2. Fallback: thiếu argument → context_slots
        context_data = context_data or {}
        slots = context_data.get("context_slots", [])
        resolved_args = _resolve_args_from_slots(tool_name, tool_args, slots)

        # 3. Idempotency Check
        args_str = json.dumps(resolved_args, sort_keys=True)
        idempotency_key = hashlib.md5(f"{session.id}:{tool_name}:{args_str}".encode()).hexdigest()

        cached = await self.idempotency_service.get_cached_result(idempotency_key)
        if cached:
            logger.info(f"Using cached result for tool '{tool_name}'")
            return self._wrap_observation(cached)

        # 4. Execution
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return ToolResult(success=False, data=None, error=f"No handler registered for tool '{tool_name}'")

        try:
            func = agent_tools.tools[tool_name]["func"]
            observation = await func(
                handler,
                session=session,
                **context_data,
                **resolved_args
            )
            
            # 4. Cache and Wrap
            await self.idempotency_service.cache_result(idempotency_key, observation)
            return self._wrap_observation(observation)
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))

    def _wrap_observation(self, observation: Any) -> ToolResult:
        if isinstance(observation, dict):
            err = observation.get("error")
            if err is None and not observation.get("success", True):
                err = observation.get("response") or observation.get("message")
            return ToolResult(
                success=observation.get("success", True),
                data=observation,
                ui_data=observation.get("g_ui_data"),
                error=err,
                new_state=observation.get("new_state")
            )
        return ToolResult(success=True, data=observation)
