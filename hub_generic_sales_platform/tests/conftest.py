"""Pytest configuration and fixtures (Async Implementation)"""

import pytest
import asyncio
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.tenant import Tenant, TenantStatus, TenantPlan
from app.infrastructure.database.models.offering import (
    TenantOffering, TenantOfferingVersion, OfferingStatus,
    TenantOfferingVariant, TenantSalesChannel, TenantPriceList
)
from app.infrastructure.database.models.knowledge import (
    KnowledgeDomain
)
from app.infrastructure.database.models.bot import Bot, BotStatus
from app.core.config.settings import get_settings

settings = get_settings()

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-wide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine using SQLite in-memory for speed and reliability"""
    from sqlalchemy.pool import StaticPool
    
    # SQLite in-memory requires StaticPool to share connection across the session
    test_sqlite_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        test_sqlite_url, 
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Create dummy inventory_status_view for SQLite compatibility
        if engine.dialect.name == "sqlite":
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS offering_inventory_status_view (
                    tenant_id TEXT,
                    offering_id TEXT,
                    offering_code TEXT,
                    offering_name TEXT,
                    variant_id TEXT,
                    sku TEXT,
                    variant_name TEXT,
                    aggregate_qty INTEGER,
                    aggregate_safety_stock INTEGER,
                    stock_status TEXT
                )
            """))
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    Session join transaction của connection. Các service dùng begin_nested() để tạo savepoint.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    async_session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
    )
    
    yield async_session
    
    await async_session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def tenant_1(db: AsyncSession) -> Tenant:
    """Create test tenant 1"""
    tenant = Tenant(        
        name=f"Test Tenant 1 - {uuid.uuid4().hex[:4]}",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.PRO
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_2(db: AsyncSession) -> Tenant:
    """Create test tenant 2"""
    tenant = Tenant(        
        name=f"Test Tenant 2 - {uuid.uuid4().hex[:4]}",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.FREE
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def bot_1(db: AsyncSession, tenant_1: Tenant) -> Bot:
    """Create test bot 1"""
    # Create a domain first for the bot
    domain = KnowledgeDomain(
        code=f"test-domain-{uuid.uuid4().hex[:4]}",
        name="Test Domain"
    )
    db.add(domain)
    await db.flush()

    bot = Bot(
        tenant_id=tenant_1.id,
        domain_id=domain.id,
        code=f"test-bot-1-{uuid.uuid4().hex[:4]}",
        name="Test Bot 1",
        status=BotStatus.ACTIVE
    )
    db.add(bot)
    await db.flush()
    await db.refresh(bot)
    return bot


@pytest.fixture
async def bot_tenant_1(db: AsyncSession, tenant_1: Tenant) -> Bot:
    """Create bot for tenant 1"""
    domain = KnowledgeDomain(code=f"dom-t1-{uuid.uuid4().hex[:4]}", name="Domain T1")
    db.add(domain)
    await db.flush()

    bot = Bot(
        tenant_id=tenant_1.id,
        domain_id=domain.id,
        code=f"bot-t1-{uuid.uuid4().hex[:4]}",
        name="Bot Tenant 1",
        status=BotStatus.ACTIVE
    )
    db.add(bot)
    await db.flush()
    await db.refresh(bot)
    return bot


@pytest.fixture
async def bot_tenant_2(db: AsyncSession, tenant_2: Tenant) -> Bot:
    """Create bot for tenant 2"""
    domain = KnowledgeDomain(code=f"dom-t2-{uuid.uuid4().hex[:4]}", name="Domain T2")
    db.add(domain)
    await db.flush()

    bot = Bot(
        tenant_id=tenant_2.id,
        domain_id=domain.id,
        code=f"bot-t2-{uuid.uuid4().hex[:4]}",
        name="Bot Tenant 2",
        status=BotStatus.ACTIVE
    )
    db.add(bot)
    await db.flush()
    await db.refresh(bot)
    return bot


@pytest.fixture
async def offering_tenant_1(db: AsyncSession, tenant_1: Tenant, bot_tenant_1: Bot) -> TenantOffering:
    """Create offering for tenant 1 with bot_id"""
    offering = TenantOffering(
        tenant_id=tenant_1.id,
        domain_id=bot_tenant_1.domain_id,
        bot_id=bot_tenant_1.id,
        code=f"off-t1-{uuid.uuid4().hex[:4]}",
        status=OfferingStatus.ACTIVE
    )
    db.add(offering)
    await db.flush()
    await db.refresh(offering)
    return offering


@pytest.fixture
async def offering_tenant_2(db: AsyncSession, tenant_2: Tenant, bot_tenant_2: Bot) -> TenantOffering:
    """Create offering for tenant 2 with bot_id"""
    offering = TenantOffering(
        tenant_id=tenant_2.id,
        domain_id=bot_tenant_2.domain_id,
        bot_id=bot_tenant_2.id,
        code=f"off-t2-{uuid.uuid4().hex[:4]}",
        status=OfferingStatus.ACTIVE
    )
    db.add(offering)
    await db.flush()
    await db.refresh(offering)
    return offering


# --- CATALOG V4 FIXTURES ---

@pytest.fixture
async def channel_web(db: AsyncSession, tenant_1: Tenant) -> TenantSalesChannel:
    """Create dummy web channel"""
    channel = TenantSalesChannel(tenant_id=tenant_1.id, code="WEB", name="Web Channel")
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return channel


@pytest.fixture
async def offering_v4(db: AsyncSession, tenant_1: Tenant, bot_1: Bot) -> TenantOffering:
    """Create offering with active version (Catalog V4)"""
    offering = TenantOffering(
        tenant_id=tenant_1.id,
        domain_id=bot_1.domain_id,
        bot_id=bot_1.id,
        code=f"off-{uuid.uuid4().hex[:8]}",
        status=OfferingStatus.ACTIVE
    )
    db.add(offering)
    await db.flush()
    
    version = TenantOfferingVersion(
        offering_id=offering.id,
        version=1,
        name="Standard Offering Name",
        description="Detailed description for v4 tests",
        status=OfferingStatus.ACTIVE
    )
    db.add(version)
    
    # Create a default variant
    variant = TenantOfferingVariant(
        tenant_id=tenant_1.id,
        offering_id=offering.id,
        sku=f"{offering.code}-STD",
        name="Standard variant",
        status=OfferingStatus.ACTIVE
    )
    db.add(variant)
    
    await db.flush()
    await db.refresh(offering)
    return offering

@pytest.fixture
async def client(db: AsyncSession):
    """Fixture for FastAPI async client override db"""
    from app.main import app
    from app.infrastructure.database.engine import get_session
    from httpx import ASGITransport, AsyncClient
    from unittest.mock import patch
    
    # Override get_session dependency to use the test db fixture
    async def override_get_session():
        yield db
    
    app.dependency_overrides[get_session] = override_get_session
    
    # Patch get_bearer_token to return a dummy token so the AuthMiddleware proceeds to validation
    with patch("app.interfaces.middleware.auth.get_bearer_token", return_value="test_token"):
        async with AsyncClient(
            transport=ASGITransport(app=app), 
            base_url="http://test",
            headers={"Authorization": "Bearer test_token"}
        ) as ac:
            yield ac
    
    app.dependency_overrides.clear()
