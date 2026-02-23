import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.services.agent_tool_registry import agent_tools
from app.application.services.catalog_state_handler import CatalogStateHandler
from app.application.services.financial_state_handler import FinancialStateHandler
from app.application.services.auto_state_handler import AutoStateHandler
from app.application.services.education_state_handler import EducationStateHandler
from app.application.services.integration_handler import IntegrationHandler
from app.infrastructure.database.repositories import ContextSlotRepository, SessionRepository, ConversationTurnRepository
from app.core import domain
from app.infrastructure.llm.factory import get_llm_provider
from app.core.domain.state_machine import StateMachine
from app.core.services.tool_executor import ToolExecutor
from app.application.services.intent_handler import IntentHandler
from app.core.shared.db_utils import transaction_scope


class AgentOrchestrator:
    """
    Agent Orchestrator (Async Implementation)
    
    Điều phối luồng Agentic: Think -> Act -> Observe.
    Sử dụng LLMService để suy luận thông minh khi các tier trước thất bại.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Khởi tạo các handlers
        self.catalog_handler = CatalogStateHandler(db)
        self.financial_handler = FinancialStateHandler()
        self.auto_handler = AutoStateHandler()
        self.education_handler = EducationStateHandler()
        self.integration_handler = IntegrationHandler()
        self.intent_handler = IntentHandler()
        self.llm_service = get_llm_provider()
        
        self.session_repo = SessionRepository(db)
        self.turn_repo = ConversationTurnRepository(db)
        self.slots_repo = ContextSlotRepository(db)
        
        
        self.tool_handlers = {
            "search_offerings": self.catalog_handler,
            "get_offering_details": self.catalog_handler,
            "compare_offerings": self.catalog_handler,
            "trigger_web_hook": self.integration_handler,
            "get_market_data": self.financial_handler,
            "get_strategic_analysis": self.financial_handler,
            "trade_in_valuation": self.auto_handler,
            "credit_scoring": self.financial_handler,
            "assessment_test": self.education_handler,
            "submit_intent": self.intent_handler
        }
        self.tool_executor = ToolExecutor(db, self.tool_handlers)
        self.logger = logging.getLogger(__name__)

    async def run(self, message: str, session_id: str, state_code: Any, tenant_id: str) -> Dict[str, Any]:
        """EntryPoint Agentic Workflow (Async) - Wrapped in Transaction to ensure Atomicity"""
        async with transaction_scope(self.db):
            # 1. Save User Message
            await self.turn_repo.create({
                "session_id": session_id,
                "speaker": domain.Speaker.USER,
                "message": message
            }, tenant_id=tenant_id)

            # 2. Execute Orchestration
            result = await self._execute_orchestration(message, session_id, state_code, tenant_id)
            
            # 3. Save Bot Response
            await self.turn_repo.create({
                "session_id": session_id,
                "speaker": domain.Speaker.BOT,
                "message": result.get("response", "Tôi không thể xử lý yêu cầu này."),
                "ui_metadata": result.get("g_ui_data")
            }, tenant_id=tenant_id)
            
            return result

    async def _execute_orchestration(self, message: str, session_id: str, state_code: Any, tenant_id: str) -> Dict[str, Any]:
        """Core Orchestration Logic without independent transaction management"""
        # 2. Context Snapshotting (Slots)
        slots = await self.slots_repo.get_by_session(session_id, tenant_id=tenant_id)
        context_snapshot = {s.key: s.value for s in slots if s.is_active()}
        
        # 3. Conversation History
        recent_turns = await self.turn_repo.get_by_session(session_id, tenant_id=tenant_id, limit=10)
        
        history = [
            {"role": "user" if t.speaker == domain.Speaker.USER else "assistant", "content": t.message}
            for t in recent_turns
        ]
        
        # 3. Bot Context
        session = await self.session_repo.get(session_id, tenant_id=tenant_id)
        if not session:
             return {"response": "Lỗi: Không tìm thấy session.", "usage": {}}

        from app.infrastructure.database.repositories import BotRepository
        bot_repo = BotRepository(self.db)
        bot = await bot_repo.get(session.bot_id, tenant_id=tenant_id)
        bot_name = bot.name if bot else "IRIS Hub Assistant"
        domain_name = bot.domain.name if bot and bot.domain else "General"

        # 4. Filter Tools
        state_str = state_code.value if hasattr(state_code, 'value') else str(state_code)
        self.logger.info("Agent orchestration started", extra={"session_id": session_id, "bot": bot_name, "state": state_str})

        state_allowed_tools = StateMachine.get_allowed_tools(state_str)
        bot_capabilities = list(bot.capabilities) if bot and bot.capabilities else []
        if "core" not in bot_capabilities:
            bot_capabilities.append("core")
        # Bot chỉ có "core" → mặc định thêm catalog tools để bot bán hàng cơ bản hoạt động
        if bot_capabilities == ["core"]:
            bot_capabilities.extend(["offering_search", "offering_details", "offering_comparison"])

        all_possible_tools = agent_tools.get_tool_metadata(enabled_capabilities=bot_capabilities)
        available_tools = [t for t in all_possible_tools if t["name"] in state_allowed_tools]
        allowed_tool_names = [t["name"] for t in available_tools]
        
        # 5. Extract Intent (Sprint 2 - Enforcement Layer)
        current_state = domain.LifecycleState(state_str)
        intent = await self.intent_handler.extract_intent(
            message=message,
            current_state=current_state,
            context=context_snapshot
        )
        intent_str = intent.value if intent else "UNKNOWN"
        self.logger.debug("Intent extracted", extra={"intent": intent_str})

        # 6. Build System Prompt
        # Inject Context Slots and Intent
        context_str = "\n".join([f"- {k}: {v}" for k, v in context_snapshot.items()]) if context_snapshot else "Chưa có thông tin."
        
        system_prompt = (
            f"Bạn là '{bot_name}', chuyên gia trong lĩnh vực '{domain_name}'.\n"
            "Nhiệm vụ: Hỗ trợ người dùng tìm kiếm, so sánh và chọn mua sản phẩm phù hợp nhất.\n\n"
            f"HỒ SƠ KHÁCH HÀNG (CONTEXT SLOTS):\n{context_str}\n\n"
            f"Trạng thái hiện tại: {state_str}\n"
            f"Ý định người dùng (Detected Intent): {intent_str}\n\n"
            f"Lưu ý QUAN TRỌNG:\n"
            "- 'Context Slots' là những gì khách đã chọn. LUÔN sử dụng thông tin này để trả lời mà không cần hỏi lại.\n"
            "- 'State dictate all': Trạng thái quyết định hành động của bạn. AI không tự ý nhảy luồng.\n"
            "- 'Intent-First': Luôn bám sát ý định người dùng đã được xác định.\n"
            "\nQUY TẮC SỬ DỤNG CÔNG CỤ:\n"
            "1. Xác báo ý định (Dùng `submit_intent`): Cho các ý định: GREETING, CONFIRM (chốt mua), CANCEL (hủy), PROVIDE_INFO (cung cấp info).\n"
            "2. Tra cứu sản phẩm: Dùng `search_offerings` khi khách hỏi chung chung.\n"
            "3. Chi tiết sản phẩm: Dùng `get_offering_details`.\n"
            f"\nCông cụ ĐƯỢC PHÉP: {json.dumps(available_tools, ensure_ascii=False)}\n"
        )
        
        # 6. Reasoning Loop
        max_turns = 3
        current_message = message
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        g_ui_data = None 
        final_new_state = None
        
        for i in range(max_turns):
            llm_result = await self.llm_service.generate_response(
                system_prompt, 
                current_message, 
                tools=available_tools if available_tools else None,
                messages_history=history
            )
            
            if llm_result.get("usage"):
                for k in total_usage:
                    total_usage[k] += llm_result["usage"].get(k, 0)

            tool_calls = llm_result.get("tool_calls", [])
            if not tool_calls:
                return {
                    "response": llm_result.get("response") or "Tôi không thể xử lý yêu cầu này.",
                    "usage": total_usage,
                    "g_ui_data": g_ui_data,
                    "new_state": final_new_state
                }
            
            tool_call = tool_calls[0]
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                return {
                    "response": "Lỗi xử lý phản hồi từ AI: Đối số công cụ không hợp lệ.",
                    "usage": total_usage
                }
            
            # Validate Tool Execution with FlowDecisionService
            from app.core.services.flow_decision_service import FlowDecisionService
            
            can_execute, rejection_reason = FlowDecisionService.can_execute_tool(
                intent=intent if intent else domain.Intent.UNKNOWN,
                current_state=current_state,
                tool_name=tool_name
            )
            
            if not can_execute:
                rejection_msg = f"Hành động '{tool_name}' không được phép thực hiện trong trạng thái hiện tại. Lý do: {rejection_reason}."
                self.logger.warning("Tool execution rejected", extra={"tool": tool_name, "reason": rejection_reason})
                return {
                    "response": rejection_msg,
                    "usage": total_usage,
                    "new_state": None
                }
            else:
                # Execute Tool via Executor
                executor_result = await self.tool_executor.execute(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    session=session,
                    allowed_tools=allowed_tool_names,
                    context_data={
                        "message": message,
                        "context_slots": slots,
                        "history": history
                    }
                )
                
                if not executor_result.success:
                    return {
                        "response": executor_result.error or f"Lỗi thực thi tool '{tool_name}'.",
                        "usage": total_usage
                    }
                
                observation = executor_result.data
                if executor_result.ui_data:
                    g_ui_data = executor_result.ui_data
            
            # 6. Flow Decision (Refactored: Business logic resides in FlowDecisionService)
            from app.core.services.flow_decision_service import FlowDecisionService
            
            # Extract intent from tool observation if it was submit_intent
            intent_code = observation.get("intent") if isinstance(observation, dict) and tool_name == "submit_intent" else None
            
            decided_state = FlowDecisionService.decide_next_state(
                current_state=state_code,
                tool_name=tool_name,
                tool_result=observation,
                intent=intent_code
            )
            
            if decided_state:
                # Optional: Double-check with StateMachine (FlowDecisionService already does this in its validate_transition)
                if FlowDecisionService.validate_transition(state_code, decided_state):
                    final_new_state = decided_state
                else:
                    self.logger.warning("Invalid state transition rejected", extra={"from": str(state_code), "to": str(decided_state)})

            self.logger.debug("Tool completed", extra={"tool": tool_name, "new_state": str(final_new_state or "Unchanged")})
            system_prompt += f"\n[Observation from {tool_name}]: {json.dumps(observation, ensure_ascii=False)}"
            current_message = f"Dựa trên kết quả từ {tool_name}, hãy hoàn tất câu trả lời cho người dùng."
                
        return {
            "response": "Xin lỗi, tôi cần quá nhiều bước để xử lý yêu cầu này.", 
            "usage": total_usage,
            "g_ui_data": g_ui_data,
            "new_state": final_new_state
        }

    async def close(self):
        """Cleanup handlers"""
        await self.integration_handler.close()
