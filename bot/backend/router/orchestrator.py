"""
Router Orchestrator - Main routing decision system
"""
import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from ..schemas import RouterRequest, RouterResponse, RouterTrace, SessionState
from ..shared.exceptions import (
    RouterError,
    InvalidInputError,
    PatternMatchError,
    EmbeddingError,
    LLMError,
    RouterTimeoutError,
    ExternalServiceError,
)
from ..shared.logger import logger
from ..shared.config import config
from ..shared.tracing import get_tracer
from ..infrastructure.session_repository import RedisSessionRepository
from .conversation_state_machine import conversation_state_machine, ConversationState
from .slot_validator import slot_validator
from .steps import (
    SessionStep,
    NormalizeStep,
    MetaTaskStep,
    PatternMatchStep,
    KeywordHintStep,
    EmbeddingClassifierStep,
    LLMClassifierStep,
)
from .policies import get_threshold_policy, RoutingSource


class RouterOrchestrator:
    """
    Main router orchestrator that coordinates all routing steps.
    
    This class implements the routing decision pipeline:
    STEP 0: Session load/create
    STEP 0.5: Normalize input
    STEP 1: Meta-task detection
    STEP 2: Global pattern match
    STEP 3: Keyword hint
    STEP 4: Embedding classifier
    STEP 5: LLM classifier (fallback)
    STEP 6: UNKNOWN handling
    """
    
    def __init__(self):
        """Initialize router orchestrator with all steps"""
        self.session_step = SessionStep()
        self.normalize_step = NormalizeStep()
        self.meta_step = MetaTaskStep()
        self.pattern_step = PatternMatchStep()
        self.keyword_step = KeywordHintStep()
        self.embedding_step = EmbeddingClassifierStep()
        self.llm_step = LLMClassifierStep()
        self.tracer = get_tracer("router.orchestrator")
        self.threshold_policy = get_threshold_policy()
        self.session_repository = RedisSessionRepository()
    
    async def route(self, request: RouterRequest) -> RouterResponse:
        """
        Main routing method.
        
        Args:
            request: Router input request
            
        Returns:
            RouterResponse with routing decision
            
        Raises:
            RouterError: If routing fails
        """
        trace_id = str(uuid.uuid4())
        router_trace = RouterTrace(trace_id=trace_id)
        
        # Extract tenant_id from metadata if available
        tenant_id = None
        if request.metadata:
            tenant_id_str = request.metadata.get("tenant_id")
            if tenant_id_str:
                try:
                    tenant_id = uuid.UUID(tenant_id_str)
                except (ValueError, AttributeError):
                    pass
        
        # Create OpenTelemetry span for entire routing operation
        with self.tracer.start_as_current_span(
            "router.route",
            attributes={
                "router.trace_id": trace_id,
                "router.user_id": request.user_id,
                "router.session_id": request.session_id or "new",
                "router.message_length": len(request.raw_message),
                "router.tenant_id": str(tenant_id) if tenant_id else "none",
            }
        ) as span:
            try:
                logger.info(
                    "Router request received",
                    extra={
                        "trace_id": trace_id,
                        "user_id": request.user_id,
                        "session_id": request.session_id,
                        "message_length": len(request.raw_message),
                        "tenant_id": str(tenant_id) if tenant_id else None,
                    }
                )
            
                # STEP 0: Session load/create
                session_state = await self._step_0_session(request, router_trace, span)
                
                # Check escalation (F4.3)
                if session_state.escalation_flag:
                    span.set_attribute("router.escalation", True)
                    return self._build_escalation_response(trace_id, router_trace, session_state)
                
                # Check retry count for escalation
                if session_state.retry_count >= config.ESCALATION_RETRY_THRESHOLD:
                    logger.warning(
                        "Retry threshold exceeded, escalating to human",
                        extra={
                            "trace_id": trace_id,
                            "retry_count": session_state.retry_count,
                            "threshold": config.ESCALATION_RETRY_THRESHOLD,
                        }
                    )
                    session_state.escalation_flag = True
                    session_state.retry_count = 0  # Reset after escalation
                    await self.session_repository.save(session_state)
                    span.set_attribute("router.escalation", True)
                    return self._build_escalation_response(trace_id, router_trace, session_state)
                
                # Transition to ROUTING state (F3.2)
                if session_state.conversation_state == ConversationState.IDLE:
                    try:
                        session_state.conversation_state = conversation_state_machine.transition(
                            session_state.conversation_state,
                            ConversationState.ROUTING
                        )
                        await self.session_repository.save(session_state)
                    except ValueError:
                        # Invalid transition, log but continue
                        logger.warning(
                            f"Invalid state transition from {session_state.conversation_state.value} to ROUTING",
                            extra={"trace_id": trace_id}
                        )
                
                # STEP 0.5: Normalize input
                normalized = await self._step_0_5_normalize(request, session_state, router_trace, span)
                
                # STEP 0.6: Check continuation (if user is in active flow)
                continuation_result = await self._step_0_6_continuation(
                    normalized, session_state, router_trace, span
                )
                if continuation_result.get("continued"):
                    span.set_attribute("router.decision", "CONTINUATION")
                    span.set_attribute("router.domain", continuation_result.get("domain", "unknown"))
                    span.set_attribute("router.intent", continuation_result.get("intent", "unknown"))
                    return self._build_continuation_response(
                        trace_id, continuation_result, router_trace, session_state
                    )
                
                # STEP 1: Meta-task detection
                meta_result = await self._step_1_meta(normalized, session_state, router_trace, span)
                if meta_result.get("handled"):
                    span.set_attribute("router.decision", "META_HANDLED")
                    return self._build_meta_response(trace_id, meta_result, router_trace, session_state)
                
                # STEP 2-3: Parallel execution of Pattern and Keyword (independent steps)
                # Pattern and Keyword can run in parallel since they're independent
                pattern_result, boost = await self._execute_pattern_and_keyword_parallel(
                    normalized, router_trace, tenant_id, span
                )
                
                # Boost based on session context (F3.3)
                boost = self._apply_session_context_boost(boost, session_state)
                
                # Check pattern match first (highest priority)
                if pattern_result.get("matched"):
                    span.set_attribute("router.decision", "PATTERN")
                    span.set_attribute("router.domain", pattern_result.get("domain", "unknown"))
                    span.set_attribute("router.intent", pattern_result.get("intent", "unknown"))
                    # Validate and merge slots into session and persist
                    await self._merge_slots_and_persist(
                        session_state,
                        pattern_result.get("slots", {}),
                        pattern_result.get("intent")
                    )
                    return self._build_routed_response(trace_id, pattern_result, router_trace, session_state)
                
                # STEP 4: Embedding classifier (runs after we have boost from Keyword)
                embedding_result = await self._step_4_embedding(normalized, boost, router_trace, span)
                if embedding_result.get("classified"):
                    confidence = embedding_result.get("confidence", 0)
                    # Use ThresholdPolicy to decide
                    if self.threshold_policy.should_route(RoutingSource.EMBEDDING, confidence):
                        span.set_attribute("router.decision", "EMBEDDING")
                        span.set_attribute("router.domain", embedding_result.get("domain", "unknown"))
                        span.set_attribute("router.intent", embedding_result.get("intent", "unknown"))
                        span.set_attribute("router.confidence", confidence)
                        # Validate and merge slots into session and persist
                        await self._merge_slots_and_persist(
                            session_state,
                            embedding_result.get("slots", {}),
                            embedding_result.get("intent")
                        )
                        return self._build_routed_response(trace_id, embedding_result, router_trace, session_state)
                
                # STEP 5: LLM classifier (fallback)
                if config.ENABLE_LLM_FALLBACK:
                    llm_result = await self._step_5_llm(normalized, session_state, router_trace, span)
                    if llm_result.get("classified"):
                        confidence = llm_result.get("confidence", 0)
                        # Use ThresholdPolicy to decide
                        if self.threshold_policy.should_route(RoutingSource.LLM, confidence):
                            span.set_attribute("router.decision", "LLM")
                            span.set_attribute("router.domain", llm_result.get("domain", "unknown"))
                            span.set_attribute("router.intent", llm_result.get("intent", "unknown"))
                            span.set_attribute("router.confidence", confidence)
                            # Validate and merge slots into session and persist
                            await self._merge_slots_and_persist(
                                session_state,
                                llm_result.get("slots", {}),
                                llm_result.get("intent")
                            )
                            return self._build_routed_response(trace_id, llm_result, router_trace, session_state)
                
                # STEP 6: UNKNOWN
                span.set_attribute("router.decision", "UNKNOWN")
                return self._build_unknown_response(trace_id, router_trace, session_state)
                
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("router.error", True)
                span.set_attribute("router.error_type", type(e).__name__)
                logger.error(
                    f"Router error: {e}",
                    extra={"trace_id": trace_id},
                    exc_info=True
                )
                raise RouterError(f"Routing failed: {e}") from e
    
    async def _step_0_session(
        self,
        request: RouterRequest,
        trace: RouterTrace,
        parent_span
    ) -> SessionState:
        """STEP 0: Session load/create"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.session",
            attributes={
                "step.name": "session",
                "step.user_id": request.user_id,
            }
        ) as step_span:
            try:
                session_state = await self.session_step.execute(request)
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.session_id", session_state.session_id)
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.session",
                    {"user_id": request.user_id, "session_id": request.session_id},
                    {"session_id": session_state.session_id},
                    duration_ms
                )
                
                return session_state
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                logger.error(f"Session step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
                raise
    
    async def _step_0_5_normalize(
        self,
        request: RouterRequest,
        session_state: SessionState,
        trace: RouterTrace,
        parent_span
    ):
        """STEP 0.5: Normalize input"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.normalize",
            attributes={
                "step.name": "normalize",
                "step.message_length": len(request.raw_message),
            }
        ) as step_span:
            try:
                normalized = await self.normalize_step.execute(
                    request.raw_message,
                    session_state
                )
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.normalized_length", len(normalized.normalized_message))
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.normalize",
                    {"raw_message": request.raw_message[:100]},
                    {"normalized_message": normalized.normalized_message[:100]},
                    duration_ms
                )
                
                return normalized
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                logger.error(f"Normalize step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
                raise
    
    async def _step_1_meta(self, normalized, session_state, trace, parent_span=None):
        """STEP 1: Meta-task detection"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.meta",
            attributes={
                "step.name": "meta",
            }
        ) as step_span:
            try:
                result = await self.meta_step.execute(normalized, session_state)
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.handled", result.get("handled", False))
                if result.get("handled"):
                    step_span.set_attribute("step.meta_type", result.get("type", "unknown"))
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.meta",
                    {"normalized_message": normalized.normalized_message[:100]},
                    result,
                    duration_ms
                )
                
                return result
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                logger.error(f"Meta step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
                return {"handled": False}
    
    async def _step_2_pattern(self, normalized, trace, tenant_id: Optional[uuid.UUID] = None, parent_span=None):
        """STEP 2: Global pattern match"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.pattern",
            attributes={
                "step.name": "pattern",
                "step.tenant_id": str(tenant_id) if tenant_id else "none",
            }
        ) as step_span:
            try:
                result = await self.pattern_step.execute(normalized.normalized_message, tenant_id)
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.matched", result.get("matched", False))
                if result.get("matched"):
                    step_span.set_attribute("step.domain", result.get("domain", "unknown"))
                    step_span.set_attribute("step.intent", result.get("intent", "unknown"))
                    step_span.set_attribute("step.confidence", result.get("confidence", 0))
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.pattern",
                    {"normalized_message": normalized.normalized_message[:100]},
                    result,
                    duration_ms,
                    score=result.get("confidence"),
                    decision_source="PATTERN" if result.get("matched") else None
                )
                
                return result
            except (PatternMatchError, ExternalServiceError) as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                step_span.set_attribute("step.error_type", type(e).__name__)
                # Log full stack trace for actual errors
                logger.error(
                    f"Pattern step error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                        "user_message": normalized.normalized_message[:100],
                    },
                    exc_info=True
                )
                # Return empty result but error is logged with full context
                return {"matched": False, "error": str(e)}
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", "unexpected_error")
                # Unexpected error - log with full stack trace
                logger.error(
                    f"Pattern step unexpected error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                    },
                    exc_info=True
                )
                return {"matched": False, "error": "unexpected_error"}
    
    async def _step_3_keyword(self, normalized, trace, tenant_id: Optional[uuid.UUID] = None, parent_span=None):
        """STEP 3: Keyword hint"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.keyword",
            attributes={
                "step.name": "keyword",
                "step.tenant_id": str(tenant_id) if tenant_id else "none",
            }
        ) as step_span:
            try:
                result = await self.keyword_step.execute(normalized.normalized_message, tenant_id)
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                boost_count = len(result.get("boost", {}))
                step_span.set_attribute("step.boost_domains", boost_count)
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.keyword",
                    {"normalized_message": normalized.normalized_message[:100]},
                    result,
                    duration_ms
                )
                
                return result.get("boost", {})
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                logger.error(f"Keyword step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
                return {}
    
    async def _step_4_embedding(self, normalized, boost, trace, parent_span=None):
        """STEP 4: Embedding classifier"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.embedding",
            attributes={
                "step.name": "embedding",
                "step.boost_domains": len(boost),
            }
        ) as step_span:
            try:
                result = await self.embedding_step.execute(
                    normalized.normalized_message,
                    boost
                )
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.classified", result.get("classified", False))
                if result.get("classified"):
                    step_span.set_attribute("step.domain", result.get("domain", "unknown"))
                    step_span.set_attribute("step.intent", result.get("intent", "unknown"))
                    step_span.set_attribute("step.confidence", result.get("confidence", 0))
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.embedding",
                    {"normalized_message": normalized.normalized_message[:100], "boost": boost},
                    result,
                    duration_ms,
                    score=result.get("confidence"),
                    decision_source="EMBEDDING" if result.get("classified") else None
                )
                
                return result
            except (EmbeddingError, RouterTimeoutError, ExternalServiceError) as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                step_span.set_attribute("step.error_type", type(e).__name__)
                # Log full stack trace for actual errors
                logger.error(
                    f"Embedding step error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                        "user_message": normalized.normalized_message[:100],
                        "boost": boost,
                    },
                    exc_info=True
                )
                # Return empty result but error is logged with full context
                return {"classified": False, "error": str(e), "reason": "step_error"}
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", "unexpected_error")
                # Unexpected error - log with full stack trace
                logger.error(
                    f"Embedding step unexpected error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                    },
                    exc_info=True
                )
                return {"classified": False, "error": "unexpected_error"}
    
    async def _step_5_llm(self, normalized, session_state, trace, parent_span=None):
        """STEP 5: LLM classifier"""
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.llm",
            attributes={
                "step.name": "llm",
            }
        ) as step_span:
            try:
                result = await self.llm_step.execute(
                    normalized.normalized_message,
                    session_state
                )
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.classified", result.get("classified", False))
                if result.get("classified"):
                    step_span.set_attribute("step.domain", result.get("domain", "unknown"))
                    step_span.set_attribute("step.intent", result.get("intent", "unknown"))
                    step_span.set_attribute("step.confidence", result.get("confidence", 0))
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.llm",
                    {"normalized_message": normalized.normalized_message[:100]},
                    result,
                    duration_ms,
                    score=result.get("confidence"),
                    decision_source="LLM" if result.get("classified") else None
                )
                
                return result
            except (LLMError, RouterTimeoutError, ExternalServiceError) as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                step_span.set_attribute("step.error_type", type(e).__name__)
                # Log full stack trace for actual errors
                logger.error(
                    f"LLM step error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                        "user_message": normalized.normalized_message[:100],
                    },
                    exc_info=True
                )
                # Return empty result but error is logged with full context
                return {"classified": False, "error": str(e), "reason": "step_error"}
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", "unexpected_error")
                # Unexpected error - log with full stack trace
                logger.error(
                    f"LLM step unexpected error: {e}",
                    extra={
                        "trace_id": trace.trace_id,
                        "error_type": type(e).__name__,
                    },
                    exc_info=True
                )
                return {"classified": False, "error": "unexpected_error"}
    
    def _build_meta_response(
        self,
        trace_id: str,
        meta_result: dict,
        trace: RouterTrace,
        session_state: SessionState
    ) -> RouterResponse:
        """Build response for meta-handled request"""
        return RouterResponse(
            trace_id=trace_id,
            session_id=session_state.session_id,
            status="META_HANDLED",
            source="META",
            message=meta_result.get("response"),
            trace=trace,
        )
    
    def _build_routed_response(
        self,
        trace_id: str,
        result: dict,
        trace: RouterTrace,
        session_state: SessionState
    ) -> RouterResponse:
        """Build response for routed request"""
        return RouterResponse(
            trace_id=trace_id,
            session_id=session_state.session_id,
            domain=result.get("domain"),
            intent=result.get("intent"),
            intent_type=result.get("intent_type"),
            slots=result.get("slots", {}),
            confidence=result.get("confidence"),
            source=result.get("source", "UNKNOWN"),
            status="ROUTED",
            trace=trace,
        )
    
    def _build_escalation_response(
        self,
        trace_id: str,
        trace: RouterTrace,
        session_state: SessionState
    ) -> RouterResponse:
        """
        Build escalation response when retry threshold is exceeded (F4.3).
        
        Args:
            trace_id: Trace ID
            trace: Router trace
            session_state: Current session state
            
        Returns:
            RouterResponse with escalation message
        """
        return RouterResponse(
            trace_id=trace_id,
            session_id=session_state.session_id,
            status="UNKNOWN",  # Use UNKNOWN status for escalation
            source="ESCALATION",
            message="Xin lỗi, tôi gặp khó khăn trong việc hiểu yêu cầu của bạn. Vui lòng liên hệ với nhân viên hỗ trợ để được giúp đỡ.",
            trace=trace,
        )
    
    def _build_unknown_response(
        self,
        trace_id: str,
        trace: RouterTrace,
        session_state: SessionState
    ) -> RouterResponse:
        """Build response for unknown request with recovery path"""
        # Check if we have last_domain to suggest resume
        if session_state.last_domain:
            message = f"Bạn muốn tiếp tục với {session_state.last_domain.upper()} hay chuyển sang domain khác?"
            options = [session_state.last_domain, "Khác"]
        else:
            message = "Bạn muốn hỏi về domain nào? Vui lòng chọn một trong các lựa chọn sau:"
            options = ["HR", "Catalog", "DBA"]
        
        return RouterResponse(
            trace_id=trace_id,
            session_id=session_state.session_id,
            status="UNKNOWN",
            source="UNKNOWN",
            message=message,
            trace=trace,
            options=options,
        )
    
    async def _step_0_6_continuation(
        self,
        normalized,
        session_state: SessionState,
        trace: RouterTrace,
        parent_span
    ) -> Dict[str, Any]:
        """
        STEP 0.6: Check if user is continuing an active flow.
        
        If user has pending_intent and active_domain, check if message is a slot value.
        If yes, route directly to active_domain with pending_intent.
        
        Args:
            normalized: Normalized input
            session_state: Current session state
            trace: Router trace
            parent_span: Parent OpenTelemetry span
            
        Returns:
            Dict with "continued" flag and routing info if continued
        """
        start_time = datetime.utcnow()
        
        with self.tracer.start_as_current_span(
            "router.step.continuation",
            attributes={
                "step.name": "continuation",
                "step.has_pending_intent": bool(session_state.pending_intent),
                "step.has_active_domain": bool(session_state.active_domain),
            }
        ) as step_span:
            try:
                # Check if user is in active flow
                if not session_state.pending_intent or not session_state.active_domain:
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    step_span.set_attribute("step.duration_ms", duration_ms)
                    step_span.set_attribute("step.continued", False)
                    step_span.set_attribute("step.success", True)
                    
                    trace.add_span(
                        "router.step.continuation",
                        {"has_pending_intent": bool(session_state.pending_intent)},
                        {"continued": False},
                        duration_ms
                    )
                    return {"continued": False}
                
                # Check if message looks like a slot value
                is_slot_value = self._is_slot_value(
                    normalized.normalized_message,
                    session_state.missing_slots,
                    normalized.normalized_entities
                )
                
                if is_slot_value:
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    step_span.set_attribute("step.duration_ms", duration_ms)
                    step_span.set_attribute("step.continued", True)
                    step_span.set_attribute("step.domain", session_state.active_domain)
                    step_span.set_attribute("step.intent", session_state.pending_intent)
                    step_span.set_attribute("step.success", True)
                    
                    result = {
                        "continued": True,
                        "domain": session_state.active_domain,
                        "intent": session_state.pending_intent,
                        "intent_type": session_state.last_intent_type or "OPERATION",
                        "slots": self._extract_slots_from_message(
                            normalized.normalized_message,
                            session_state.missing_slots,
                            normalized.normalized_entities
                        ),
                        "source": "CONTINUATION",
                        "confidence": 1.0,
                    }
                    
                    trace.add_span(
                        "router.step.continuation",
                        {
                            "pending_intent": session_state.pending_intent,
                            "missing_slots": session_state.missing_slots,
                        },
                        result,
                        duration_ms
                    )
                    
                    logger.info(
                        "Continuation detected",
                        extra={
                            "trace_id": trace.trace_id,
                            "domain": session_state.active_domain,
                            "intent": session_state.pending_intent,
                            "missing_slots": session_state.missing_slots,
                        }
                    )
                    
                    return result
                
                # Not a slot value, continue normal routing
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                step_span.set_attribute("step.duration_ms", duration_ms)
                step_span.set_attribute("step.continued", False)
                step_span.set_attribute("step.success", True)
                
                trace.add_span(
                    "router.step.continuation",
                    {"pending_intent": session_state.pending_intent},
                    {"continued": False, "reason": "not_slot_value"},
                    duration_ms
                )
                
                return {"continued": False}
                
            except Exception as e:
                step_span.record_exception(e)
                step_span.set_attribute("step.success", False)
                step_span.set_attribute("step.error", str(e))
                logger.error(
                    f"Continuation step failed: {e}",
                    extra={"trace_id": trace.trace_id},
                    exc_info=True
                )
                # Don't raise - continue normal routing on error
                return {"continued": False}
    
    def _is_slot_value(
        self,
        message: str,
        missing_slots: list[str],
        normalized_entities: Dict[str, Any]
    ) -> bool:
        """
        Check if message looks like a slot value.
        
        Heuristics:
        - Short message (< 50 chars) suggests slot value
        - Contains date entity (from normalized_entities)
        - Contains number entity
        - Single word or short phrase
        
        Args:
            message: Normalized message
            missing_slots: List of missing slot names
            normalized_entities: Entities extracted during normalization
            
        Returns:
            True if message looks like a slot value
        """
        message = message.strip()
        
        # Very short messages are likely slot values
        if len(message) < 50:
            # Check if contains date entity
            if normalized_entities.get("dates"):
                return True
            
            # Check if contains number entity
            if normalized_entities.get("numbers"):
                return True
            
            # Check if it's a single word or short phrase (likely slot value)
            words = message.split()
            if len(words) <= 3:
                # Exclude common meta words
                meta_words = ["help", "giúp", "cancel", "hủy", "reset", "bắt đầu lại"]
                if message.lower() not in meta_words:
                    return True
        
        return False
    
    def _extract_slots_from_message(
        self,
        message: str,
        missing_slots: list[str],
        normalized_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract slot values from message for continuation.
        
        Args:
            message: Normalized message
            missing_slots: List of missing slot names
            normalized_entities: Entities extracted during normalization
            
        Returns:
            Dict of slot_name -> value
        """
        slots = {}
        
        # Extract date slots
        if normalized_entities.get("dates") and missing_slots:
            date_entities = normalized_entities["dates"]
            # Try to match date slots
            for slot_name in missing_slots:
                if any(keyword in slot_name.lower() for keyword in ["date", "ngày", "time", "thời"]):
                    if date_entities:
                        # Use first date entity
                        slots[slot_name] = date_entities[0].get("value")
                        break
        
        # Extract number slots
        if normalized_entities.get("numbers") and missing_slots:
            number_entities = normalized_entities["numbers"]
            # Try to match number slots
            for slot_name in missing_slots:
                if any(keyword in slot_name.lower() for keyword in ["number", "số", "count", "số lượng", "amount", "số tiền"]):
                    if number_entities:
                        # Use first number entity
                        slots[slot_name] = number_entities[0].get("value")
                        break
        
        # If no entity match, try to match first missing slot with message
        if not slots and missing_slots:
            # For simple cases, assign message to first missing slot
            # This is a best-effort approach
            first_missing = missing_slots[0]
            if len(message.split()) <= 3:  # Short message
                slots[first_missing] = message
        
        return slots
    
    async def _build_continuation_response(
        self,
        trace_id: str,
        continuation_result: dict,
        trace: RouterTrace,
        session_state: SessionState
    ) -> RouterResponse:
        """Build response for continuation request"""
        # Validate and merge slots into session before returning
        slots = continuation_result.get("slots", {})
        if slots:
            await self._merge_slots_and_persist(
                session_state,
                slots,
                continuation_result.get("intent")
            )
        
        return RouterResponse(
            trace_id=trace_id,
            session_id=session_state.session_id,
            domain=continuation_result.get("domain"),
            intent=continuation_result.get("intent"),
            intent_type=continuation_result.get("intent_type"),
            slots=slots,
            confidence=continuation_result.get("confidence", 1.0),
            source=continuation_result.get("source", "CONTINUATION"),
            status="ROUTED",
            trace=trace,
        )
    
    def _apply_session_context_boost(
        self,
        boost: Dict[str, float],
        session_state: SessionState
    ) -> Dict[str, float]:
        """
        Apply session context boost to routing.
        
        This implements F3.3: Router Sử Dụng Session Context.
        If user has last_domain, boost that domain's confidence.
        
        Args:
            boost: Current boost scores from keyword step
            session_state: Current session state
            
        Returns:
            Updated boost scores with session context
        """
        if not session_state.last_domain:
            return boost
        
        # Boost last_domain by 0.1 (10% confidence boost)
        # This makes router more likely to route to same domain
        boost = boost.copy()
        current_boost = boost.get(session_state.last_domain, 0.0)
        boost[session_state.last_domain] = current_boost + 0.1
        
        logger.debug(
            "Applied session context boost",
            extra={
                "last_domain": session_state.last_domain,
                "boost_value": boost.get(session_state.last_domain),
            }
        )
        
        return boost
    
    def _validate_slots(
        self,
        slots: Dict[str, Any],
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate slot formats at router level (F4.1).
        
        Args:
            slots: Slots to validate
            intent: Optional intent name for context
            
        Returns:
            Validated slots dict
            
        Raises:
            InvalidInputError: If slot format is invalid
        """
        if not slots:
            return {}
        
        try:
            validated_slots = slot_validator.validate_slots(slots)
            logger.debug(
                "Slots validated at router level",
                extra={
                    "intent": intent,
                    "slots_count": len(validated_slots),
                }
            )
            return validated_slots
        except InvalidInputError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(
                f"Slot validation error: {e}",
                extra={"intent": intent},
                exc_info=True
            )
            # Return original slots on unexpected error (don't block routing)
            return slots
    
    async def _merge_slots_and_persist(
        self,
        session_state: SessionState,
        new_slots: Dict[str, Any],
        intent: Optional[str] = None
    ) -> None:
        """
        Merge new slots into session memory and persist.
        
        Args:
            session_state: Current session state
            new_slots: New slots to merge
            intent: Optional intent name for validation context
        """
        if not new_slots:
            return
        
        try:
            # Validate slots before merging (F4.1)
            validated_slots = self._validate_slots(new_slots, intent)
            
            # Merge validated slots into session memory
            session_state.merge_slots(validated_slots)
            
            # Persist session
            await self.session_repository.save(session_state)
            
            logger.debug(
                "Slots validated, merged and session persisted",
                extra={
                    "session_id": session_state.session_id,
                    "slots_count": len(validated_slots),
                    "total_slots": len(session_state.slots_memory),
                }
            )
        except InvalidInputError as e:
            logger.warning(
                f"Slot validation failed, skipping merge: {e}",
                extra={"session_id": session_state.session_id, "intent": intent}
            )
            # Don't merge invalid slots, but don't block routing
        except Exception as e:
            logger.error(
                f"Failed to merge slots and persist session: {e}",
                extra={"session_id": session_state.session_id},
                exc_info=True
            )
            # Don't raise - this is not critical for routing
    
    async def _execute_pattern_and_keyword_parallel(
        self,
        normalized,
        trace: RouterTrace,
        tenant_id: Optional[uuid.UUID],
        parent_span
    ) -> tuple[Dict[str, Any], Dict[str, float]]:
        """
        Execute Pattern and Keyword steps in parallel.
        
        These steps are independent and can run concurrently to reduce latency.
        
        Args:
            normalized: Normalized input
            trace: Router trace
            tenant_id: Optional tenant ID
            parent_span: Parent OpenTelemetry span
            
        Returns:
            Tuple of (pattern_result, boost)
        """
        try:
            # Execute Pattern and Keyword in parallel
            pattern_task = self._step_2_pattern(normalized, trace, tenant_id, parent_span)
            keyword_task = self._step_3_keyword(normalized, trace, tenant_id, parent_span)
            
            # Wait for both to complete with timeout
            # Use max timeout between the two steps
            max_timeout = max(
                config.STEP_PATTERN_TIMEOUT,
                config.STEP_KEYWORD_TIMEOUT
            ) / 1000.0  # Convert to seconds
            
            pattern_result, keyword_result = await asyncio.wait_for(
                asyncio.gather(
                    pattern_task,
                    keyword_task,
                    return_exceptions=True
                ),
                timeout=max_timeout
            )
            
            # Extract boost from keyword result
            if isinstance(keyword_result, dict):
                boost = keyword_result.get("boost", {})
            elif isinstance(keyword_result, Exception):
                logger.error(
                    f"Keyword step exception in parallel execution: {keyword_result}",
                    exc_info=True
                )
                boost = {}
            else:
                boost = {}
            
            # Handle pattern result exceptions
            if isinstance(pattern_result, Exception):
                logger.error(
                    f"Pattern step exception in parallel execution: {pattern_result}",
                    exc_info=True
                )
                pattern_result = {"matched": False, "error": str(pattern_result)}
            
            logger.debug(
                "Parallel steps completed",
                extra={
                    "trace_id": trace.trace_id,
                    "pattern_matched": pattern_result.get("matched", False),
                    "boost_domains": len(boost),
                }
            )
            
            return pattern_result, boost
            
        except asyncio.TimeoutError:
            logger.error(
                "Parallel steps execution timeout",
                extra={"trace_id": trace.trace_id}
            )
            # Return safe defaults
            return (
                {"matched": False, "error": "timeout"},
                {}
            )
        except Exception as e:
            logger.error(
                f"Error in parallel steps execution: {e}",
                extra={"trace_id": trace.trace_id},
                exc_info=True
            )
            # Return safe defaults
            return (
                {"matched": False, "error": str(e)},
                {}
            )

