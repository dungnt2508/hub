"""Integration tests for Hybrid Orchestrator - Sprint 3 Enhanced Features"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.infrastructure.database.repositories import SemanticCacheRepository
from app.infrastructure.database.repositories import FAQRepository
from app.infrastructure.database.repositories import DecisionRepository
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.infrastructure.database.models.decision import DecisionType

@pytest.mark.asyncio
async def test_orchestrator_usage_and_cost(db, tenant_1):
    """Test cost calculation and usage tracking across all tiers"""
    
    # 1. Setup Data
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    cache_repo = SemanticCacheRepository(db)
    faq_repo = FAQRepository(db)
    decision_repo = DecisionRepository(db)
    
    from app.infrastructure.database.models.knowledge import KnowledgeDomain
    domain = KnowledgeDomain(code=f"s3-dom-{uuid.uuid4().hex[:4]}", name="Sprint 3 Domain")
    db.add(domain)
    await db.flush()
    
    bot = await bot_repo.create({"code": "s3-bot", "name": "Sprint 3 Bot", "domain_id": domain.id}, tenant_id=tenant_1.id)
    version = await version_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
    
    orchestrator = HybridOrchestrator(db)
    
    # --- TIER 1: FAST PATH ---
    resp_fast = await orchestrator.handle_message(tenant_1.id, bot.id, "Chào bạn")
    assert resp_fast["metadata"]["tier"] == "fast_path"
    assert resp_fast["metadata"]["cost"] == "$0.00000"
    
    # Verify DB log
    decisions = await decision_repo.get_by_session(resp_fast["session_id"], tenant_id=tenant_1.id)
    assert len(decisions) >= 1
    assert decisions[0].tier_code == "fast_path"
    assert "Pattern matched" in decisions[0].decision_reason

    # --- TIER 2: KNOWLEDGE PATH (FAQ) ---
    mock_vector = [0.1] * 1536
    await faq_repo.create({
        "question": "What is IRIS?",
        "answer": "IRIS is a smart hub.",
        "embedding": mock_vector,
        "is_active": True,
        "domain_id": bot.domain_id,
        "bot_id": bot.id  # Ensure FAQ is linked to bot
    }, tenant_id=tenant_1.id)
    await db.commit()  # Ensure FAQ is persisted

    # Mock cache to return None (no cache match)
    with patch.object(orchestrator.semantic_cache_service, "find_match", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None  # No cache match
        
        with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm:
            mock_llm = AsyncMock()
            # Vector for FAQ match (should match with threshold 0.85)
            # Same vector [0.1]*1536 will have cosine similarity = 1.0 (perfect match)
            mock_llm.get_embedding = AsyncMock(return_value=mock_vector)
            mock_get_llm.return_value = mock_llm
            
            resp_faq = await orchestrator.handle_message(tenant_1.id, bot.id, "What is IRIS?")
            assert resp_faq["metadata"]["tier"] == "knowledge_path", \
                f"Expected knowledge_path but got {resp_faq['metadata']['tier']}. " \
                f"Response: {resp_faq.get('response', '')[:100]}"
            assert float(resp_faq["metadata"]["cost"].replace("$", "")) > 0

            # Verify DB log
            results = await decision_repo.get_by_session(resp_faq["session_id"], tenant_id=tenant_1.id)
            # Recent decisions come first if ordered by created_at desc
            faq_decision = next((d for d in results if d.tier_code == "knowledge_path"), None)
            assert faq_decision is not None, "No knowledge_path decision found in DB"
            assert "FAQ semantic match" in faq_decision.decision_reason
            assert "similarity" in faq_decision.decision_reason

    # --- TIER 3: AGENTIC PATH (Usage Aggregation) ---
    # Ensure no FAQ/cache match by using a unique query
    unique_query = f"Find me a very specific product XYZ-{uuid.uuid4().hex[:8]}"
    
    # Mock LLM to return usage data
    mock_usage_1 = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    mock_usage_2 = {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}
    
    mock_tool_call = AsyncMock()
    mock_tool_call.function.name = "search_offerings"
    mock_tool_call.function.arguments = '{"query": "XYZ"}'
    
    # Mock embedding to return different vector (not matching FAQ)
    mock_vector_agentic = [0.5] * 1536  # Different from FAQ vector [0.1] * 1536
    
    # Mock both cache and FAQ repositories to return None (no matches)
    with patch.object(orchestrator.semantic_cache_service, "find_match", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None  # No cache match
        
        with patch.object(orchestrator.faq_repo, "semantic_search", new_callable=AsyncMock) as mock_faq:
            mock_faq.return_value = []  # No FAQ match
            
            # Mock LLM service at both levels: hybrid_orchestrator (for embedding) and agent_orchestrator (for generate_response)
            with patch("app.application.orchestrators.hybrid_orchestrator.get_llm_provider") as mock_get_llm_hybrid:
                mock_llm_hybrid = AsyncMock()
                mock_llm_hybrid.get_embedding = AsyncMock(return_value=mock_vector_agentic)
                mock_get_llm_hybrid.return_value = mock_llm_hybrid
                
                # Mock agent_orchestrator's llm_service directly (it's initialized in __init__)
                with patch.object(orchestrator.agent_orchestrator, "llm_service") as mock_llm_agent:
                    mock_llm_agent.get_embedding = AsyncMock(return_value=mock_vector_agentic)
                    mock_llm_agent.generate_response = AsyncMock(side_effect=[
                        {"response": "", "tool_calls": [mock_tool_call], "usage": mock_usage_1}, # Turn 1
                        {"response": "Đây là kết quả tìm kiếm.", "tool_calls": [], "usage": mock_usage_2} # Turn 2
                    ])
                    
                    resp_agent = await orchestrator.handle_message(tenant_1.id, bot.id, unique_query)
                    
                    # Verify usage aggregation
                    expected_total_tokens = 450
                    assert resp_agent["metadata"]["tier"] == "agentic_path", \
                        f"Expected agentic_path but got {resp_agent['metadata']['tier']}. " \
                        f"Response: {resp_agent.get('response', '')[:100]}"
                    assert resp_agent["metadata"]["usage"]["total_tokens"] == expected_total_tokens, \
                        f"Expected {expected_total_tokens} tokens but got {resp_agent['metadata']['usage']['total_tokens']}"
                    
                    # Verify cost calculation: base_fee (0.005) + (450/1000 * 0.01) = 0.005 + 0.0045 = 0.0095
                    cost_float = float(resp_agent["metadata"]["cost"].replace("$", ""))
                    assert 0.0094 <= cost_float <= 0.0096
                    
                    # Verify DB log
                    results = await decision_repo.get_by_session(resp_agent["session_id"], tenant_id=tenant_1.id)
                    agent_decision = next(d for d in results if d.tier_code == "agentic_path")
                    assert agent_decision.token_usage["total_tokens"] == expected_total_tokens
                    assert agent_decision.estimated_cost >= 0.0095
