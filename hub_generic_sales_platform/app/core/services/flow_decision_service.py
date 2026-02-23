from typing import Optional, Dict, Any, Tuple
from app.core.domain.runtime import LifecycleState, Intent
from app.core.domain.state_machine import StateMachine
import logging

logger = logging.getLogger(__name__)

class FlowDecisionService:
    """
    Domain Service chịu trách nhiệm quyết định state transitions
    dựa trên business rules và tool execution results.
    
    NGUYÊN TẮC:
    - State transitions là BUSINESS LOGIC, không phải infrastructure concern
    - Tool handlers CHỈ trả về data, KHÔNG đề xuất state
    - Service này là single source of truth cho transition logic
    - Intent PHẢI được validate với State trước khi cho phép Tool execution
    """
    
    # Intent → Allowed States Mapping (State-First Enforcement)
    INTENT_STATE_MAP = {
        Intent.GREETING: {
            LifecycleState.IDLE,
        },
        Intent.SEARCH_PRODUCT: {
            LifecycleState.IDLE,
            LifecycleState.BROWSING,
            LifecycleState.VIEWING,
            LifecycleState.COMPARING,
            LifecycleState.FILTERING,
        },
        Intent.INQUIRY_PRICE: {
            LifecycleState.IDLE,
            LifecycleState.BROWSING,
            LifecycleState.SEARCHING,
            LifecycleState.FILTERING,
            LifecycleState.VIEWING,
            LifecycleState.COMPARING,
        },
        Intent.CHECK_AVAILABILITY: {
            LifecycleState.VIEWING,
            LifecycleState.COMPARING,
        },
        Intent.PROVIDE_INFO: {
            LifecycleState.BROWSING,
            LifecycleState.SEARCHING,
            LifecycleState.VIEWING,
            LifecycleState.COMPARING,
            LifecycleState.ANALYZING,
            LifecycleState.PURCHASING,
        },
        Intent.CONFIRM: {
            LifecycleState.COMPARING,
            LifecycleState.PURCHASING,
        },
        Intent.CANCEL: {
            LifecycleState.BROWSING,
            LifecycleState.SEARCHING,
            LifecycleState.FILTERING,
            LifecycleState.VIEWING,
            LifecycleState.COMPARING,
            LifecycleState.ANALYZING,
            LifecycleState.PURCHASING,
            LifecycleState.WAITING_INPUT,
        },
    }
    
    @staticmethod
    def can_execute_tool(
        intent: Intent,
        current_state: LifecycleState,
        tool_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if a tool can execute given intent and current state.
        
        This is the CORE enforcement point for State-First architecture.
        
        Args:
            intent: User's detected intent
            current_state: Current lifecycle state of the session
            tool_name: Name of tool LLM wants to execute
        
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        # Normalize current_state (DB may return str)
        state_val = current_state.value if hasattr(current_state, "value") else str(current_state)
        state_val = (state_val or "idle").lower()
        state_enum = LifecycleState(state_val) if state_val in [s.value for s in LifecycleState] else LifecycleState.IDLE

        # Step 1: Tool must be allowed in current state (primary gate)
        allowed_tools = StateMachine.get_allowed_tools(state_val)
        if tool_name not in allowed_tools:
            return False, f"Tool '{tool_name}' không được phép ở trạng thái '{state_val}'"

        # Step 2: Intent validation. Catalog tools (search/get details) chỉ cần state machine — bỏ qua intent
        CATALOG_TOOLS = {"search_offerings", "get_offering_details"}
        if tool_name in CATALOG_TOOLS:
            return True, None

        allowed_states = FlowDecisionService.INTENT_STATE_MAP.get(intent)
        if allowed_states and state_enum not in allowed_states:
            return False, f"Intent '{intent.value}' không được phép ở trạng thái '{state_val}'"
        
        return True, None
    
    @staticmethod
    def decide_next_state(
        current_state: LifecycleState,
        tool_name: str,
        tool_result: Any,
        intent: Optional[str] = None
    ) -> Optional[LifecycleState]:
        """
        Quyết định state tiếp theo dựa trên kết quả tool và Intent.
        """
        # Nếu có intent rõ ràng, ưu tiên xử lý intent trước
        if intent:
            next_state = FlowDecisionService.decide_next_state_by_intent(current_state, intent)
            if next_state:
                return next_state

        # Chuẩn hóa success/data từ tool_result
        if isinstance(tool_result, dict):
            success = tool_result.get("success", False)
            data = tool_result
        else:
            success = True
            data = {}
        
        # Business Rules cho search_offerings
        if tool_name == "search_offerings":
            offerings = data.get("offerings", [])
            if success and len(offerings) > 0:
                return LifecycleState.SEARCHING
            elif success and len(offerings) == 0:
                return LifecycleState.BROWSING
            else:
                return None
        
        # Business Rules cho get_offering_details
        if tool_name == "get_offering_details":
            if success:
                return LifecycleState.VIEWING
            else:
                return None
        
        # Business Rules cho compare_offerings
        if tool_name == "compare_offerings":
            if success:
                return LifecycleState.COMPARING
            else:
                return None

        # Business Rules cho financial tools
        if tool_name in ["get_market_data", "get_strategic_analysis", "credit_scoring"]:
            if success:
                return LifecycleState.ANALYZING
            else:
                return None

        # Business Rules cho auto tools
        if tool_name == "trade_in_valuation":
            if success:
                return LifecycleState.ANALYZING
            else:
                return None
        
        # Business Rules cho education tools
        if tool_name == "assessment_test":
            if success:
                return LifecycleState.IDLE
            else:
                return None
        
        return None

    @staticmethod
    def decide_next_state_by_intent(
        current_state: LifecycleState,
        intent_code: str
    ) -> Optional[LifecycleState]:
        """
        Quyết định state dựa trên Intent người dùng đề xuất.
        """
        from app.core.domain.runtime import Intent
        
        intent_str = intent_code.upper() if intent_code else ""
        
        # Mapping Intent -> State transitions (Business Logic)
        if intent_str == Intent.SEARCH_PRODUCT:
            return LifecycleState.SEARCHING
        
        if intent_str == Intent.CANCEL:
            return LifecycleState.IDLE
            
        if intent_str == Intent.CONFIRM:
            if current_state == LifecycleState.VIEWING:
                return LifecycleState.PURCHASING
            if current_state == LifecycleState.COMPARING:
                return LifecycleState.PURCHASING
        
        if intent_str == Intent.INQUIRY_PRICE:
            if current_state in [LifecycleState.IDLE, LifecycleState.BROWSING, LifecycleState.SEARCHING]:
                return LifecycleState.VIEWING # Chuyển sang xem sản phẩm cụ thể nếu hỏi giá
                
        return None
    
    @staticmethod
    def validate_transition(
        current_state: LifecycleState,
        next_state: LifecycleState
    ) -> bool:
        """Wrapper cho StateMachine validation"""
        current_str = current_state.value if hasattr(current_state, 'value') else str(current_state)
        next_str = next_state.value if hasattr(next_state, 'value') else str(next_state)
        
        # Handle cases where current_state might be None or Empty in DB
        if not current_str or current_str == "None":
            return True # Allow initial state set
            
        return StateMachine.is_transition_valid(current_str, next_str)
