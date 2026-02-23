"""
Integration tests for Auth API – login, /me
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_login_401_invalid_credentials(client):
    """Test POST /auth/login - sai mật khẩu trả 401"""
    with patch("app.core.services.auth_service.AuthService.authenticate_user", new_callable=AsyncMock) as m:
        m.return_value = None
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "wrong"},
        )
    assert resp.status_code == 401
    assert "Invalid" in resp.json().get("detail", "") or "invalid" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_login_200(client, db):
    """Test POST /auth/login - đúng credentials trả 200 + token"""
    mock_user = MagicMock()
    mock_user.id = "user-1"
    mock_user.email = "admin@test.com"
    mock_user.role = "admin"
    mock_user.tenant_id = "tenant-1"
    mock_user.tenant = MagicMock(name="Test Tenant")

    with patch("app.core.services.auth_service.AuthService.authenticate_user", new_callable=AsyncMock) as m_auth:
        with patch("app.core.services.auth_service.AuthService.generate_jwt_token") as m_jwt:
            m_auth.return_value = mock_user
            m_jwt.return_value = "fake.jwt.token"

            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@test.com", "password": "correct"},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"] == "fake.jwt.token"
    assert data.get("user", {}).get("email") == "admin@test.com"


@pytest.mark.asyncio
async def test_me_200(client, tenant_1, db):
    """Test GET /auth/me - có token trả 200"""
    from app.infrastructure.database.models.tenant import UserAccount

    user = UserAccount(
        tenant_id=tenant_1.id,
        email=f"me-{tenant_1.id[:8]}@test.com",
        password_hash="unused",
        role="admin",
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        mock_u = MagicMock()
        mock_u.id = user.id
        mock_u.tenant_id = tenant_1.id
        mock_u.role = "admin"
        mock_u.status = "active"
        mock_u.tenant = MagicMock(status="active")
        m.return_value = mock_u

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test_token"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == user.email
    assert data["tenant_id"] == tenant_1.id
