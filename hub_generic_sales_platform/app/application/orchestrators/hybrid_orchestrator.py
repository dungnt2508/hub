import re
import time
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import traceback

from app.application.orchestrators.agent_orchestrator import AgentOrchestrator
from app.application.services.session_service import SessionService
from app.core.shared.db_utils import transaction_scope
from app.application.services.semantic_cache_service import SemanticCacheService
from app.infrastructure.database.repositories import FAQRepository
from app.infrastructure.database.repositories import DecisionRepository
from app.infrastructure.database.engine import get_session_maker
from app.core import domain
from app.infrastructure.llm.factory import get_llm_provider
from app.core.config.settings import get_settings
from app.application.services.session_state import SessionStateHandler


class HybridOrchestrator:
    """
    Hybrid Orchestrator (Refactored for SRP & Performance)
    
    Phân tầng xử lý thông minh: Fast Path -> Knowledge Path -> Agentic Path.
    Tối ưu hóa độ trễ bằng BackgroundTasks và tách biệt logic quản lý phiên.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.agent_orchestrator = AgentOrchestrator(db)
        self.session_service = SessionService(db)
        self.session_state_handler = SessionStateHandler(db)
        
        self.semantic_cache_service = SemanticCacheService(db)
        self.faq_repo = FAQRepository(db)
        self.decision_repo = DecisionRepository(db)
        self.logger = logging.getLogger(__name__)

    async def handle_message(
        self, 
        tenant_id: str, 
        bot_id: str, 
        message: str, 
        session_id: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
        channel_code: str = "webchat",
        ext_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """EntryPoint điều phối 3 tầng xử lý.
        ext_metadata: Channel-specific user mapping (zalo_user_id, messenger_id, ...) for runtime_session."""
        try:
            start_time = time.time()
        
            # 1. Quản lý Session (map external user → runtime_session via ext_metadata)
            session_data = await self.session_service.get_or_create_session(
                tenant_id, bot_id, session_id, channel_code=channel_code, ext_metadata=ext_metadata
            )
            session_id = session_data["session_id"]
            bot_version_id = session_data["bot_version_id"]
            
            # Retrieve session object for state routing
            session_obj = await self.session_state_handler.read_session_state(session_id, tenant_id)
            
            # --- STATE DISPATCHING & TIER PROCESSING ---
            current_state = session_obj.lifecycle_state if session_obj else "idle"
            if not current_state:
                current_state = "idle"

            # --- HANDOVER: Human agent reply (no LLM) ---
            if session_obj and session_obj.is_handover_mode():
                async with transaction_scope(self.db):
                    await self.session_service.log_bot_response(session_id, message)
                    return await self._finalize_response(
                        session_id, bot_version_id, message, "handover",
                        decision_type=domain.DecisionType.PROCEED,
                        cost=0.0,
                        start_time=start_time,
                        reason="Human agent reply (handover mode)",
                        background_tasks=background_tasks
                    )

            # --- TIER 1: FAST PATH (Cost: $0) ---
            if current_state not in ["purchasing"]:
                social_response = self._check_social_patterns(message)
                if social_response:
                    async with transaction_scope(self.db):
                        await self.session_service.log_user_message(session_id, message)
                        return await self._finalize_response(
                            session_id, bot_version_id, social_response, "fast_path", 
                            decision_type=domain.DecisionType.PROCEED, 
                            cost=self.settings.cost_fast_path, 
                            start_time=start_time,
                            reason=f"Pattern matched in Fast Path (State: {current_state})",
                            background_tasks=background_tasks
                        )

            # --- TIER 2: KNOWLEDGE PATH (Cost: Mini) ---
            # State-driven: Skip Tier 2 khi user đang trong flow bán hàng (tiết kiệm ~50-100ms + $0.0001)
            SKIP_TIER2_STATES = {"viewing", "comparing", "purchasing", "searching"}
            current_state_lower = (current_state or "").lower()
            skip_tier2 = current_state_lower in SKIP_TIER2_STATES

            if not skip_tier2:
                llm = get_llm_provider()
                query_vector = await llm.get_embedding(message)
                msg_lower = message.lower().strip()
                
                # Check Semantic Cache via Service
                threshold_cache = self.settings.semantic_cache_threshold
                cached = await self.semantic_cache_service.find_match(
                    tenant_id=tenant_id,
                    message=message,
                    query_vector=query_vector,
                    threshold=threshold_cache
                )
                
                if cached:
                    async with transaction_scope(self.db):
                        await self.session_service.log_user_message(session_id, message)
                        if background_tasks:
                            background_tasks.add_task(self.semantic_cache_service.track_hit, cached.id)
                        else:
                            await self.semantic_cache_service.track_hit(cached.id)
                            
                        return await self._finalize_response(
                            session_id, bot_version_id, cached.response_text, "knowledge_path", 
                            decision_type=domain.DecisionType.PROCEED, 
                            cost=self.settings.cost_knowledge_base, 
                            start_time=start_time,
                            reason=f"Semantic Cache hit (threshold={threshold_cache}, State: {current_state})",
                            background_tasks=background_tasks
                        )

                # Check FAQ
                if current_state_lower in ["idle", "browsing"]:
                    if query_vector:
                        threshold_faq = 0.85 
                        semantic_faqs = await self.faq_repo.semantic_search(tenant_id, query_vector, threshold=threshold_faq, bot_id=bot_id)
                        if semantic_faqs:
                            best_faq, similarity = semantic_faqs[0]
                            async with transaction_scope(self.db):
                                await self.session_service.log_user_message(session_id, message)
                                return await self._finalize_response(
                                    session_id, bot_version_id, best_faq.answer, "knowledge_path", 
                                    decision_type=domain.DecisionType.PROCEED, 
                                    cost=self.settings.cost_knowledge_base, 
                                    start_time=start_time,
                                    reason=f"FAQ semantic match (similarity={similarity:.4f}, State: {current_state})",
                                    background_tasks=background_tasks
                                )

            # --- TIER 3: AGENTIC PATH (Cost: High) ---
            # Agent reasoning now constrained by State
            agent_result = await self.agent_orchestrator.run(message, session_id, current_state, tenant_id)
            bot_response = agent_result.get("response", "Xin lỗi, tôi gặp sự cố khi xử lý.")
            usage = agent_result.get("usage")
            g_ui_data = agent_result.get("g_ui_data")
            new_state = agent_result.get("new_state")

            # Update State if recommended by Agent (and validated by logic)
            async with transaction_scope(self.db):
                if new_state:
                    # Handle both Enum and string
                    target_state = new_state if isinstance(new_state, domain.LifecycleState) else domain.LifecycleState(new_state)
                    if target_state != current_state:
                        try:
                            if background_tasks:
                                # Define wrapper to catch background errors
                                async def _safe_update_state(handler, sid, state, tid):
                                    try:
                                        await handler.update_lifecycle_state(sid, state, tid)
                                    except ValueError as e:
                                        logging.getLogger(__name__).warning(f"Invalid state transition requested by Agent: {str(e)}")
                                        
                                background_tasks.add_task(_safe_update_state, self.session_state_handler, session_id, target_state, tenant_id)
                            else:
                                await self.session_state_handler.update_lifecycle_state(session_id, target_state, tenant_id)
                        except ValueError as e:
                            self.logger.warning(f"Invalid state transition requested by Agent (Sync): {str(e)}")
                            # Continue processing, just don't update state
                
                if usage and usage.get("total_tokens"):
                    estimated_cost = self.settings.cost_agentic_base + (usage["total_tokens"] / 1000.0 * 0.01)
                else:
                    estimated_cost = self.settings.cost_agentic_base + (len(message) * self.settings.cost_agentic_per_char)
                
                return await self._finalize_response(
                    session_id, bot_version_id, bot_response, "agentic_path", 
                    decision_type=domain.DecisionType.PROCEED, 
                    cost=estimated_cost, 
                    start_time=start_time,
                    usage=usage,
                    reason=f"Processed via Agentic Reasoner (End State: {new_state or current_state})",
                    g_ui_data=g_ui_data,
                    background_tasks=background_tasks,
                    skip_turns=True,
                    tenant_id=tenant_id,
                    user_message=message
                )
        except Exception as e:
            self.logger.error(f"Error in HybridOrchestrator.handle_message: {str(e)}")
            self.logger.error(traceback.format_exc())
            # Re-raise to let API handler catch it or return a safer error response
            raise e

    async def _cache_agentic_response(
        self, tenant_id: str, user_message: str, response: str
    ) -> None:
        """Ghi response Agentic vào semantic cache (background, tạo session riêng vì request session đã đóng)."""
        try:
            session_maker = get_session_maker()
            async with session_maker() as db:
                svc = SemanticCacheService(db)
                await svc.create_entry(
                    tenant_id=tenant_id,
                    query_text=user_message,
                    response_text=response,
                )
                await db.commit()
        except Exception as e:
            self.logger.debug(f"Auto-cache skip: {e}")

    def _check_social_patterns(self, message: str) -> Optional[str]:
        """Kiểm tra các mẫu câu xã giao từ cấu hình"""
        msg_lower = message.lower().strip()
        for pattern, response in self.settings.social_patterns.items():
            if re.search(pattern, msg_lower):
                return response
        return None

    async def _finalize_response(
        self, 
        session_id: str,
        bot_version_id: str,
        response: str, 
        tier: str, 
        decision_type: Any,
        cost: float,
        start_time: float,
        reason: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None,
        g_ui_data: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None,
        skip_turns: bool = False,
        tenant_id: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tối ưu hóa phản hồi - Chuyển việc ghi log sang background task"""
        try:
            latency = int((time.time() - start_time) * 1000)
        
            # Build metadata
            metadata: Dict[str, Any] = {
                "tier": tier,
                "cost": f"${cost:.5f}",
                "latency_ms": latency,
                "usage": usage
            }
            
            # Add generative UI metadata if available
            if g_ui_data:
                metadata["g_ui"] = g_ui_data
            
            # Payload trả về ngay
            payload = {
                "response": response,
                "session_id": session_id,
                "metadata": metadata
            }
            
            # Chuẩn bị dữ liệu log
            log_data = {
                "session_id": session_id,
                "bot_version_id": bot_version_id,
                "decision_type": decision_type.value if hasattr(decision_type, 'value') else str(decision_type),
                "tier_code": tier,
                "estimated_cost": cost,
                "latency_ms": latency,
                "decision_reason": reason or f"Processed via {tier}",
                "token_usage": usage
            }

            # Ghi log Turn + Decision (Async/Background)
            if not skip_turns:
                if background_tasks:
                    background_tasks.add_task(self.session_service.log_bot_response, session_id, response)
                else:
                    await self.session_service.log_bot_response(session_id, response)
            
            if background_tasks:
                background_tasks.add_task(self.decision_repo.create, log_data)
            else:
                await self.decision_repo.create(log_data)

            # Prometheus: record tier distribution
            try:
                from app.infrastructure.metrics import record_decision_tier
                record_decision_tier(tier)
            except Exception:
                pass
            
            # Auto-write semantic cache: Agentic response tốt → cache cho lần sau
            if tier == "agentic_path" and tenant_id and user_message and len(response.strip()) > 30:
                if not any(x in response.lower() for x in ["lỗi", "xin lỗi", "không thể", "sự cố"]):
                    if background_tasks:
                        background_tasks.add_task(
                            self._cache_agentic_response, tenant_id, user_message, response
                        )
                    else:
                        await self._cache_agentic_response(tenant_id, user_message, response)
            
            return payload
        except Exception as e:
            self.logger.error(f"Error in HybridOrchestrator._finalize_response: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e
