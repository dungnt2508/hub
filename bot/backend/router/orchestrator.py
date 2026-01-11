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
                
                # STEP 0.5: Normalize input
                normalized = await self._step_0_5_normalize(request, session_state, router_trace, span)
                
                # STEP 1: Meta-task detection
                meta_result = await self._step_1_meta(normalized, session_state, router_trace, span)
                if meta_result.get("handled"):
                    span.set_attribute("router.decision", "META_HANDLED")
                    return self._build_meta_response(trace_id, meta_result, router_trace)
                
                # STEP 2-3: Parallel execution of Pattern and Keyword (independent steps)
                # Pattern and Keyword can run in parallel since they're independent
                pattern_result, boost = await self._execute_pattern_and_keyword_parallel(
                    normalized, router_trace, tenant_id, span
                )
                
                # Check pattern match first (highest priority)
                if pattern_result.get("matched"):
                    span.set_attribute("router.decision", "PATTERN")
                    span.set_attribute("router.domain", pattern_result.get("domain", "unknown"))
                    span.set_attribute("router.intent", pattern_result.get("intent", "unknown"))
                    return self._build_routed_response(trace_id, pattern_result, router_trace)
                
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
                        return self._build_routed_response(trace_id, embedding_result, router_trace)
                
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
                            return self._build_routed_response(trace_id, llm_result, router_trace)
                
                # STEP 6: UNKNOWN
                span.set_attribute("router.decision", "UNKNOWN")
                return self._build_unknown_response(trace_id, router_trace)
                
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
        trace: RouterTrace
    ) -> RouterResponse:
        """Build response for meta-handled request"""
        return RouterResponse(
            trace_id=trace_id,
            status="META_HANDLED",
            source="META",
            message=meta_result.get("response"),
            trace=trace,
        )
    
    def _build_routed_response(
        self,
        trace_id: str,
        result: dict,
        trace: RouterTrace
    ) -> RouterResponse:
        """Build response for routed request"""
        return RouterResponse(
            trace_id=trace_id,
            domain=result.get("domain"),
            intent=result.get("intent"),
            intent_type=result.get("intent_type"),
            slots=result.get("slots", {}),
            confidence=result.get("confidence"),
            source=result.get("source", "UNKNOWN"),
            status="ROUTED",
            trace=trace,
        )
    
    def _build_unknown_response(
        self,
        trace_id: str,
        trace: RouterTrace
    ) -> RouterResponse:
        """Build response for unknown request"""
        return RouterResponse(
            trace_id=trace_id,
            status="UNKNOWN",
            source="UNKNOWN",
            message="Xin lỗi, tôi chưa hiểu câu hỏi của bạn. Bạn có thể diễn đạt lại không?",
            trace=trace,
        )
    
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

