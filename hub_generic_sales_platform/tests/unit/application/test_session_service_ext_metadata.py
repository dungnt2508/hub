"""Unit tests for SessionService ext_metadata (Sprint 3 - Zalo mapping)"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_or_create_session_with_ext_metadata():
    """Tạo session mới với ext_metadata (zalo_user_id)"""
    from app.application.services.session_service import SessionService

    db = AsyncMock()
    session_repo = MagicMock()
    version_repo = MagicMock()

    mock_version = MagicMock()
    mock_version.id = "bv-1"
    version_repo.get_active_version = AsyncMock(return_value=mock_version)

    mock_session = MagicMock()
    mock_session.id = "zalo_12345"
    mock_session.bot_version_id = "bv-1"
    mock_session.ext_metadata = {"zalo_user_id": "12345", "channel": "zalo"}
    session_repo.get = AsyncMock(return_value=None)
    session_repo.create = AsyncMock(return_value=mock_session)

    svc = SessionService(db)
    svc.session_repo = session_repo
    svc.version_repo = version_repo

    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def noop_scope(_):
        yield

    with patch("app.application.services.session_service.transaction_scope", noop_scope):
        result = await svc.get_or_create_session(
            tenant_id="t1",
            bot_id="b1",
            session_id="zalo_12345",
            channel_code="zalo",
            ext_metadata={"zalo_user_id": "12345", "channel": "zalo"},
        )

    assert result["session_id"] == "zalo_12345"
    session_repo.create.assert_called_once()
    call_kw = session_repo.create.call_args[0][0]
    assert "ext_metadata" in call_kw
    assert call_kw["ext_metadata"]["zalo_user_id"] == "12345"
