"""
Test Pattern Match Step
"""
import pytest
from backend.router.steps.pattern_step import PatternMatchStep


@pytest.fixture
def pattern_step():
    """Create pattern step instance"""
    return PatternMatchStep()


@pytest.mark.asyncio
async def test_pattern_match_leave_balance(pattern_step):
    """Test pattern match for leave balance query"""
    result = await pattern_step.execute("còn bao nhiêu ngày phép")
    assert result["matched"] is True
    assert result["domain"] == "hr"
    assert result["intent"] == "query_leave_balance"
    assert result["confidence"] == 1.0
    assert result["source"] == "PATTERN"


@pytest.mark.asyncio
async def test_pattern_match_create_leave(pattern_step):
    """Test pattern match for create leave request"""
    result = await pattern_step.execute("xin nghỉ phép")
    assert result["matched"] is True
    assert result["domain"] == "hr"
    assert result["intent"] == "create_leave_request"


@pytest.mark.asyncio
async def test_pattern_match_no_match(pattern_step):
    """Test pattern match with no match"""
    result = await pattern_step.execute("hôm nay trời đẹp")
    assert result["matched"] is False

