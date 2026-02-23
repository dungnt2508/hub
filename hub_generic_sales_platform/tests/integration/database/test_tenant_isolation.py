"""Tests for mandatory tenant isolation in repositories"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import BotRepository, OfferingRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_without_tenant_id_raises_error(db: AsyncSession):
    """Test that get() raises ValueError when tenant_id is missing for multi-tenant model"""
    
    repo = BotRepository(db)
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await repo.get(id="any_id", tenant_id=None)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_multi_without_tenant_id_raises_error(db: AsyncSession):
    """Test that get_multi() raises ValueError when tenant_id is missing"""
    
    repo = BotRepository(db)
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await repo.get_multi(tenant_id=None)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_without_tenant_id_raises_error(db: AsyncSession):
    """Test that create() raises ValueError when tenant_id is missing"""
    
    repo = BotRepository(db)
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await repo.create(
            {"code": "TEST", "name": "Test Bot"},
            tenant_id=None
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_without_tenant_id_raises_error(db: AsyncSession):
    """Test that delete() raises ValueError when tenant_id is missing"""
    
    repo = BotRepository(db)
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await repo.delete(id="any_id", tenant_id=None)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_tenant_get_returns_none(db: AsyncSession, tenant_1, tenant_2):
    """Test that getting another tenant's resource returns None"""
    
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    # Create domain
    domain = KnowledgeDomain(code="dom_test", name="Test Domain")
    db.add(domain)
    await db.flush()
    
    repo = BotRepository(db)
    
    # Create bot for tenant_1
    bot = await repo.create({
        "code": "T1_BOT",
        "name": "Tenant 1 Bot",
        "domain_id": domain.id
    }, tenant_id=tenant_1.id)
    
    # Try to get it as tenant_2
    result = await repo.get(bot.id, tenant_id=tenant_2.id)
    
    # Should return None (tenant isolation)
    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_tenant_list_empty(db: AsyncSession, tenant_1, tenant_2):
    """Test that list returns only current tenant's resources"""
    
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    
    domain = KnowledgeDomain(code="dom_list", name="List Domain")
    db.add(domain)
    await db.flush()
    
    repo = BotRepository(db)
    
    # Create bots for both tenants
    await repo.create({
        "code": "T1_BOT_A",
        "name": "T1 Bot A",
        "domain_id": domain.id
    }, tenant_id=tenant_1.id)
    
    await repo.create({
        "code": "T2_BOT_B",
        "name": "T2 Bot B",
        "domain_id": domain.id
    }, tenant_id=tenant_2.id)
    
    # List for tenant_1
    tenant1_bots = await repo.get_multi(tenant_id=tenant_1.id)
    codes_t1 = [b.code for b in tenant1_bots]
    
    # List for tenant_2
    tenant2_bots = await repo.get_multi(tenant_id=tenant_2.id)
    codes_t2 = [b.code for b in tenant2_bots]
    
    # Each tenant should only see their own
    assert "T1_BOT_A" in codes_t1
    assert "T2_BOT_B" not in codes_t1
    
    assert "T2_BOT_B" in codes_t2
    assert "T1_BOT_A" not in codes_t2
