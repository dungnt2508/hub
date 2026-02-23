import pytest
import uuid
from unittest.mock import patch, AsyncMock
from app.application.orchestrators.hybrid_orchestrator import HybridOrchestrator
from app.infrastructure.database.repositories import BotRepository, BotVersionRepository
from app.core.domain.runtime import LifecycleState

pytestmark = pytest.mark.e2e

@pytest.mark.asyncio
async def test_full_shopping_journey_e2e(db, tenant_1, offering_v4, channel_web):
    """
    Kịch bản người dùng thật: 
    1. Chào hỏi (Fast Path)
    2. Hỏi sản phẩm (Agentic Path - Search)
    3. Hỏi chi tiết & giá (Agentic Path - Details V4)
    """
    
    # --- SETUP BOT ---
    bot_repo = BotRepository(db)
    version_repo = BotVersionRepository(db)
    bot = await bot_repo.create({"code": "e2e-bot", "name": "Shopping Assistant"}, tenant_id=tenant_1.id)
    await version_repo.create({"bot_id": bot.id, "version": 1, "is_active": True})
    
    orchestrator = HybridOrchestrator(db)
    session_id = None
    
    # --- TURN 1: GREETING (Tier 1) ---
    print("\n[E2E] Turn 1: Greeting")
    resp_1 = await orchestrator.handle_message(tenant_1.id, bot.id, "Chào shop")
    session_id = resp_1["session_id"]
    
    assert resp_1["metadata"]["tier"] == "fast_path"
    assert "chào" in resp_1["response"].lower()
    
    # --- TURN 2: SEARCH (Tier 3) ---
    print("[E2E] Turn 2: Search Request")
    
    # Mock LLM để giả lập Agent quyết định gọi tool search_products
    mock_search_call = AsyncMock()
    mock_search_call.function.name = "search_offerings"
    mock_search_call.function.arguments = '{"query": "iPhone"}'
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [
            {"response": "Để tôi tìm cho bạn.", "tool_calls": [mock_search_call]}, # AI muốn gọi tool
            {"response": "Tôi thấy có iPhone 15 trong kho.", "tool_calls": []}     # AI trả lời sau khi tool chạy
        ]
        
        resp_2 = await orchestrator.handle_message(
            tenant_1.id, bot.id, "Bên mình còn iPhone không?", session_id=session_id
        )
        
        assert resp_2["metadata"]["tier"] == "agentic_path"
        assert "iPhone 15" in resp_2["response"]
        
    # --- TURN 3: DETAILS & PRICE (Tier 3 - Catalog V4) ---
    print("[E2E] Turn 3: Ask for Price & Details")
    
    # Mock LLM để AI gọi tool get_product_details
    mock_details_call = AsyncMock()
    mock_details_call.function.name = "get_offering_details"
    mock_details_call.function.arguments = f'{{"offering_code": "{offering_v4.code}"}}'
    
    with patch.object(orchestrator.agent_orchestrator.llm_service, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [
            {"response": "Đợi tôi chút để kiểm tra giá mới nhất.", "tool_calls": [mock_details_call]},
            {"response": "iPhone 15 đang có giá ưu đãi, bạn xem nhé.", "tool_calls": []}
        ]
        
        resp_3 = await orchestrator.handle_message(
            tenant_1.id, bot.id, "Giá của nó bao nhiêu vậy?", session_id=session_id
        )
        
        # Verify kết quả cuối cùng
        assert resp_3["metadata"]["tier"] == "agentic_path"
        # Trạng thái session phải được cập nhật sang VIEWING
        from app.infrastructure.database.repositories import SessionRepository
        sess_repo = SessionRepository(db)
        final_session = await sess_repo.get(session_id, tenant_id=tenant_1.id)
        assert final_session.lifecycle_state == LifecycleState.VIEWING.value
        
    print("[E2E] Success: Full user journey verified with Catalog V4 Integration")
