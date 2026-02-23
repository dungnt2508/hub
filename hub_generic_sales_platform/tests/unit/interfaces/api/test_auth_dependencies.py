"""
Unit tests for Auth dependencies – get_current_tenant_id
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.interfaces.api.dependencies import get_current_tenant_id


@pytest.mark.asyncio
async def test_get_current_tenant_id_from_state():
    """tenant_id từ request.state (do AuthMiddleware set)"""
    from types import SimpleNamespace
    request = MagicMock()
    request.state = SimpleNamespace(tenant_id="tenant-123")
    request.headers.get = MagicMock(return_value=None)

    result = await get_current_tenant_id(request)
    assert result == "tenant-123"


@pytest.mark.asyncio
async def test_get_current_tenant_id_missing_when_state_none_raises():
    """Không còn fallback X-Tenant-ID - khi state.tenant_id=None thì 403"""
    from types import SimpleNamespace
    request = MagicMock()
    request.state = SimpleNamespace(tenant_id=None)
    request.headers.get = MagicMock(side_effect=lambda k: "tenant-456" if k == "X-Tenant-ID" else None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant_id(request)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_tenant_id_missing_raises():
    """Không có tenant_id → 403"""
    from types import SimpleNamespace
    request = MagicMock()
    request.state = SimpleNamespace(tenant_id=None)
    request.headers.get = MagicMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant_id(request)
    assert exc_info.value.status_code == 403
