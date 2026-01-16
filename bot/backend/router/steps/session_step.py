"""
STEP 0: Session Load/Create
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ...schemas import RouterRequest, SessionState
from ...router.conversation_state_machine import ConversationState
from ...shared.exceptions import SessionNotFoundError
from ...shared.logger import logger
from ...shared.config import config
from ...infrastructure.session_repository import RedisSessionRepository
from datetime import datetime, timedelta


class SessionStep:
    """Session management step"""
    
    def __init__(self):
        """Initialize session step with repository"""
        self.session_repository = RedisSessionRepository()
    
    async def execute(self, user_id: str, session_id: Optional[str] = None) -> SessionState:
        """
        Execute session step - load or create session
        
        Args:
            user_id: User identifier
            session_id: Optional existing session ID
            
        Returns:
            SessionState object
        """
        try:
            if session_id:
                # Try to load existing session
                session = await self.session_repository.get(session_id)
                if session:
                    # Check conversation timeout (F4.2)
                    session = await self._check_conversation_timeout(session)
                    logger.debug(f"Session loaded: {session_id}")
                    return session
            
            # Create new session
            new_session = SessionState(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                last_domain=None,
                slots_memory={},
                conversation_state=ConversationState.IDLE,
            )
            
            await self.session_repository.save(new_session)
            
            logger.debug(f"Session created: {new_session.session_id}")
            
            return new_session
            
        except Exception as e:
            logger.error(f"Session step error: {e}")
            # Create in-memory session on error (Redis might not be connected in tests)
            return SessionState(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                last_domain=None,
                slots_memory={},
                conversation_state=ConversationState.IDLE,
            )
    
    async def _load_session(self, session_id: str, user_id: str) -> Optional[SessionState]:
        """
        Load session from repository.
        
        Args:
            session_id: Session ID
            user_id: User ID for validation
            
        Returns:
            SessionState if found, None otherwise
        """
        try:
            session = await self.session_repository.get(session_id)
            return session
        except Exception as e:
            logger.warning(
                f"Failed to load session: {e}",
                extra={"session_id": session_id, "user_id": user_id}
            )
            return None
    
    def _create_session(self, user_id: str) -> SessionState:
        """
        Create new session.
        
        Args:
            user_id: User ID
            
        Returns:
            New SessionState
        """
        return SessionState(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
        )
    
    async def _check_conversation_timeout(self, session: SessionState) -> SessionState:
        """
        Check if conversation has timed out and clear pending state (F4.2).
        
        Args:
            session: Session state to check
            
        Returns:
            Updated session state
        """
        timeout_minutes = config.CONVERSATION_TIMEOUT_MINUTES
        timeout_delta = timedelta(minutes=timeout_minutes)
        
        # Check if session has pending intent and is timed out
        if session.pending_intent and session.updated_at:
            # Handle both datetime and string formats
            updated_at = session.updated_at
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    logger.warning(
                        f"Invalid updated_at format in session: {updated_at}",
                        extra={"session_id": session.session_id}
                    )
                    return session
            
            time_since_update = datetime.utcnow() - updated_at
            
            if isinstance(time_since_update, timedelta) and time_since_update > timeout_delta:
                logger.info(
                    "Conversation timeout detected, clearing pending state",
                    extra={
                        "session_id": session.session_id,
                        "pending_intent": session.pending_intent,
                        "time_since_update_minutes": time_since_update.total_seconds() / 60,
                        "timeout_minutes": timeout_minutes,
                    }
                )
                
                # Clear pending state
                session.pending_intent = None
                session.active_domain = None
                session.missing_slots = []
                session.conversation_state = ConversationState.IDLE
                
                # Update timestamp
                session.update_timestamp()
                
                # Save updated session
                try:
                    await self.session_repository.save(session)
                    logger.debug(
                        "Session updated after conversation timeout",
                        extra={"session_id": session.session_id}
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to save session after timeout clear: {e}",
                        extra={"session_id": session.session_id},
                        exc_info=True
                    )
        
        return session

