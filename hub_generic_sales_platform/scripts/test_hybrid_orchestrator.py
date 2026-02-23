
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.infrastructure.database.engine import get_session_maker, init_database
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.infrastructure.database.repositories import TenantRepository
from app.infrastructure.database.repositories import SemanticCacheRepository
from app.infrastructure.database.repositories import FAQRepository
from app.core.shared.llm_service import get_llm_service

async def setup_test_data(db, tenant_id, bot_id):
    # Setup Tenant
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        await tenant_repo.create({"id": tenant_id, "name": "Test Tenant"})
    
    # Setup Bot
    bot_repo = BotRepository(db)
    bot = await bot_repo.get(bot_id)
    if not bot:
        bot = await bot_repo.create({"id": bot_id, "tenant_id": tenant_id, "name": "Test Bot", "code": "TEST_BOT"})
    
    # Setup Bot Version
    version_repo = BotVersionRepository(db)
    version = await version_repo.get_active_version(bot_id)
    if not version:
        version = await version_repo.create({
            "bot_id": bot_id,
            "version": 1,
            "is_active": True
        })
    
    # Setup Cache
    cache_repo = SemanticCacheRepository(db)
    llm = get_llm_service()
    emb = await llm.get_embedding("Giá sản phẩm này bao nhiêu?")
    await cache_repo.create({
        "tenant_id": tenant_id,
        "query_text": "Giá sản phẩm này bao nhiêu?",
        "response_text": "Sản phẩm này giá 1.000.000đ.",
        "embedding": emb
    })

    # Setup FAQ
    faq_repo = FAQRepository(db)
    emb_faq = await llm.get_embedding("Chính sách đổi trả như thế nào?")
    await faq_repo.create({
        "tenant_id": tenant_id,
        "bot_id": bot_id,
        "question": "Chính sách đổi trả như thế nào?",
        "answer": "Chúng tôi hỗ trợ đổi trả trong 7 ngày.",
        "embedding": emb_faq,
        "is_active": True
    })

    await db.commit()

async def test_flow():
    await init_database()
    session_maker = get_session_maker()
    
    tenant_id = "test-tenant-1"
    bot_id = "test-bot-1"
    
    async with session_maker() as db:
        await setup_test_data(db, tenant_id, bot_id)
        
        orchestrator = HybridOrchestrator(db)
        
        print("\n--- Testing TIER 1: FAST PATH ---")
        res1 = await orchestrator.handle_message(tenant_id, bot_id, "Chào bạn")
        print(f"User: Chào bạn")
        print(f"Bot: {res1['response']}")
        print(f"Metadata: {res1['metadata']}")
        
        print("\n--- Testing TIER 2: CACHE PATH ---")
        res2 = await orchestrator.handle_message(tenant_id, bot_id, "Cho hỏi giá sản phẩm này")
        print(f"User: Cho hỏi giá sản phẩm này")
        print(f"Bot: {res2['response']}")
        print(f"Metadata: {res2['metadata']}")
        
        print("\n--- Testing TIER 2: FAQ PATH ---")
        res3 = await orchestrator.handle_message(tenant_id, bot_id, "Bạn có hỗ trợ đổi trả không?")
        print(f"User: Bạn có hỗ trợ đổi trả không?")
        print(f"Bot: {res3['response']}")
        print(f"Metadata: {res3['metadata']}")
        
        print("\n--- Testing TIER 3: AGENTIC PATH ---")
        res4 = await orchestrator.handle_message(tenant_id, bot_id, "Tìm cho tôi tivi màn hình cong dưới 10 triệu")
        print(f"User: Tìm cho tôi tivi màn hình cong dưới 10 triệu")
        print(f"Bot: {res4['response']}")
        print(f"Metadata: {res4['metadata']}")

if __name__ == "__main__":
    asyncio.run(test_flow())
