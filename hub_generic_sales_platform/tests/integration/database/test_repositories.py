"""Comprehensive Integration Tests for V4 Repositories"""

import pytest
import uuid
from app.infrastructure.database.repositories import OfferingRepository, OfferingVersionRepository, OfferingVariantRepository
from app.infrastructure.database.repositories import FAQRepository
from app.infrastructure.database.repositories import SessionRepository
from app.infrastructure.database.repositories import DecisionRepository
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.infrastructure.database.repositories import GuardrailRepository
from app.infrastructure.database.repositories import DomainAttributeDefinitionRepository
from app.infrastructure.database.repositories import InventoryRepository
from app.infrastructure.database.repositories import TenantPriceListRepository, TenantSalesChannelRepository
from app.infrastructure.database.repositories import SemanticCacheRepository

from app.core import domain

@pytest.mark.asyncio
async def test_ontology_and_offering_flow(db, tenant_1):
    """Test full flow: Domain -> Attribute Def -> Offering -> Version -> Variant"""
    # 1. Create Domain
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    domain_db = KnowledgeDomain(code="jewelry", name="Jewelry Domain")
    db.add(domain_db)
    await db.flush()

    # 2. Create Attribute Definition
    attr_repo = DomainAttributeDefinitionRepository(db)
    attr_def = await attr_repo.create({
        "domain_id": domain_db.id,
        "key": "material",
        "value_type": "text"
    }, tenant_id=tenant_1.id)
    assert attr_def.id is not None

    # 3. Create Offering (TenantOffering)
    off_repo = OfferingRepository(db)
    offering = await off_repo.create({
        "domain_id": domain_db.id,
        "code": "ring-001",
        "status": domain.OfferingStatus.ACTIVE
    }, tenant_id=tenant_1.id)
    
    found_off = await off_repo.get_by_code("ring-001", tenant_1.id, domain_id=domain_db.id)
    assert found_off.id == offering.id

    # 4. Create Version
    ver_repo = OfferingVersionRepository(db)
    version = await ver_repo.create({
        "offering_id": offering.id,
        "version": 1,
        "name": "Gold Ring",
        "status": domain.OfferingStatus.ACTIVE
    })
    
    active_ver = await ver_repo.get_active_version(offering.id, tenant_id=tenant_1.id)
    assert active_ver.id == version.id

    # 5. Create Variant
    var_repo = OfferingVariantRepository(db)
    variant = await var_repo.create({
        "offering_id": offering.id,
        "sku": "RING-GLD-01",
        "name": "Gold Ring Size 6"
    }, tenant_id=tenant_1.id)
    
    found_var = await var_repo.get_by_sku("RING-GLD-01", tenant_1.id)
    assert found_var.id == variant.id


@pytest.mark.asyncio
async def test_bot_and_knowledge_flow(db, tenant_1):
    """Test Bot -> FAQ / UseCase / Comparison"""
    # 1. Create Domain
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    domain_db = KnowledgeDomain(code="bot-domain", name="Bot Domain")
    db.add(domain_db)
    await db.flush()

    # 2. Create Bot
    bot_repo = BotRepository(db)
    bot = await bot_repo.create({
        "domain_id": domain_db.id,
        "code": "faq-bot",
        "name": "FAQ Assistant"
    }, tenant_id=tenant_1.id)

    # 3. Create FAQ (BotFAQ)
    faq_repo = FAQRepository(db)
    faq = await faq_repo.create({
        "bot_id": bot.id,
        "domain_id": domain_db.id,
        "question": "How to buy?",
        "answer": "Click the button",
        "is_active": True
    }, tenant_id=tenant_1.id)
    
    active_faqs = await faq_repo.get_active(tenant_1.id, bot_id=bot.id)
    assert len(active_faqs) == 1
    assert active_faqs[0].question == "How to buy?"


@pytest.mark.asyncio
async def test_runtime_flow(db, tenant_1):
    """Test Session -> Decision"""
    # 1. Create Bot & Version
    bot_repo = BotRepository(db)
    ver_repo = BotVersionRepository(db)
    
    bot = await bot_repo.create({"code": "run-bot", "name": "Runtime Bot"}, tenant_id=tenant_1.id)
    version = await ver_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})

    # 2. Create Session (RuntimeSession)
    session_repo = SessionRepository(db)
    session = await session_repo.create({
        "bot_id": bot.id,
        "bot_version_id": version.id,
        "channel_code": "webchat",
        "lifecycle_state": "IDLE"
    }, tenant_id=tenant_1.id)
    
    active_sessions = await session_repo.get_active_sessions(tenant_1.id)
    assert len(active_sessions) >= 1

    # 3. Create Decision (RuntimeDecisionEvent)
    decision_repo = DecisionRepository(db)
    decision = await decision_repo.create({
        "session_id": session.id,
        "bot_version_id": version.id,
        "decision_type": domain.DecisionType.PROCEED,
        "tier_code": "agentic",
        "latency_ms": 100
    }, tenant_id=tenant_1.id)
    
    found_decision = await decision_repo.get(decision.id, tenant_id=tenant_1.id)
    assert found_decision.tier_code == "agentic"


@pytest.mark.asyncio
async def test_guardrail_repository(db, tenant_1):
    """Test GuardrailRepository (TenantGuardrail)"""
    repo = GuardrailRepository(db)
    
    await repo.create({
        "code": "POL-001",
        "name": "No Profanity",
        "condition_expression": "contains_profanity(input)",
        "violation_action": "block",
        "priority": 1,
        "is_active": True
    }, tenant_id=tenant_1.id)
    
    active_policies = await repo.get_active_for_tenant(tenant_1.id)
    assert len(active_policies) == 1
    assert active_policies[0].code == "POL-001"


@pytest.mark.asyncio
async def test_inventory_repository(db, tenant_1):
    """Test InventoryRepository (TenantInventoryItem)"""
    from app.infrastructure.database.models.offering import TenantOffering, TenantOfferingVariant, TenantInventoryLocation
    
    # Setup - Domain already exists
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    domain = KnowledgeDomain(code="inv-domain", name="Inv Domain")
    db.add(domain)
    await db.flush()
    
    offering = TenantOffering(tenant_id=tenant_1.id, domain_id=domain.id, code="INV-PROD")
    db.add(offering)
    await db.flush()
    
    variant = TenantOfferingVariant(tenant_id=tenant_1.id, offering_id=offering.id, sku="SKU-INV", name="Inv Variant")
    db.add(variant)
    
    location = TenantInventoryLocation(tenant_id=tenant_1.id, code="WH1", name="Warehouse 1")
    db.add(location)
    await db.flush()
    
    repo = InventoryRepository(db)
    item = await repo.create({
        "variant_id": variant.id,
        "location_id": location.id,
        "stock_qty": 10
    }, tenant_id=tenant_1.id)
    
    status = await repo.get_stock_status(tenant_1.id, "SKU-INV")
    assert status is not None
    assert status["aggregate_qty"] == 10


@pytest.mark.asyncio
async def test_price_repository(db, tenant_1):
    """Test Pricing repositories"""
    channel_repo = TenantSalesChannelRepository(db)
    channel = await channel_repo.create({"code": "WEB", "name": "Web"}, tenant_id=tenant_1.id)
    
    price_list_repo = TenantPriceListRepository(db)
    price_list = await price_list_repo.create({
        "channel_id": channel.id,
        "code": "PROMO-2026"
    }, tenant_id=tenant_1.id)
    
    assert price_list.code == "PROMO-2026"


@pytest.mark.asyncio
async def test_cache_repository(db, tenant_1):
    """Test SemanticCacheRepository (TenantSemanticCache)"""
    repo = SemanticCacheRepository(db)
    
    await repo.create({
        "query_text": "hello world",
        "response_text": "Hi there!",
        "hit_count": 1
    }, tenant_id=tenant_1.id)
    
    # Simple check
    found = await repo.get_multi(tenant_id=tenant_1.id)
    assert len(found) >= 1
    assert found[0].query_text == "hello world"
