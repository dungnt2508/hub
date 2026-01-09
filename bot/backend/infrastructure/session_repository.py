"""
Session Repository - Stores and retrieves session state
"""
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta
import json
import logging
from dataclasses import asdict

from ..schemas import SessionState
from .redis_client import redis_client
from ..shared.config import config

logger = logging.getLogger(__name__)


class ISessionRepository(ABC):
    """Interface for session storage"""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        pass
    
    @abstractmethod
    async def save(self, session: SessionState) -> None:
        """Save or update session"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session"""
        pass
    
    @abstractmethod
    async def clear_expired(self) -> int:
        """Clear expired sessions, return count"""
        pass


class RedisSessionRepository(ISessionRepository):
    """Redis-based session repository"""
    
    def __init__(self):
        """Initialize Redis session repository"""
        self.prefix = "session:"
        self.ttl_seconds = config.SESSION_TTL_SECONDS
    
    async def get(self, session_id: str) -> Optional[SessionState]:
        """
        Get session from Redis
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState or None if not found
        """
        try:
            key = f"{self.prefix}{session_id}"
            data = await redis_client.client.get(key)
            
            if not data:
                logger.debug(f"Session not found: {session_id}")
                return None
            
            # Deserialize session (handle both bytes and string)
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            session_dict = json.loads(data)
            
            # Convert dict to SessionState dataclass
            session = SessionState(**session_dict)
            
            logger.debug(f"Session retrieved: {session_id}")
            return session
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    async def save(self, session: SessionState) -> None:
        """
        Save session to Redis with TTL
        
        Args:
            session: SessionState to save
        """
        try:
            key = f"{self.prefix}{session.session_id}"
            
            # Serialize dataclass to JSON
            session_dict = asdict(session)
            data = json.dumps(session_dict, default=str)  # default=str for datetime serialization
            
            # Save with TTL
            await redis_client.client.setex(
                key,
                self.ttl_seconds,
                data
            )
            
            logger.debug(f"Session saved: {session.session_id} (TTL: {self.ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            raise
    
    async def delete(self, session_id: str) -> None:
        """
        Delete session from Redis
        
        Args:
            session_id: Session identifier
        """
        try:
            key = f"{self.prefix}{session_id}"
            await redis_client.client.delete(key)
            logger.debug(f"Session deleted: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
    
    async def clear_expired(self) -> int:
        """
        Clear expired sessions (Redis handles auto-expiry)
        In Redis, keys expire automatically, but we can log stats.
        
        Returns:
            Number of sessions cleared (0 if handled by Redis)
        """
        # Note: Redis automatically expires keys, so this is mostly for logging
        logger.info("Redis auto-expires sessions via TTL")
        return 0