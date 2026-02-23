from typing import Dict, Any, Optional
from app.application.services.agent_tool_registry import agent_tools
from app.core.domain.runtime import Intent, LifecycleState
from app.infrastructure.llm.factory import get_llm_provider
import logging

logger = logging.getLogger(__name__)

class IntentHandler:
    """
    Extracts Intent from user messages using LLM.
    Maps natural language to Intent enum for flow validation.
    """
    
    def __init__(self):
        self.llm_provider = get_llm_provider()
    
    async def extract_intent(
        self,
        message: str,
        current_state: LifecycleState,
        context: dict = None
    ) -> Optional[Intent]:
        """
        Uses LLM to classify user message into Intent enum.
        
        Args:
            message: User's input message
            current_state: Current conversation state
            context: Optional context from slots
        
        Returns:
            Intent enum or None if unrecognized
        """
        intent_list = [intent.value for intent in Intent]
        
        system_prompt = f"""
        You are an intent classifier for a Vietnamese sales bot.
        Current conversation state: {current_state.value}
        
        Classify the user's message into ONE of these intents:
        {', '.join(intent_list)}
        
        Return ONLY the intent name (e.g., SEARCH_PRODUCT), no explanation.
        If no intent matches clearly, return "UNKNOWN".
        """
        
        try:
            # Simple LLM call for intent classification (no tools)
            result = await self.llm_provider.generate_response(
                system_prompt=system_prompt.strip(),
                user_message=message,
            )
            response = result.get("response", "") or ""
            intent_value = response.strip().upper()
            
            # Try to map to Intent enum
            try:
                return Intent(intent_value)
            except ValueError:
                logger.debug(f"Unrecognized intent: {intent_value} from message: {message[:50]}")
                return None
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            return None
    
    @agent_tools.register_tool(
        name="submit_intent",
        description="Gửi ý định (Intent) của người dùng để hệ thống quyết định bước tiếp theo. Dùng khi không cần tra cứu dữ liệu nhưng cần chuyển trạng thái (VD: Chốt mua, Hủy, Chào hỏi).",
        capability="core"
    )
    async def handle_submit_intent(
        self,
        intent_code: str, # Phải là một trong các giá trị của Intent Enum: GREETING, CONFIRM, CANCEL, vv.
        **kwargs
    ) -> Dict[str, Any]:
        """Xử lý khai báo intent từ AI"""
        # Trả về intent_code để Orchestrator có thể nhận diện và chuyển cho FlowDecisionService
        return {
            "success": True,
            "intent": intent_code.upper()
        }
