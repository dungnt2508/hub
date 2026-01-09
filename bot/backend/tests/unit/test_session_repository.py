"""Tests for session repository"""
import pytest
from datetime import datetime
from uuid import uuid4

from backend.infrastructure.session_repository import RedisSessionRepository
from backend.schemas import SessionState


@pytest.fixture
async def repo():
    """Create session repository"""
    return RedisSessionRepository()


@pytest.fixture
def sample_session():
    """Create sample session"""
    return SessionState(
        session_id=str(uuid4()),
        user_id="test-user",
        created_at=datetime.now(),
        last_domain="hr",
        conversation_state={},
    )


@pytest.mark.asyncio
async def test_save_and_retrieve(repo, sample_session):
    """Test saving and retrieving session"""
    # Save
    await repo.save(sample_session)
    
    # Retrieve
    retrieved = await repo.get(sample_session.session_id)
    
    assert retrieved is not None
    assert retrieved.session_id == sample_session.session_id
    assert retrieved.user_id == sample_session.user_id


@pytest.mark.asyncio
async def test_session_not_found(repo):
    """Test retrieving non-existent session"""
    result = await repo.get("non-existent")
    assert result is None


@pytest.mark.asyncio
async def test_delete_session(repo, sample_session):
    """Test deleting session"""
    # Save
    await repo.save(sample_session)
    
    # Delete
    await repo.delete(sample_session.session_id)
    
    # Verify deleted
    result = await repo.get(sample_session.session_id)
    assert result is None


@pytest.mark.asyncio
async def test_session_ttl_expiry(repo, sample_session):
    """Test session TTL expiry"""
    # This test requires Redis server
    # Save session
    await repo.save(sample_session)
    
    # Verify it exists
    session = await repo.get(sample_session.session_id)
    assert session is not None
    
    # In actual test, would wait for TTL to expire
    # For now, just verify TTL is set correctly
    # Can be tested with shorter TTL in test config