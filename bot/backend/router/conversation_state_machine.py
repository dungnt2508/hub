"""
Conversation State Machine - Manages conversation flow states

This implements F3.2: Conversation State Machine for better flow control.
"""
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from ..shared.logger import logger


class ConversationState(str, Enum):
    """Conversation states"""
    IDLE = "idle"  # No active conversation
    ROUTING = "routing"  # Router is processing request
    PROCESSING = "processing"  # Domain is processing request
    NEED_INFO = "need_info"  # Waiting for user to provide missing slots
    COMPLETE = "complete"  # Intent completed successfully
    ERROR = "error"  # Error occurred


@dataclass
class StateTransition:
    """State transition definition"""
    from_state: ConversationState
    to_state: ConversationState
    guard: Optional[Callable[[Dict[str, Any]], bool]] = None  # Optional guard function
    action: Optional[Callable[[Dict[str, Any]], None]] = None  # Optional action function


class ConversationStateMachine:
    """
    Conversation state machine with transitions and guards.
    
    States:
    - IDLE: No active conversation
    - ROUTING: Router is processing
    - PROCESSING: Domain is processing
    - NEED_INFO: Waiting for user input
    - COMPLETE: Intent completed
    - ERROR: Error occurred
    """
    
    def __init__(self):
        """Initialize state machine with valid transitions"""
        self.transitions: List[StateTransition] = [
            # From IDLE
            StateTransition(ConversationState.IDLE, ConversationState.ROUTING),
            
            # From ROUTING
            StateTransition(ConversationState.ROUTING, ConversationState.PROCESSING),
            StateTransition(ConversationState.ROUTING, ConversationState.ERROR),
            StateTransition(ConversationState.ROUTING, ConversationState.IDLE),  # META_HANDLED or UNKNOWN
            
            # From PROCESSING
            StateTransition(ConversationState.PROCESSING, ConversationState.NEED_INFO),
            StateTransition(ConversationState.PROCESSING, ConversationState.COMPLETE),
            StateTransition(ConversationState.PROCESSING, ConversationState.ERROR),
            
            # From NEED_INFO
            StateTransition(ConversationState.NEED_INFO, ConversationState.ROUTING),  # User provides info
            StateTransition(ConversationState.NEED_INFO, ConversationState.IDLE),  # User cancels
            
            # From COMPLETE
            StateTransition(ConversationState.COMPLETE, ConversationState.IDLE),
            StateTransition(ConversationState.COMPLETE, ConversationState.ROUTING),  # New request
            
            # From ERROR
            StateTransition(ConversationState.ERROR, ConversationState.IDLE),
            StateTransition(ConversationState.ERROR, ConversationState.ROUTING),  # Retry
        ]
    
    def can_transition(
        self,
        from_state: ConversationState,
        to_state: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if transition is allowed.
        
        Args:
            from_state: Current state
            to_state: Target state
            context: Optional context for guard evaluation
            
        Returns:
            True if transition is allowed
        """
        # Find transition
        transition = next(
            (t for t in self.transitions if t.from_state == from_state and t.to_state == to_state),
            None
        )
        
        if not transition:
            return False
        
        # Check guard if present
        if transition.guard and context:
            try:
                return transition.guard(context)
            except Exception as e:
                logger.error(
                    f"Guard evaluation failed: {e}",
                    extra={"from_state": from_state.value, "to_state": to_state.value},
                    exc_info=True
                )
                return False
        
        return True
    
    def get_allowed_transitions(
        self,
        from_state: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ConversationState]:
        """
        Get all allowed transitions from a state.
        
        Args:
            from_state: Current state
            context: Optional context for guard evaluation
            
        Returns:
            List of allowed target states
        """
        allowed = []
        for transition in self.transitions:
            if transition.from_state == from_state:
                if not transition.guard or (context and transition.guard(context)):
                    allowed.append(transition.to_state)
        return allowed
    
    def transition(
        self,
        from_state: ConversationState,
        to_state: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """
        Perform state transition.
        
        Args:
            from_state: Current state
            to_state: Target state
            context: Optional context for guard/action
            
        Returns:
            New state (or from_state if transition not allowed)
            
        Raises:
            ValueError: If transition is not allowed
        """
        if not self.can_transition(from_state, to_state, context):
            raise ValueError(
                f"Invalid transition from {from_state.value} to {to_state.value}"
            )
        
        # Find transition and execute action if present
        transition = next(
            (t for t in self.transitions if t.from_state == from_state and t.to_state == to_state),
            None
        )
        
        if transition and transition.action and context:
            try:
                transition.action(context)
            except Exception as e:
                logger.error(
                    f"Transition action failed: {e}",
                    extra={"from_state": from_state.value, "to_state": to_state.value},
                    exc_info=True
                )
        
        logger.debug(
            f"State transition: {from_state.value} → {to_state.value}",
            extra={"from_state": from_state.value, "to_state": to_state.value}
        )
        
        return to_state


# Global state machine instance
conversation_state_machine = ConversationStateMachine()
