"""
Integration tests for Ontology API – domains, attribute definitions, tenant configs
"""
import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
async def test_list_domains(client):
    """Test GET /knowledge/domains"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get("/api/v1/knowledge/domains")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_domain(client, db):
    """Test POST /knowledge/domains"""
    code = f"ont-{uuid.uuid4().hex[:8]}"
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            "/api/v1/knowledge/domains",
            json={"code": code, "name": "Ontology Test Domain", "domain_type": "product"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == code
    assert data["name"] == "Ontology Test Domain"


@pytest.mark.asyncio
async def test_create_domain_400_duplicate(client, db):
    """Test POST /knowledge/domains - trùng code trả 400"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain

    dom = KnowledgeDomain(code=f"dup-{uuid.uuid4().hex[:6]}", name="Dup Domain")
    db.add(dom)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            "/api/v1/knowledge/domains",
            json={"code": dom.code, "name": "Another", "domain_type": "product"},
        )
    assert resp.status_code == 400
    assert "already exists" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_list_attribute_definitions(client, db):
    """Test GET /knowledge/attribute-definitions"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get("/api/v1/knowledge/attribute-definitions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_attribute_definitions_with_domain_id(client, db):
    """Test GET /knowledge/attribute-definitions?domain_id=..."""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain

    dom = KnowledgeDomain(code=f"attr-{uuid.uuid4().hex[:6]}", name="Attr Domain")
    db.add(dom)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get(f"/api/v1/knowledge/attribute-definitions?domain_id={dom.id}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_attribute_definition(client, db):
    """Test POST /knowledge/attribute-definitions"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain

    dom = KnowledgeDomain(code=f"def-{uuid.uuid4().hex[:6]}", name="Def Domain")
    db.add(dom)
    await db.flush()

    key = f"attr_{uuid.uuid4().hex[:6]}"
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            "/api/v1/knowledge/attribute-definitions",
            json={
                "domain_id": dom.id,
                "key": key,
                "value_type": "text",
                "scope": "offering",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == key
    assert data["domain_id"] == dom.id


@pytest.mark.asyncio
async def test_create_attribute_definition_400_duplicate(client, db):
    """Test POST /knowledge/attribute-definitions - trùng key trả 400"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain, DomainAttributeDefinition

    dom = KnowledgeDomain(code=f"dupattr-{uuid.uuid4().hex[:6]}", name="Dup Attr Domain")
    db.add(dom)
    await db.flush()

    key = f"dupkey_{uuid.uuid4().hex[:4]}"
    attr = DomainAttributeDefinition(domain_id=dom.id, key=key, value_type="text", scope="offering")
    db.add(attr)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id="t1", role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            "/api/v1/knowledge/attribute-definitions",
            json={"domain_id": dom.id, "key": key, "value_type": "number", "scope": "offering"},
        )
    assert resp.status_code == 400
    assert "already exists" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_list_tenant_configs(client, tenant_1):
    """Test GET /knowledge/attribute-configs"""
    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.get(
            "/api/v1/knowledge/attribute-configs",
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_update_tenant_config_create(client, tenant_1, db):
    """Test POST /knowledge/attribute-definitions/{id}/config - tạo mới"""
    from app.infrastructure.database.models.knowledge import KnowledgeDomain, DomainAttributeDefinition

    dom = KnowledgeDomain(code=f"cfg-{uuid.uuid4().hex[:6]}", name="Config Domain")
    db.add(dom)
    await db.flush()

    attr = DomainAttributeDefinition(
        domain_id=dom.id, key=f"cfg_attr_{uuid.uuid4().hex[:4]}",
        value_type="text", scope="offering"
    )
    db.add(attr)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            f"/api/v1/knowledge/attribute-definitions/{attr.id}/config",
            json={"label": "My Label", "is_display": True, "is_searchable": False},
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "My Label"
    assert data["is_display"] is True


@pytest.mark.asyncio
async def test_update_tenant_config_update(client, tenant_1, db):
    """Test POST /knowledge/attribute-definitions/{id}/config - cập nhật config có sẵn"""
    from app.infrastructure.database.models.knowledge import (
        KnowledgeDomain, DomainAttributeDefinition, TenantAttributeConfig,
    )

    dom = KnowledgeDomain(code=f"updcfg-{uuid.uuid4().hex[:6]}", name="Update Config Domain")
    db.add(dom)
    await db.flush()

    attr = DomainAttributeDefinition(
        domain_id=dom.id, key=f"upd_attr_{uuid.uuid4().hex[:4]}",
        value_type="text", scope="offering",
    )
    db.add(attr)
    await db.flush()

    cfg = TenantAttributeConfig(
        tenant_id=tenant_1.id,
        attribute_def_id=attr.id,
        label="Old Label",
        is_display=False,
        is_searchable=True,
    )
    db.add(cfg)
    await db.flush()

    with patch("app.core.services.auth_service.AuthService.get_user_from_token", new_callable=AsyncMock) as m:
        m.return_value = MagicMock(tenant_id=tenant_1.id, role="admin", status="active", tenant=MagicMock(status="active"))
        resp = await client.post(
            f"/api/v1/knowledge/attribute-definitions/{attr.id}/config",
            json={"label": "New Label", "is_display": True},
            headers={"X-Tenant-ID": tenant_1.id},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "New Label"
    assert data["is_display"] is True
