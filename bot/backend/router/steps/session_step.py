"""
STEP 0: Session Load/Create
"""
import uuid
from datetime import datetime

from ...schemas import RouterRequest, SessionState
from ...shared.exceptions import SessionNotFoundError
from ...shared.logger import logger
from ...shared.config import config
from ...infrastructure.session_repository import SessionRepository


class SessionStep:
    """Session management step"""
    
    def __init__(self, session_repo: SessionRepository = None):
        """Initialize session step with repository"""
        self.session_repo = session_repo or SessionRepository()
    
    async def execute(self, request: RouterRequest) -> SessionState:
        """
        Load existing session or create new one.
        
        Args:
            request: Router request with user_id and optional session_id
            
        Returns:
            SessionState object
        """
        if request.session_id:
            # Try to load existing session
            session = await self._load_session(request.session_id, request.user_id)
            if session:
                # Extend TTL
                await self.session_repo.extend_ttl(session.session_id)
                logger.info(
                    "Session loaded",
                    extra={
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                    }
                )
                return session
        
        # Create new session
        session = self._create_session(request.user_id)
        await self.session_repo.save(session)
        logger.info(
            "New session created",
            extra={
                "session_id": session.session_id,
                "user_id": session.user_id,
            }
        )
        return session
    
    async def _load_session(self, session_id: str, user_id: str) -> SessionState | None:
        """
        Load session from repository.
        
        Args:
            session_id: Session ID
            user_id: User ID for validation
            
        Returns:
            SessionState if found, None otherwise
        """
        try:
            session = await self.session_repo.get(session_id, user_id)
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

