"""
Session Repository - Redis-based session storage
"""
import json
from typing import Optional
from datetime import datetime

from ..schemas import SessionState
from ..shared.exceptions import SessionNotFoundError, SessionCorruptedError, ExternalServiceError
from ..shared.logger import logger
from ..shared.config import config
from .redis_client import redis_client


class SessionRepository:
    """Redis-based session repository"""
    
    def __init__(self):
        self.redis = redis_client
        self.key_prefix = "session:"
        self.ttl = config.SESSION_TTL_SECONDS
    
    def _make_key(self, session_id: str) -> str:
        """Create Redis key for session"""
        return f"{self.key_prefix}{session_id}"
    
    async def get(self, session_id: str, user_id: str) -> Optional[SessionState]:
        """
        Load session from Redis.
        
        Args:
            session_id: Session ID
            user_id: User ID for validation
            
        Returns:
            SessionState if found, None otherwise
            
        Raises:
            SessionCorruptedError: If session data is corrupted
            ExternalServiceError: If Redis fails
        """
        try:
            key = self._make_key(session_id)
            data = await self.redis.client.get(key)
            
            if not data:
                return None
            
            # Parse session data
            try:
                session_dict = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse session data: {e}",
                    extra={"session_id": session_id}
                )
                raise SessionCorruptedError(f"Session data corrupted: {e}") from e
            
            # Validate user_id matches
            if session_dict.get("user_id") != user_id:
                logger.warning(
                    "Session user_id mismatch",
                    extra={
                        "session_id": session_id,
                        "expected_user_id": user_id,
                        "found_user_id": session_dict.get("user_id"),
                    }
                )
                return None
            
            # Convert datetime strings back to datetime objects
            if "created_at" in session_dict and isinstance(session_dict["created_at"], str):
                session_dict["created_at"] = datetime.fromisoformat(session_dict["created_at"])
            if "updated_at" in session_dict and isinstance(session_dict["updated_at"], str):
                session_dict["updated_at"] = datetime.fromisoformat(session_dict["updated_at"])
            
            # Convert to SessionState
            session = SessionState(**session_dict)
            logger.debug(
                "Session loaded",
                extra={"session_id": session_id, "user_id": user_id}
            )
            return session
            
        except (SessionCorruptedError, ExternalServiceError):
            raise
        except Exception as e:
            logger.error(
                f"Failed to load session: {e}",
                extra={"session_id": session_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Session load failed: {e}") from e
    
    async def save(self, session: SessionState) -> None:
        """
        Save session to Redis.
        
        Args:
            session: SessionState to save
            
        Raises:
            ExternalServiceError: If Redis fails
        """
        try:
            key = self._make_key(session.session_id)
            
            # Update timestamp
            session.update_timestamp()
            
            # Convert to dict
            session_dict = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "active_domain": session.active_domain,
                "last_domain": session.last_domain,
                "last_intent": session.last_intent,
                "last_intent_type": session.last_intent_type,
                "pending_intent": session.pending_intent,
                "missing_slots": session.missing_slots,
                "slots_memory": session.slots_memory,
                "retry_count": session.retry_count,
                "escalation_flag": session.escalation_flag,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }
            
            # Serialize and save
            data = json.dumps(session_dict, ensure_ascii=False)
            await self.redis.client.setex(key, self.ttl, data)
            
            logger.debug(
                "Session saved",
                extra={
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "ttl": self.ttl,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to save session: {e}",
                extra={"session_id": session.session_id},
                exc_info=True
            )
            raise ExternalServiceError(f"Session save failed: {e}") from e
    
    async def delete(self, session_id: str) -> None:
        """
        Delete session from Redis.
        
        Args:
            session_id: Session ID to delete
        """
        try:
            key = self._make_key(session_id)
            await self.redis.client.delete(key)
            logger.debug("Session deleted", extra={"session_id": session_id})
        except Exception as e:
            logger.warning(
                f"Failed to delete session: {e}",
                extra={"session_id": session_id}
            )
    
    async def extend_ttl(self, session_id: str) -> None:
        """
        Extend session TTL.
        
        Args:
            session_id: Session ID
        """
        try:
            key = self._make_key(session_id)
            await self.redis.client.expire(key, self.ttl)
        except Exception as e:
            logger.warning(
                f"Failed to extend session TTL: {e}",
                extra={"session_id": session_id}
            )

