"""
Integration tests for Catalog API
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
async def test_list_offerings_200(client, tenant_1, offering_v4):
    """Test GET /catalog/offerings - trả danh sách offerings"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/offerings",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Có thể có offering từ offering_v4 fixture
    if data:
        assert "id" in data[0] or "code" in data[0]


@pytest.mark.asyncio
async def test_get_offering_by_code_200(client, tenant_1, offering_v4):
    """Test GET /catalog/offerings/{code}"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            f"/api/v1/catalog/offerings/{offering_v4.code}",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == offering_v4.code


@pytest.mark.asyncio
async def test_get_offering_by_code_404(client, tenant_1):
    """Test GET /catalog/offerings/{code} - không tồn tại trả 404"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/offerings/NONEXISTENT-CODE-XYZ",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_channels_200(client, tenant_1, channel_web):
    """Test GET /catalog/channels"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/channels",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_price_lists_200(client, tenant_1):
    """Test GET /catalog/price-lists"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/price-lists",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_locations_200(client, tenant_1):
    """Test GET /catalog/locations"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/locations",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_inventory_status_200(client, tenant_1):
    """Test GET /catalog/inventory/status"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(
            tenant_id=tenant_1.id, role="admin", status="active",
            tenant=MagicMock(status="active"),
        )
        resp = await client.get(
            "/api/v1/catalog/inventory/status",
            headers={"Authorization": "Bearer test_token", "X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
