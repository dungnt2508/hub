"""
Test Normalize Step
"""
import pytest
from backend.router.steps.normalize_step import NormalizeStep
from backend.types import SessionState
from backend.shared.exceptions import InvalidInputError


@pytest.fixture
def normalize_step():
    """Create normalize step instance"""
    return NormalizeStep()


@pytest.fixture
def session_state():
    """Create session state"""
    return SessionState(
        session_id="test_session",
        user_id="test_user",
    )


@pytest.mark.asyncio
async def test_normalize_input_empty_string(normalize_step, session_state):
    """Test normalize with empty string"""
    with pytest.raises(InvalidInputError):
        await normalize_step.execute("", session_state)


@pytest.mark.asyncio
async def test_normalize_input_unicode(normalize_step, session_state):
    """Test normalize with unicode characters"""
    result = await normalize_step.execute("Xin chào 👋", session_state)
    assert result.normalized_message == "xin chào"
    assert result.noise_level in ["LOW", "MEDIUM", "HIGH"]


@pytest.mark.asyncio
async def test_normalize_input_whitespace(normalize_step, session_state):
    """Test normalize with whitespace"""
    result = await normalize_step.execute("  xin chào  ", session_state)
    assert result.normalized_message == "xin chào"


@pytest.mark.asyncio
async def test_normalize_input_abbreviations(normalize_step, session_state):
    """Test normalize with abbreviations"""
    result = await normalize_step.execute("ko dc", session_state)
    assert "không" in result.normalized_message
    assert "được" in result.normalized_message


@pytest.mark.asyncio
async def test_normalize_input_dates(normalize_step, session_state):
    """Test normalize with date references"""
    result = await normalize_step.execute("mai tôi nghỉ", session_state)
    assert len(result.normalized_entities.get("dates", [])) > 0

