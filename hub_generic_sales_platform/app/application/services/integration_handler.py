"""Integration Handler - External tools (Webhook, API)"""

import json
import httpx
from typing import Dict, Any, Optional
from app.application.services.agent_tool_registry import agent_tools
from typing import Dict, Any, Optional
from app.application.services.agent_tool_registry import agent_tools
from app.core.shared.logger import get_logger

logger = get_logger(__name__)


class IntegrationHandler:
    """
    Integration Handler (Async Implementation)
    
    Cung cấp các công cụ để Agent tương tác với hệ thống bên ngoài.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @agent_tools.register_tool(
        name="trigger_web_hook",
        description="Kích hoạt một webhook bên ngoài (ví dụ n8n, Make) để thực hiện quy trình tự động."
    )
    async def handle_trigger_webhook(
        self,
        webhook_url: str,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Kích hoạt Webhook (Async)"""
        if not webhook_url:
            return {"success": False, "error": "URL webhook không hợp lệ."}
            
        try:
            # Nếu không có payload, tự động gom context hữu ích gửi đi
            if payload is None:
                session = kwargs.get("session")
                payload = {
                    "source": "iris_hub_agent",
                    "event": "tool_trigger",
                    "session_id": str(session.id) if session else "unknown",
                    "raw_message": kwargs.get("message", "")
                }
            
            logger.info(f"Triggering webhook: {webhook_url}")
            
            response = await self.client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Webhook đã được kích hoạt thành công.",
                "response_data": response.json() if "application/json" in response.headers.get("Content-Type", "") else response.text
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook HTTP error: {e}")
            return {"success": False, "error": f"Lỗi HTTP: {e.response.status_code}", "detail": e.response.text}
        except Exception as e:
            logger.error(f"Webhook unexpected error: {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Đóng kết nối client"""
        await self.client.aclose()
