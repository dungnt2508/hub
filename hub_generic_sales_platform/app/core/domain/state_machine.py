"""
State Machine Definition for IRIS Hub (v4)
Triết lý: State defines the scope; Agent executes within the scope.
"""

from typing import List, Dict, Set
from .runtime import LifecycleState

class StateMachine:
    """
    Quản lý các trạng thái và các hành động (skills/tools) được phép.
    """
    
    # Định nghĩa các Tools (Skills) được phép cho mỗi State
    STATE_SKILL_MAP: Dict[LifecycleState, Set[str]] = {
        LifecycleState.IDLE: {
            "search_offerings",
            "compare_offerings",
            "get_offering_details",
            "get_market_data",
            "get_strategic_analysis",
            "trade_in_valuation",
            "credit_scoring",
            "assessment_test"
        },
        LifecycleState.BROWSING: {
            "search_offerings",
            "get_offering_details",
            "get_market_data",
            "trade_in_valuation",
            "credit_scoring",
            "assessment_test"
        },
        LifecycleState.SEARCHING: {
            "search_offerings",
            "get_offering_details",
            "get_market_data",
            "trade_in_valuation",
            "credit_scoring",
            "assessment_test"
        },
        LifecycleState.FILTERING: {
            "search_offerings",
            "get_offering_details",
        },
        LifecycleState.VIEWING: {
            "get_offering_details",
            "compare_offerings",
            "search_offerings",
            "get_market_data",
            "trade_in_valuation",
            "credit_scoring",
            "assessment_test"
        },
        LifecycleState.COMPARING: {
            "compare_offerings",
            "get_offering_details",
            "search_offerings",
            "trigger_web_hook"
        },
        LifecycleState.ANALYZING: {
            "get_market_data",
            "get_strategic_analysis",
            "search_offerings",
            "get_offering_details",
            "trade_in_valuation",
            "credit_scoring",
            "assessment_test"
        },
        LifecycleState.PURCHASING: {
            "trigger_web_hook",
            "search_offerings",
            "get_offering_details"
        },
        LifecycleState.COMPLETED: {
            "search_offerings",  # Can start new session
        },
        LifecycleState.CLOSED: {
            "search_offerings",
            "get_offering_details"
        },
        LifecycleState.ERROR: {
            "search_offerings",
            "get_offering_details"
        },
        LifecycleState.WAITING_INPUT: {
            "search_offerings",
            "get_offering_details"
        }
    }

    # Định nghĩa các Transition hợp lệ (Optional - dùng để validate)
    VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
        LifecycleState.IDLE: {LifecycleState.BROWSING, LifecycleState.SEARCHING, LifecycleState.ANALYZING},
        LifecycleState.BROWSING: {LifecycleState.VIEWING, LifecycleState.SEARCHING, LifecycleState.FILTERING, LifecycleState.IDLE, LifecycleState.ANALYZING},
        LifecycleState.SEARCHING: {LifecycleState.VIEWING, LifecycleState.BROWSING, LifecycleState.FILTERING, LifecycleState.IDLE, LifecycleState.ANALYZING},
        LifecycleState.FILTERING: {LifecycleState.VIEWING, LifecycleState.BROWSING, LifecycleState.SEARCHING},
        LifecycleState.VIEWING: {LifecycleState.COMPARING, LifecycleState.PURCHASING, LifecycleState.BROWSING, LifecycleState.IDLE, LifecycleState.ANALYZING},
        LifecycleState.COMPARING: {LifecycleState.VIEWING, LifecycleState.PURCHASING, LifecycleState.IDLE, LifecycleState.ANALYZING},
        LifecycleState.ANALYZING: {LifecycleState.IDLE, LifecycleState.BROWSING, LifecycleState.VIEWING},
        LifecycleState.PURCHASING: {LifecycleState.COMPLETED, LifecycleState.CLOSED, LifecycleState.ERROR},
        LifecycleState.COMPLETED: {LifecycleState.IDLE},
        LifecycleState.CLOSED: {LifecycleState.IDLE},
        LifecycleState.ERROR: {LifecycleState.IDLE, LifecycleState.BROWSING},
        LifecycleState.WAITING_INPUT: {LifecycleState.IDLE, LifecycleState.BROWSING, LifecycleState.VIEWING, LifecycleState.ANALYZING}
    }

    @classmethod
    def get_allowed_tools(cls, state_code: str) -> List[str]:
        """Lấy danh sách các tool được phép cho một state cụ thể.
        Hỗ trợ cả state_code uppercase (IDLE) và lowercase (idle).
        """
        try:
            code = str(state_code).strip()
            # Thử theo tên enum (IDLE) hoặc theo value (idle)
            try:
                state = LifecycleState[code.upper()]
            except KeyError:
                state = LifecycleState(code.lower())
            return list(cls.STATE_SKILL_MAP.get(state, set()))
        except (ValueError, KeyError):
            return []

    @classmethod
    def is_transition_valid(cls, current_state_code: str, next_state_code: str) -> bool:
        """Kiểm tra xem việc chuyển từ state A sang B có hợp lệ không.
        Hỗ trợ state_code uppercase (IDLE) và lowercase (idle).
        """
        try:
            def _parse(s: str) -> LifecycleState:
                c = str(s).strip()
                try:
                    return LifecycleState[c.upper()]
                except KeyError:
                    return LifecycleState(c.lower())
            current = _parse(current_state_code)
            next_state = _parse(next_state_code)
            return next_state in cls.VALID_TRANSITIONS.get(current, set())
        except (ValueError, KeyError):
            return False
