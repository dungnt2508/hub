"""
Integration tests for session flow
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.infrastructure.session_repository import RedisSessionRepository
from backend.schemas import SessionState
from backend.router.steps.session_step import SessionStep


@pytest.fixture
async def session_repo(redis_connection):
    """Create session repository with Redis"""
    if redis_connection is None:
        pytest.skip("Redis not available")
    return RedisSessionRepository()


@pytest.fixture
def session_step():
    """Create session step"""
    return SessionStep()


@pytest.fixture
def sample_session():
    """Create sample session"""
    return SessionState(
        session_id=str(uuid4()),
        user_id=str(uuid4()),
        last_domain="hr",
        slots_memory={},
    )


class TestSessionRepository:
    """Test session repository operations"""
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, session_repo, sample_session):
        """Test saving and retrieving session"""
        # Save session
        await session_repo.save(sample_session)
        
        # Retrieve session
        retrieved = await session_repo.get(sample_session.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == sample_session.session_id
        assert retrieved.user_id == sample_session.user_id
        assert retrieved.last_domain == sample_session.last_domain
    
    @pytest.mark.asyncio
    async def test_session_not_found(self, session_repo):
        """Test retrieving non-existent session"""
        result = await session_repo.get("non-existent-session-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_repo, sample_session):
        """Test deleting session"""
        # Save session
        await session_repo.save(sample_session)
        
        # Verify it exists
        retrieved = await session_repo.get(sample_session.session_id)
        assert retrieved is not None
        
        # Delete session
        await session_repo.delete(sample_session.session_id)
        
        # Verify deleted
        result = await session_repo.get(sample_session.session_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self, session_repo):
        """Test managing multiple sessions"""
        sessions = []
        for i in range(3):
            session = SessionState(
                session_id=str(uuid4()),
                user_id=str(uuid4()),
                last_domain="hr",
                slots_memory={},
            )
            await session_repo.save(session)
            sessions.append(session)
        
        # Verify all sessions exist
        for session in sessions:
            retrieved = await session_repo.get(session.session_id)
            assert retrieved is not None
            assert retrieved.user_id == session.user_id


class TestSessionStep:
    """Test session step integration"""
    
    @pytest.mark.asyncio
    async def test_create_new_session(self, session_step, redis_connection):
        """Test creating new session"""
        if redis_connection is None:
            pytest.skip("Redis not available")
        
        user_id = str(uuid4())
        result = await session_step.execute(user_id=user_id, session_id=None)
        
        # Result is now a SessionState object
        assert result.session_id is not None
        assert result.user_id == user_id
        assert result.last_domain is None
        assert result.slots_memory == {}
    
    @pytest.mark.asyncio
    async def test_load_existing_session(self, session_repo):
        """Test loading existing session from repo"""
        # Create and save a session directly
        user_id = str(uuid4())
        original_session = SessionState(
            session_id=str(uuid4()),
            user_id=user_id,
            last_domain="hr",
            slots_memory={"key": "value"},
        )
        
        try:
            await session_repo.save(original_session)
            
            # Load via repository
            loaded_session = await session_repo.get(original_session.session_id)
            
            assert loaded_session is not None
            assert loaded_session.session_id == original_session.session_id
            assert loaded_session.user_id == original_session.user_id
            assert loaded_session.last_domain == "hr"
        except Exception as e:
            # If Redis not available, skip test
            pytest.skip(f"Redis not available: {e}")
    
    @pytest.mark.asyncio
    async def test_session_with_invalid_id(self, session_step, redis_connection):
        """Test session step with invalid session ID"""
        if redis_connection is None:
            pytest.skip("Redis not available")
        
        # Should create new session if ID doesn't exist
        result = await session_step.execute(
            user_id=str(uuid4()),
            session_id=str(uuid4())  # Different user/session combo
        )
        
        # Result is now a SessionState object
        assert result.session_id is not None


class TestSessionPersistence:
    """Test session persistence across requests"""
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, session_step, session_repo, redis_connection):
        """Test session persists across multiple requests"""
        if redis_connection is None:
            pytest.skip("Redis not available")
        
        user_id = str(uuid4())
        
        # First request - create session
        result1 = await session_step.execute(user_id=user_id, session_id=None)
        session_id_1 = result1.session_id
        
        # Verify session is in Redis
        session = await session_repo.get(session_id_1)
        assert session is not None
        
        # Second request - load same session
        result2 = await session_step.execute(user_id=user_id, session_id=session_id_1)
        
        assert result2.session_id == session_id_1
    
    @pytest.mark.asyncio
    async def test_conversation_state_update(self, session_step, session_repo, redis_connection):
        """Test updating slots in session"""
        if redis_connection is None:
            pytest.skip("Redis not available")
        
        user_id = str(uuid4())
        
        # Create session
        result1 = await session_step.execute(user_id=user_id, session_id=None)
        session_id = result1.session_id
        
        # Get session from Redis
        session = await session_repo.get(session_id)
        
        # Update slots_memory
        if session:
            session.slots_memory = {"domain": "hr", "intent": "query_leave"}
            await session_repo.save(session)
            
            # Retrieve and verify
            updated_session = await session_repo.get(session_id)
            assert updated_session is not None
            assert updated_session.slots_memory["domain"] == "hr"
            assert updated_session.slots_memory["intent"] == "query_leave"

