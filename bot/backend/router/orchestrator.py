"""
Router Orchestrator - Main routing decision system
"""
import uuid
from typing import Optional
from datetime import datetime

from ..schemas import RouterRequest, RouterResponse, RouterTrace, SessionState
from ..shared.exceptions import RouterError, InvalidInputError
from ..shared.logger import logger
from ..shared.config import config
from .steps import (
    SessionStep,
    NormalizeStep,
    MetaTaskStep,
    PatternMatchStep,
    KeywordHintStep,
    EmbeddingClassifierStep,
    LLMClassifierStep,
)


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
        trace = RouterTrace(trace_id=trace_id)
        
        try:
            logger.info(
                "Router request received",
                extra={
                    "trace_id": trace_id,
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "message_length": len(request.raw_message),
                }
            )
            
            # STEP 0: Session load/create
            session_state = await self._step_0_session(request, trace)
            
            # STEP 0.5: Normalize input
            normalized = await self._step_0_5_normalize(request, session_state, trace)
            
            # STEP 1: Meta-task detection
            meta_result = await self._step_1_meta(normalized, session_state, trace)
            if meta_result.get("handled"):
                return self._build_meta_response(trace_id, meta_result, trace)
            
            # STEP 2: Global pattern match
            pattern_result = await self._step_2_pattern(normalized, trace)
            if pattern_result.get("matched"):
                return self._build_routed_response(trace_id, pattern_result, trace)
            
            # STEP 3: Keyword hint
            boost = await self._step_3_keyword(normalized, trace)
            
            # STEP 4: Embedding classifier
            embedding_result = await self._step_4_embedding(normalized, boost, trace)
            if embedding_result.get("classified") and embedding_result.get("confidence", 0) >= config.EMBEDDING_THRESHOLD:
                return self._build_routed_response(trace_id, embedding_result, trace)
            
            # STEP 5: LLM classifier (fallback)
            if config.ENABLE_LLM_FALLBACK:
                llm_result = await self._step_5_llm(normalized, session_state, trace)
                if llm_result.get("classified") and llm_result.get("confidence", 0) >= config.LLM_THRESHOLD:
                    return self._build_routed_response(trace_id, llm_result, trace)
            
            # STEP 6: UNKNOWN
            return self._build_unknown_response(trace_id, trace)
            
        except Exception as e:
            logger.error(
                f"Router error: {e}",
                extra={"trace_id": trace_id},
                exc_info=True
            )
            raise RouterError(f"Routing failed: {e}") from e
    
    async def _step_0_session(
        self,
        request: RouterRequest,
        trace: RouterTrace
    ) -> SessionState:
        """STEP 0: Session load/create"""
        start_time = datetime.utcnow()
        
        try:
            session_state = await self.session_step.execute(request)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.session",
                {"user_id": request.user_id, "session_id": request.session_id},
                {"session_id": session_state.session_id},
                duration_ms
            )
            
            return session_state
        except Exception as e:
            logger.error(f"Session step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            raise
    
    async def _step_0_5_normalize(
        self,
        request: RouterRequest,
        session_state: SessionState,
        trace: RouterTrace
    ):
        """STEP 0.5: Normalize input"""
        start_time = datetime.utcnow()
        
        try:
            normalized = await self.normalize_step.execute(
                request.raw_message,
                session_state
            )
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.normalize",
                {"raw_message": request.raw_message[:100]},
                {"normalized_message": normalized.normalized_message[:100]},
                duration_ms
            )
            
            return normalized
        except Exception as e:
            logger.error(f"Normalize step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            raise
    
    async def _step_1_meta(self, normalized, session_state, trace):
        """STEP 1: Meta-task detection"""
        start_time = datetime.utcnow()
        
        try:
            result = await self.meta_step.execute(normalized, session_state)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.meta",
                {"normalized_message": normalized.normalized_message[:100]},
                result,
                duration_ms
            )
            
            return result
        except Exception as e:
            logger.error(f"Meta step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            return {"handled": False}
    
    async def _step_2_pattern(self, normalized, trace):
        """STEP 2: Global pattern match"""
        start_time = datetime.utcnow()
        
        try:
            result = await self.pattern_step.execute(normalized.normalized_message)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.pattern",
                {"normalized_message": normalized.normalized_message[:100]},
                result,
                duration_ms,
                score=result.get("confidence"),
                decision_source="PATTERN" if result.get("matched") else None
            )
            
            return result
        except Exception as e:
            logger.error(f"Pattern step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            return {"matched": False}
    
    async def _step_3_keyword(self, normalized, trace):
        """STEP 3: Keyword hint"""
        start_time = datetime.utcnow()
        
        try:
            result = await self.keyword_step.execute(normalized.normalized_message)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.keyword",
                {"normalized_message": normalized.normalized_message[:100]},
                result,
                duration_ms
            )
            
            return result.get("boost", {})
        except Exception as e:
            logger.error(f"Keyword step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            return {}
    
    async def _step_4_embedding(self, normalized, boost, trace):
        """STEP 4: Embedding classifier"""
        start_time = datetime.utcnow()
        
        try:
            result = await self.embedding_step.execute(
                normalized.normalized_message,
                boost
            )
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.embedding",
                {"normalized_message": normalized.normalized_message[:100], "boost": boost},
                result,
                duration_ms,
                score=result.get("confidence"),
                decision_source="EMBEDDING" if result.get("classified") else None
            )
            
            return result
        except Exception as e:
            logger.error(f"Embedding step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            return {"classified": False}
    
    async def _step_5_llm(self, normalized, session_state, trace):
        """STEP 5: LLM classifier"""
        start_time = datetime.utcnow()
        
        try:
            result = await self.llm_step.execute(
                normalized.normalized_message,
                session_state
            )
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            trace.add_span(
                "router.step.llm",
                {"normalized_message": normalized.normalized_message[:100]},
                result,
                duration_ms,
                score=result.get("confidence"),
                decision_source="LLM" if result.get("classified") else None
            )
            
            return result
        except Exception as e:
            logger.error(f"LLM step failed: {e}", extra={"trace_id": trace.trace_id}, exc_info=True)
            return {"classified": False}
    
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

