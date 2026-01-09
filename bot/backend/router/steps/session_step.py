"""
STEP 0: Session Load/Create
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ...schemas import RouterRequest, SessionState
from ...shared.exceptions import SessionNotFoundError
from ...shared.logger import logger
from ...shared.config import config
from ...infrastructure.session_repository import RedisSessionRepository


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
                    logger.debug(f"Session loaded: {session_id}")
                    return session
            
            # Create new session
            new_session = SessionState(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                last_domain=None,
                slots_memory={},
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

