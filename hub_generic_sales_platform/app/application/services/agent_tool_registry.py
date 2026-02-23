"""Agent Tool Registry - Cơ chế đăng ký công cụ cho Agent (2026 Style)"""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry quản lý các công cụ mà Agent có thể sử dụng"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: Optional[str] = None, description: Optional[str] = None, capability: str = "core"):
        """Decorator để biến method thành Tool, có hỗ trợ nhãn Capability"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or "Không có mô tả."
            
            signature = inspect.signature(func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in signature.parameters.items():
                if param_name == "self": continue
                
                parameters["properties"][param_name] = {
                    "type": "string",
                    "description": f"Tham số {param_name}"
                }
                if param.default is inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            self.tools[tool_name] = {
                "name": tool_name,
                "description": tool_description.strip(),
                "parameters": parameters,
                "capability": capability, # Mới: liên kết với Capability
                "func": func
            }
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_tool_metadata(self, enabled_capabilities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Trả về metadata của các tool đang được bật cho bot/tenant.
        Nếu enabled_capabilities là None, trả về toàn bộ core tools.
        """
        if enabled_capabilities is None:
            enabled_capabilities = ["core"]
        else:
            if "core" not in enabled_capabilities:
                enabled_capabilities.append("core")

        return [
            {
                "name": info["name"],
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for info in self.tools.values()
            if info["capability"] in enabled_capabilities
        ]


# Global registry
agent_tools = ToolRegistry()
