import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.application.services.session_state import SessionStateHandler
from app.core.domain.runtime import RuntimeSession, LifecycleState

@pytest.mark.asyncio
async def test_valid_state_transition():
    # Setup
    db = AsyncMock()
    handler = SessionStateHandler(db)
    
    session_id = str(uuid.uuid4())
    tenant_id = "tenant-1"
    
    # Mock existing session in IDLE state
    mock_session = RuntimeSession(
        id=session_id,
        tenant_id=tenant_id,
        bot_id="bot-1",
        bot_version_id="v1",
        channel_code="web",
        lifecycle_state=LifecycleState.IDLE,
        version=1
    )
    handler.session_repo.get = AsyncMock(return_value=mock_session)
    handler.session_repo.update = AsyncMock(return_value=mock_session)
    
    # Execute valid transition: IDLE -> BROWSING
    result = await handler.update_flow_step(session_id, LifecycleState.BROWSING, tenant_id)
    
    # Verify
    assert result is not None
    handler.session_repo.update.assert_called_once()
    args = handler.session_repo.update.call_args[0]
    assert args[1]["lifecycle_state"] == LifecycleState.BROWSING

@pytest.mark.asyncio
async def test_invalid_state_transition():
    # Setup
    db = AsyncMock()
    handler = SessionStateHandler(db)
    
    session_id = str(uuid.uuid4())
    tenant_id = "tenant-1"
    
    # Mock existing session in BROWSING state
    mock_session = RuntimeSession(
        id=session_id,
        tenant_id=tenant_id,
        bot_id="bot-1",
        bot_version_id="v1",
        channel_code="web",
        lifecycle_state=LifecycleState.BROWSING,
        version=1
    )
    handler.session_repo.get = AsyncMock(return_value=mock_session)
    
    # Execute invalid transition: BROWSING -> PURCHASING (Skip VIEWING)
    # Valid flow: BROWSING -> VIEWING -> PURCHASING
    
    with pytest.raises(ValueError, match="Invalid state transition"):
        await handler.update_flow_step(session_id, LifecycleState.PURCHASING, tenant_id)
