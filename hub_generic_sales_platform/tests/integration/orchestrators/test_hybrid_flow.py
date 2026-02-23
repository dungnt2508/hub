"""Integration tests for Hybrid Orchestrator - Sprint 2"""

import pytest
import uuid
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.infrastructure.database.repositories import SemanticCacheRepository
from app.infrastructure.database.repositories import FAQRepository
from app.infrastructure.database.repositories import DecisionRepository
from app.infrastructure.database.models.decision import DecisionType

@pytest.mark.asyncio
async def test_hybrid_flow_complete_cycle(db, tenant_1, tenant_2):
    """Test full 3-tier hybrid flow with observability"""
    
    # 1. Setup Data
    cache_repo = SemanticCacheRepository(db)
    faq_repo = FAQRepository(db)
    decision_repo = DecisionRepository(db)
    
    # Create bot version for testing
    from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    domain = KnowledgeDomain(code=f"hybrid-dom-{uuid.uuid4().hex[:4]}", name="Hybrid Domain")
    db.add(domain)
    await db.flush()

    bot = await bot_repo.create({"code": "hybrid-bot", "name": "AI Assistant", "domain_id": domain.id}, tenant_id=tenant_1.id)
    version = await version_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
    
    # Tier 2 Seed
    mock_vector = [0.1] * 1536
    await cache_repo.create({
        "query_text": "giá sản phẩm x",
        "response_text": "Giá sản phẩm X là 500k.",
    }, tenant_id=tenant_1.id)
    
    await faq_repo.create({
        "bot_id": bot.id,
        "question": "Bạn ở đâu?",
        "answer": "Tôi ở trong mây!",
        "embedding": mock_vector, 
        "is_active": True,
        "domain_id": bot.domain_id
    }, tenant_id=tenant_1.id)
    
    orchestrator = HybridOrchestrator(db)
    
    # --- TIER 1: Social ---
    print("\n[TEST] Handling Social Message (Tier 1)...")
    resp1 = await orchestrator.handle_message(tenant_1.id, bot.id, "Chào bạn!")
    print(f"  Request: Chào bạn! -> Response: {resp1['response']}")
    print(f"  Metadata: {resp1['metadata']}")
    assert "chào" in resp1["response"].lower()
    assert resp1["metadata"]["tier"] == "fast_path"
    session_id = resp1["session_id"]
    
    # --- TIER 2A: Cache ---
    print("\n[TEST] Handling Cached Query (Tier 2A)...")
    resp2 = await orchestrator.handle_message(tenant_1.id, bot.id, "giá sản phẩm x", session_id=session_id)
    print(f"  Request: giá sản phẩm x -> Response: {resp2['response']}")
    print(f"  Metadata: {resp2['metadata']}")
    assert "500k" in resp2["response"]
    assert resp2["metadata"]["tier"] == "knowledge_path"
    
    # --- TIER 2B: FAQ ---
    print("\n[TEST] Handling FAQ Query (Tier 2B)...")
    # Mock get_embedding để trả về vector giống với FAQ đã seed
    from unittest.mock import patch, AsyncMock
    with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.get_embedding = AsyncMock(return_value=mock_vector)
        mock_get_llm.return_value = mock_llm
        
        resp3 = await orchestrator.handle_message(tenant_1.id, bot.id, "Bạn ở đâu?", session_id=session_id)
        print(f"  Request: Bạn ở đâu? -> Response: {resp3['response']}")
        print(f"  Metadata: {resp3['metadata']}")
        assert "mây" in resp3["response"]
        assert resp3["metadata"]["tier"] == "knowledge_path"
    
    # --- TIER 2C: Semantic Fallback ---
    print("\n[TEST] Handling Semantic Query (Tier 2C)...")
    # "Địa chỉ của bạn?" is semantically similar to "Bạn ở đâu?"
    # Note: This requires mocking LLM.get_embedding to return the mock_vector
    with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.get_embedding = AsyncMock(return_value=mock_vector)  # Perfect match for FAQ
        mock_get_llm.return_value = mock_llm
        
        resp_semantic = await orchestrator.handle_message(tenant_1.id, bot.id, "Địa chỉ của bạn?", session_id=session_id)
        print(f"  Request: Địa chỉ của bạn? -> Response: {resp_semantic['response']}")
        assert "mây" in resp_semantic["response"]
        assert resp_semantic["metadata"]["tier"] == "knowledge_path"

    # --- TIER 3: Dynamic Tool Calling ---
    print("\n[TEST] Handling Dynamic Tool Call (Tier 3)...")
    # Patch generate_response của llm_service instance trong AgentOrchestrator
    mock_tool_call = AsyncMock()
    mock_tool_call.function.name = "compare_offerings"
    mock_tool_call.function.arguments = "{}"
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [
            {"response": "", "tool_calls": [mock_tool_call]}, # First turn: Think
            {"response": "Đã so sánh xong.", "tool_calls": []} # Second turn: Report
        ]
        
        resp_tool = await orchestrator.handle_message(tenant_1.id, bot.id, "So sánh sản phẩm", session_id=session_id)
        print(f"  Request: So sánh sản phẩm -> Response: {resp_tool['response']}")
        assert "so sánh" in resp_tool["response"].lower()
        assert resp_tool["metadata"]["tier"] == "agentic_path"

    # --- Verify Observability in DB ---
    print("\n[TEST] Verifying Observability Data in DB...")
    decisions = await decision_repo.get_by_session(resp1["session_id"], tenant_id=tenant_1.id)
    for d in decisions:
        print(f"  Logged Decision: ID={d.id[:8]}, Tier={d.tier_code}, Type={d.decision_type}, Cost=${d.estimated_cost}")
    
    # Check if cases were logged
    tiers_found = [d.tier_code for d in decisions]
    assert "fast_path" in tiers_found
    assert "knowledge_path" in tiers_found
    assert "agentic_path" in tiers_found
    
    print("\n[SUCCESS] All paths (including semantic and dynamic tool calls) verified.")
