"""
Unit tests for FlowDecisionService - State-First Enforcement Layer
"""

import pytest
from app.core.domain.runtime import Intent, LifecycleState
from app.core.services.flow_decision_service import FlowDecisionService


class TestIntentStateValidation:
    """Test Intent → State validation"""
    
    def test_invalid_confirm_from_idle(self):
        """User cannot CONFIRM from IDLE state"""
        can_execute, reason = FlowDecisionService.can_execute_tool(
            intent=Intent.CONFIRM,
            current_state=LifecycleState.IDLE,
            tool_name="trigger_web_hook"
        )
        assert not can_execute
        assert "không được phép" in reason
    
    def test_valid_confirm_from_comparing(self):
        """User CAN confirm from COMPARING state"""
        can_execute, reason = FlowDecisionService.can_execute_tool(
            intent=Intent.CONFIRM,
            current_state=LifecycleState.COMPARING,
            tool_name="trigger_web_hook"
        )
        assert can_execute
        assert reason is None
    
    def test_search_allowed_from_multiple_states(self):
        """SEARCH_PRODUCT intent allowed from multiple states"""
        for state in [LifecycleState.IDLE, LifecycleState.BROWSING, LifecycleState.VIEWING]:
            can_execute, _ = FlowDecisionService.can_execute_tool(
                intent=Intent.SEARCH_PRODUCT,
                current_state=state,
                tool_name="search_offerings"
            )
            assert can_execute, f"Search should be allowed from {state}"
    
    def test_tool_not_allowed_in_state(self):
        """Tool validation works even if intent is valid"""
        # INQUIRY_PRICE intent is valid for VIEWING
        # But if tool is not in StateMachine for that state, should fail
        can_execute, reason = FlowDecisionService.can_execute_tool(
            intent=Intent.INQUIRY_PRICE,
            current_state=LifecycleState.VIEWING,
            tool_name="trigger_web_hook"  # Not allowed in VIEWING
        )
        # Should fail because trigger_web_hook not in VIEWING's allowed tools
        assert not can_execute


class TestStateTransitionDecisions:
    """Test state transition logic"""
    
    def test_search_success_transitions_to_searching(self):
        """Successful search transitions to SEARCHING"""
        tool_result = {"success": True, "offerings": [{"id": "1"}]}
        next_state = FlowDecisionService.decide_next_state(
            current_state=LifecycleState.IDLE,
            tool_name="search_offerings",
            tool_result=tool_result
        )
        assert next_state == LifecycleState.SEARCHING
    
    def test_view_details_transitions_to_viewing(self):
        """get_offering_details transitions to VIEWING"""
        tool_result = {"success": True, "offering": {"id": "1"}}
        next_state = FlowDecisionService.decide_next_state(
            current_state=LifecycleState.SEARCHING,
            tool_name="get_offering_details",
            tool_result=tool_result
        )
        assert next_state == LifecycleState.VIEWING
    
    def test_failed_tool_stays_in_current_state(self):
        """Failed tool execution should not change state"""
        tool_result = {"success": False, "error": "Not found"}
        next_state = FlowDecisionService.decide_next_state(
            current_state=LifecycleState.IDLE,
            tool_name="search_offerings",
            tool_result=tool_result
        )
        # Should return None (no transition)
        assert next_state is None


class TestIntentDrivenTransitions:
    """Test intent-driven state transitions"""
    
    def test_cancel_intent_resets_to_idle(self):
        """CANCEL intent from any state should suggest IDLE"""
        next_state = FlowDecisionService.decide_next_state_by_intent(
            current_state=LifecycleState.COMPARING,
            intent_code="CANCEL"
        )
        assert next_state == LifecycleState.IDLE
    
    def test_confirm_from_viewing_suggests_purchasing(self):
        """CONFIRM from VIEWING suggests PURCHASING"""
        next_state = FlowDecisionService.decide_next_state_by_intent(
            current_state=LifecycleState.VIEWING,
            intent_code="CONFIRM"
        )
        assert next_state == LifecycleState.PURCHASING


class TestTransitionValidation:
    """Test transition validation wrapper"""
    
    def test_valid_transition(self):
        """Validate legal state transition"""
        is_valid = FlowDecisionService.validate_transition(
            current_state=LifecycleState.VIEWING,
            next_state=LifecycleState.COMPARING
        )
        assert is_valid
    
    def test_invalid_transition(self):
        """Block illegal state transition"""
        is_valid = FlowDecisionService.validate_transition(
            current_state=LifecycleState.IDLE,
            next_state=LifecycleState.PURCHASING
        )
        assert not is_valid
