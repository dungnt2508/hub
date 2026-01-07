# 🚀 SPRINT 1-2: ROUTER CORE - IMPLEMENTATION PLAN
## Timeline: 2 Tuần (10 ngày làm việc)
## Team: 2 Backend Engineers
## Goal: Router pipeline hoàn chỉnh, routing chính xác >80%

---

## 🎯 SPRINT GOALS

### Primary Objectives
1. ✅ Session Repository hoạt động (Redis-backed)
2. ✅ Embedding Classifier chính xác >85%
3. ✅ LLM Fallback classifier working
4. ✅ Pattern/Keyword load từ DB (dynamic config)
5. ✅ Test coverage: 60% cho router module

### Success Criteria
- [ ] All router steps (0-7) functional
- [ ] Routing accuracy: >80% trên test dataset
- [ ] Session persistence: 100% reliable
- [ ] Latency: P99 < 500ms
- [ ] Tests passing: 60+ test cases

---

## 📋 TASK BREAKDOWN

### 🔹 TASK 1: Session Repository (3 days)
**Owner**: Engineer 1  
**Priority**: 🔴 CRITICAL  
**Dependencies**: None

#### Deliverables
1. **Interface Definition**
   ```python
   # backend/infrastructure/session_repository.py
   
   from abc import ABC, abstractmethod
   from typing import Optional
   from backend.schemas.session_types import SessionState
   
   class ISessionRepository(ABC):
       @abstractmethod
       async def get(self, session_id: str) -> Optional[SessionState]:
           """Retrieve session by ID"""
           pass
       
       @abstractmethod
       async def save(self, session: SessionState) -> None:
           """Save or update session"""
           pass
       
       @abstractmethod
       async def delete(self, session_id: str) -> None:
           """Delete session"""
           pass
       
       @abstractmethod
       async def clear_expired(self, ttl_seconds: int) -> int:
           """Clear expired sessions, return count deleted"""
           pass
   ```

2. **Redis Implementation**
   ```python
   # backend/infrastructure/redis_session_repository.py
   
   import json
   from typing import Optional
   import aioredis
   from backend.infrastructure.session_repository import ISessionRepository
   from backend.schemas.session_types import SessionState
   from backend.shared.config import config
   
   class RedisSessionRepository(ISessionRepository):
       def __init__(self):
           self.redis = None
           self._pool = None
       
       async def connect(self):
           """Initialize Redis connection pool"""
           self._pool = aioredis.ConnectionPool.from_url(
               config.REDIS_URL,
               max_connections=20,
               decode_responses=True
           )
           self.redis = aioredis.Redis(connection_pool=self._pool)
       
       async def close(self):
           """Close Redis connection"""
           if self._pool:
               await self._pool.disconnect()
       
       def _session_key(self, session_id: str) -> str:
           return f"session:{session_id}"
       
       async def get(self, session_id: str) -> Optional[SessionState]:
           key = self._session_key(session_id)
           data = await self.redis.get(key)
           if not data:
               return None
           
           session_dict = json.loads(data)
           return SessionState(**session_dict)
       
       async def save(self, session: SessionState) -> None:
           key = self._session_key(session.session_id)
           data = json.dumps(session.to_dict())
           
           # Set with TTL
           await self.redis.setex(
               key,
               config.SESSION_TTL_SECONDS,
               data
           )
       
       async def delete(self, session_id: str) -> None:
           key = self._session_key(session_id)
           await self.redis.delete(key)
       
       async def clear_expired(self, ttl_seconds: int) -> int:
           # Redis automatically expires keys with TTL
           # This is a no-op for Redis
           return 0
   ```

3. **Update Session Step**
   ```python
   # backend/router/steps/session_step.py
   
   from backend.infrastructure.redis_session_repository import RedisSessionRepository
   from backend.schemas.session_types import SessionState
   import uuid
   from datetime import datetime
   
   class SessionStep:
       def __init__(self):
           self.repository = RedisSessionRepository()
       
       async def initialize(self):
           """Called at startup"""
           await self.repository.connect()
       
       async def shutdown(self):
           """Called at shutdown"""
           await self.repository.close()
       
       async def execute(self, request: RouterRequest) -> SessionState:
           # Try to get existing session
           session = await self.repository.get(request.session_id)
           
           if session:
               # Check expiry
               age = (datetime.utcnow() - session.updated_at).total_seconds()
               if age > config.SESSION_TTL_SECONDS:
                   await self.repository.delete(request.session_id)
                   session = None
           
           # Create new session if needed
           if not session:
               session = SessionState(
                   session_id=request.session_id or str(uuid.uuid4()),
                   user_id=request.user_id,
                   created_at=datetime.utcnow(),
                   updated_at=datetime.utcnow()
               )
           else:
               # Update timestamp
               session.updated_at = datetime.utcnow()
           
           return session
       
       async def save_session(self, session: SessionState) -> None:
           """Save session after routing"""
           await self.repository.save(session)
   ```

4. **Tests**
   ```python
   # tests/unit/infrastructure/test_session_repository.py
   
   import pytest
   from backend.infrastructure.redis_session_repository import RedisSessionRepository
   from backend.schemas.session_types import SessionState
   import uuid
   from datetime import datetime
   
   @pytest.fixture
   async def repo():
       repository = RedisSessionRepository()
       await repository.connect()
       yield repository
       await repository.close()
   
   @pytest.mark.asyncio
   async def test_save_and_get_session(repo):
       session = SessionState(
           session_id=str(uuid.uuid4()),
           user_id="test-user",
           created_at=datetime.utcnow(),
           updated_at=datetime.utcnow()
       )
       
       await repo.save(session)
       retrieved = await repo.get(session.session_id)
       
       assert retrieved is not None
       assert retrieved.session_id == session.session_id
       assert retrieved.user_id == session.user_id
   
   @pytest.mark.asyncio
   async def test_session_expiry(repo):
       # Test TTL functionality
       # Mock time or use short TTL
       pass
   
   @pytest.mark.asyncio
   async def test_delete_session(repo):
       session = SessionState(
           session_id=str(uuid.uuid4()),
           user_id="test-user",
           created_at=datetime.utcnow(),
           updated_at=datetime.utcnow()
       )
       
       await repo.save(session)
       await repo.delete(session.session_id)
       retrieved = await repo.get(session.session_id)
       
       assert retrieved is None
   ```

#### Acceptance Criteria
- [ ] Redis connection pooling working
- [ ] CRUD operations tested
- [ ] TTL expiry working
- [ ] Session persistence across restarts
- [ ] Tests coverage: 80%

---

### 🔹 TASK 2: Embedding Classifier (4 days)
**Owner**: Engineer 2  
**Priority**: 🔴 CRITICAL  
**Dependencies**: None

#### Deliverables

1. **Embedding Infrastructure**
   ```python
   # backend/infrastructure/embedding_scorer.py
   
   from sentence_transformers import SentenceTransformer
   import numpy as np
   from typing import List, Dict, Tuple
   from backend.shared.intent_registry import intent_registry
   import pickle
   from pathlib import Path
   
   class EmbeddingScorer:
       def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
           self.model = SentenceTransformer(model_name)
           self.intent_embeddings: Dict[str, np.ndarray] = {}
           self.cache_path = Path("data/intent_embeddings.pkl")
       
       def load_or_compute_intent_embeddings(self):
           """Load cached embeddings or compute from scratch"""
           if self.cache_path.exists():
               with open(self.cache_path, 'rb') as f:
                   self.intent_embeddings = pickle.load(f)
               return
           
           # Compute from intent registry
           for domain, domain_info in intent_registry.domains.items():
               for intent_name, intent_info in domain_info["intents"].items():
                   # Get training examples
                   examples = self._get_training_examples(intent_name)
                   if not examples:
                       continue
                   
                   # Compute mean embedding
                   embeddings = self.model.encode(examples)
                   mean_embedding = np.mean(embeddings, axis=0)
                   
                   self.intent_embeddings[intent_name] = mean_embedding
           
           # Cache results
           self.cache_path.parent.mkdir(parents=True, exist_ok=True)
           with open(self.cache_path, 'wb') as f:
               pickle.dump(self.intent_embeddings, f)
       
       def _get_training_examples(self, intent_name: str) -> List[str]:
           """
           Get training examples for an intent.
           
           Sources:
           1. Pattern rules (từ DB hoặc config)
           2. Manual examples (từ intent_store)
           3. Historical data (optional)
           """
           examples = []
           
           # TODO: Load từ database pattern_rules table
           # WHERE intent = intent_name
           
           # For now, hardcoded examples:
           example_map = {
               "hr.query_leave": [
                   "Tôi còn bao nhiêu ngày phép?",
                   "Kiểm tra số ngày nghỉ",
                   "Xem số phép còn lại",
                   "Check leave balance"
               ],
               "catalog.search": [
                   "Tìm workflow tự động gửi email",
                   "Tôi cần tool automation",
                   "Workflow nào phù hợp với tôi?",
                   "Tìm product về email marketing"
               ]
           }
           
           return example_map.get(intent_name, [])
       
       def score_intent(self, query: str) -> List[Tuple[str, float]]:
           """
           Score query against all intents.
           
           Returns:
               List of (intent_name, similarity_score) sorted by score descending
           """
           if not self.intent_embeddings:
               self.load_or_compute_intent_embeddings()
           
           query_embedding = self.model.encode([query])[0]
           
           scores = []
           for intent_name, intent_embedding in self.intent_embeddings.items():
               similarity = self._cosine_similarity(query_embedding, intent_embedding)
               scores.append((intent_name, similarity))
           
           # Sort by score descending
           scores.sort(key=lambda x: x[1], reverse=True)
           return scores
       
       def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
           return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
   ```

2. **Embedding Step Implementation**
   ```python
   # backend/router/steps/embedding_step.py
   
   from backend.infrastructure.embedding_scorer import EmbeddingScorer
   from backend.schemas.router_types import NormalizedInput, RouterTrace
   from backend.shared.config import config
   from typing import Dict, Any
   
   class EmbeddingClassifierStep:
       def __init__(self):
           self.scorer = EmbeddingScorer()
           self.confidence_threshold = config.EMBEDDING_CONFIDENCE_THRESHOLD or 0.7
       
       async def initialize(self):
           """Load embeddings at startup"""
           self.scorer.load_or_compute_intent_embeddings()
       
       async def execute(
           self,
           normalized: NormalizedInput,
           trace: RouterTrace
       ) -> Dict[str, Any]:
           """
           Classify intent using semantic similarity.
           
           Returns:
               {
                   "classified": bool,
                   "intent": str,
                   "domain": str,
                   "confidence": float,
                   "scores": List[Tuple[str, float]]
               }
           """
           query = normalized.normalized_message
           
           # Score against all intents
           scores = self.scorer.score_intent(query)
           
           trace.add_step(
               step_name="embedding_classifier",
               input_data={"query": query},
               output_data={"top_5_scores": scores[:5]}
           )
           
           if not scores:
               return {"classified": False}
           
           top_intent, top_score = scores[0]
           
           if top_score >= self.confidence_threshold:
               # Extract domain from intent (e.g., "hr.query_leave" -> "hr")
               domain = top_intent.split(".")[0]
               
               return {
                   "classified": True,
                   "intent": top_intent,
                   "domain": domain,
                   "confidence": top_score,
                   "scores": scores,
                   "source": "EMBEDDING"
               }
           
           return {
               "classified": False,
               "top_score": top_score,
               "top_intent": top_intent
           }
   ```

3. **Tests**
   ```python
   # tests/unit/router/test_embedding_step.py
   
   import pytest
   from backend.router.steps.embedding_step import EmbeddingClassifierStep
   from backend.schemas.router_types import NormalizedInput, RouterTrace
   
   @pytest.fixture
   async def embedding_step():
       step = EmbeddingClassifierStep()
       await step.initialize()
       return step
   
   @pytest.mark.asyncio
   async def test_classify_hr_intent(embedding_step):
       normalized = NormalizedInput(
           normalized_message="Tôi còn bao nhiêu ngày phép?",
           raw_message="Tôi còn bao nhiêu ngày phép?",
           normalized_entities={}
       )
       trace = RouterTrace(trace_id="test-001")
       
       result = await embedding_step.execute(normalized, trace)
       
       assert result["classified"] == True
       assert result["domain"] == "hr"
       assert "query_leave" in result["intent"]
       assert result["confidence"] > 0.7
   
   @pytest.mark.asyncio
   async def test_classify_catalog_intent(embedding_step):
       normalized = NormalizedInput(
           normalized_message="Tìm workflow tự động gửi email",
           raw_message="Tìm workflow tự động gửi email",
           normalized_entities={}
       )
       trace = RouterTrace(trace_id="test-002")
       
       result = await embedding_step.execute(normalized, trace)
       
       assert result["classified"] == True
       assert result["domain"] == "catalog"
       assert result["confidence"] > 0.7
   
   @pytest.mark.asyncio
   async def test_low_confidence_query(embedding_step):
       normalized = NormalizedInput(
           normalized_message="xyz abc random text",
           raw_message="xyz abc random text",
           normalized_entities={}
       )
       trace = RouterTrace(trace_id="test-003")
       
       result = await embedding_step.execute(normalized, trace)
       
       # Should not classify với low confidence
       assert result["classified"] == False
   ```

#### Acceptance Criteria
- [ ] Embedding model loaded
- [ ] Intent embeddings precomputed
- [ ] Similarity scoring working
- [ ] Accuracy >85% on test set
- [ ] Latency <200ms per query
- [ ] Tests coverage: 75%

---

### 🔹 TASK 3: LLM Fallback Classifier (3 days)
**Owner**: Engineer 1  
**Priority**: 🟠 HIGH  
**Dependencies**: Task 1 complete

#### Deliverables

1. **LLM Classifier Implementation**
   ```python
   # backend/router/steps/llm_step.py
   
   from backend.infrastructure.ai_provider import AIProvider
   from backend.schemas.router_types import NormalizedInput, RouterTrace
   from backend.shared.intent_registry import intent_registry
   from typing import Dict, Any
   import json
   import asyncio
   
   class LLMClassifierStep:
       def __init__(self):
           self.ai_provider = AIProvider()
           self.timeout_seconds = 5
       
       def _build_classification_prompt(self, query: str) -> str:
           """Build prompt for LLM classification"""
           
           # Get all available intents
           intents = []
           for domain, domain_info in intent_registry.domains.items():
               for intent_name in domain_info["intents"].keys():
                   intents.append(intent_name)
           
           prompt = f"""You are an intent classifier for a multi-domain bot service.

Available intents:
{chr(10).join(f"- {intent}" for intent in intents)}

User query: "{query}"

Classify the query into ONE of the intents above.
If the query doesn't match any intent, respond with "UNKNOWN".

Respond in JSON format:
{{
  "intent": "intent_name or UNKNOWN",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}
"""
           return prompt
       
       async def execute(
           self,
           normalized: NormalizedInput,
           trace: RouterTrace
       ) -> Dict[str, Any]:
           """
           Classify using LLM as fallback.
           
           Returns same format as embedding classifier.
           """
           query = normalized.normalized_message
           prompt = self._build_classification_prompt(query)
           
           try:
               # Call with timeout
               response = await asyncio.wait_for(
                   self.ai_provider.chat(
                       messages=[{"role": "user", "content": prompt}],
                       temperature=0.0,  # Deterministic
                       max_tokens=200
                   ),
                   timeout=self.timeout_seconds
               )
               
               # Parse JSON response
               result_json = json.loads(response)
               
               trace.add_step(
                   step_name="llm_classifier",
                   input_data={"query": query},
                   output_data=result_json
               )
               
               if result_json["intent"] == "UNKNOWN":
                   return {"classified": False}
               
               intent = result_json["intent"]
               confidence = result_json["confidence"]
               
               # Extract domain
               domain = intent.split(".")[0]
               
               return {
                   "classified": True,
                   "intent": intent,
                   "domain": domain,
                   "confidence": confidence,
                   "source": "LLM",
                   "reasoning": result_json.get("reasoning")
               }
           
           except asyncio.TimeoutError:
               trace.add_step(
                   step_name="llm_classifier",
                   input_data={"query": query},
                   output_data={"error": "timeout"}
               )
               return {"classified": False, "error": "timeout"}
           
           except Exception as e:
               trace.add_step(
                   step_name="llm_classifier",
                   input_data={"query": query},
                   output_data={"error": str(e)}
               )
               return {"classified": False, "error": str(e)}
   ```

2. **Circuit Breaker**
   ```python
   # backend/infrastructure/circuit_breaker.py
   
   from typing import Callable, Any
   from datetime import datetime, timedelta
   import asyncio
   
   class CircuitBreaker:
       """Prevent repeated calls to failing service"""
       
       def __init__(
           self,
           failure_threshold: int = 5,
           recovery_timeout: int = 60,
           expected_exception: type = Exception
       ):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.expected_exception = expected_exception
           
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
       
       async def call(self, func: Callable, *args, **kwargs) -> Any:
           if self.state == "OPEN":
               # Check if recovery timeout has passed
               if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                   self.state = "HALF_OPEN"
               else:
                   raise Exception("Circuit breaker is OPEN")
           
           try:
               result = await func(*args, **kwargs)
               
               # Success - reset failure count
               if self.state == "HALF_OPEN":
                   self.state = "CLOSED"
               self.failure_count = 0
               
               return result
           
           except self.expected_exception as e:
               self.failure_count += 1
               self.last_failure_time = datetime.utcnow()
               
               if self.failure_count >= self.failure_threshold:
                   self.state = "OPEN"
               
               raise e
   ```

3. **Integration in RouterOrchestrator**
   ```python
   # backend/router/orchestrator.py (update)
   
   async def _step_5_llm(self, normalized, trace):
       """STEP 5: LLM Classifier (fallback)"""
       try:
           result = await self.llm_step.execute(normalized, trace)
           return result
       except Exception as e:
           logger.warning(f"LLM classifier failed: {e}")
           return {"classified": False, "error": str(e)}
   ```

#### Acceptance Criteria
- [ ] LLM integration working
- [ ] Circuit breaker prevents cascading failures
- [ ] Timeout mechanism (5s)
- [ ] Error handling comprehensive
- [ ] Fallback accuracy >70%
- [ ] Tests coverage: 70%

---

### 🔹 TASK 4: Dynamic Config Loading (2 days)
**Owner**: Engineer 2  
**Priority**: 🟡 MEDIUM  
**Dependencies**: None (can run parallel)

#### Deliverables

1. **Update Pattern Step**
   ```python
   # backend/router/steps/pattern_step.py (refactor)
   
   from backend.infrastructure.config_loader import ConfigLoader
   import re
   
   class PatternMatchStep:
       def __init__(self):
           self.config_loader = ConfigLoader()
           self.patterns_cache = []
           self.last_refresh = None
           self.refresh_interval = 300  # 5 minutes
       
       async def _load_patterns(self, tenant_id: Optional[str] = None):
           """Load patterns from DB via config loader"""
           patterns_config = await self.config_loader.get_pattern_rules(tenant_id)
           
           self.patterns_cache = []
           for rule in patterns_config:
               compiled_regex = re.compile(rule["pattern"], re.IGNORECASE)
               self.patterns_cache.append({
                   "regex": compiled_regex,
                   "domain": rule["domain"],
                   "intent": rule["intent"],
                   "priority": rule["priority"]
               })
           
           # Sort by priority
           self.patterns_cache.sort(key=lambda x: x["priority"], reverse=True)
       
       async def execute(self, normalized, trace, tenant_id=None):
           # Refresh if needed
           if not self.patterns_cache or self._should_refresh():
               await self._load_patterns(tenant_id)
           
           # Try to match
           for pattern in self.patterns_cache:
               match = pattern["regex"].search(normalized.normalized_message)
               if match:
                   return {
                       "matched": True,
                       "domain": pattern["domain"],
                       "intent": pattern["intent"],
                       "source": "PATTERN",
                       "pattern": pattern["regex"].pattern
                   }
           
           return {"matched": False}
   ```

2. **Update Keyword Step** (similar refactor)

3. **Tests**
   ```python
   # tests/unit/router/test_pattern_dynamic_loading.py
   
   @pytest.mark.asyncio
   async def test_pattern_loads_from_db(mock_config_loader):
       step = PatternMatchStep()
       step.config_loader = mock_config_loader
       
       await step._load_patterns(tenant_id="test-tenant")
       
       assert len(step.patterns_cache) > 0
       mock_config_loader.get_pattern_rules.assert_called_once()
   ```

#### Acceptance Criteria
- [ ] Patterns load từ DB
- [ ] Keywords load từ DB
- [ ] Cache refresh working (5 min interval)
- [ ] Tenant-specific patterns working
- [ ] Tests coverage: 70%

---

### 🔹 TASK 5: Router Integration & Testing (2 days)
**Owner**: Both Engineers  
**Priority**: 🔴 CRITICAL  
**Dependencies**: Tasks 1-4 complete

#### Deliverables

1. **Update RouterOrchestrator**
   - Integrate session save after routing
   - Wire up all steps
   - Add proper error handling

2. **Integration Tests**
   ```python
   # tests/integration/test_router_full_flow.py
   
   @pytest.mark.asyncio
   async def test_full_routing_flow_hr_query():
       """Test complete flow: user query -> routing -> session save"""
       
       request = RouterRequest(
           raw_message="Tôi còn bao nhiêu ngày phép?",
           user_id="test-user-123",
           session_id=None  # New session
       )
       
       response = await orchestrator.route(request)
       
       # Assertions
       assert response.status == "ROUTED"
       assert response.domain == "hr"
       assert "query_leave" in response.intent
       assert response.confidence > 0.7
       
       # Check session was saved
       session = await orchestrator.session_step.repository.get(response.session_id)
       assert session is not None
       assert session.last_domain == "hr"
   
   @pytest.mark.asyncio
   async def test_routing_with_existing_session():
       """Test routing với session context"""
       # Create session with history
       # Send follow-up query
       # Assert context was used
       pass
   ```

3. **Performance Tests**
   ```python
   # tests/performance/test_router_latency.py
   
   @pytest.mark.asyncio
   async def test_routing_latency():
       """Ensure P99 latency < 500ms"""
       import time
       
       latencies = []
       for _ in range(100):
           request = RouterRequest(
               raw_message="Test query",
               user_id="test-user"
           )
           
           start = time.time()
           await orchestrator.route(request)
           latency = time.time() - start
           
           latencies.append(latency)
       
       p99 = np.percentile(latencies, 99)
       assert p99 < 0.5  # 500ms
   ```

#### Acceptance Criteria
- [ ] All steps integrated
- [ ] End-to-end flow working
- [ ] Session persistence verified
- [ ] Latency acceptable
- [ ] 20+ integration tests

---

## 📊 SPRINT METRICS & TRACKING

### Daily Standup Template
```
Yesterday:
- Task X: 70% complete
- Blocker: Redis connection issue (resolved)

Today:
- Finish Task X
- Start Task Y

Blockers:
- None / [describe blocker]
```

### Progress Tracking

#### Day 1-3: Session Repository
- [ ] Day 1: Interface + Redis impl (50%)
- [ ] Day 2: Tests + integration (80%)
- [ ] Day 3: Bug fixes, complete (100%)

#### Day 3-6: Embedding Classifier
- [ ] Day 3: Infrastructure setup (30%)
- [ ] Day 4: Embedding computation (60%)
- [ ] Day 5: Scoring + tests (85%)
- [ ] Day 6: Tuning + complete (100%)

#### Day 4-6: LLM Classifier
- [ ] Day 4: LLM integration (50%)
- [ ] Day 5: Circuit breaker + tests (80%)
- [ ] Day 6: Integration + complete (100%)

#### Day 7-8: Dynamic Config
- [ ] Day 7: Pattern/keyword refactor (70%)
- [ ] Day 8: Tests + complete (100%)

#### Day 9-10: Integration & Testing
- [ ] Day 9: Router integration (60%)
- [ ] Day 10: E2E tests + fixes (100%)

### Success Metrics Dashboard

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Session persistence | 100% | TBD | ⏳ |
| Embedding accuracy | >85% | TBD | ⏳ |
| LLM accuracy | >70% | TBD | ⏳ |
| P99 latency | <500ms | TBD | ⏳ |
| Test coverage | >60% | TBD | ⏳ |
| Router steps working | 8/8 | 4/8 | ⏳ |

---

## 🚨 RISK MITIGATION

### Risk 1: Redis Connection Issues
**Mitigation**: 
- Use connection pooling
- Retry logic với exponential backoff
- Health check endpoint

### Risk 2: Embedding Model Too Slow
**Mitigation**:
- Precompute intent embeddings
- Cache query embeddings (optional)
- Use smaller model if needed

### Risk 3: LLM API Unreliable
**Mitigation**:
- Circuit breaker pattern
- Timeout (5s)
- Fallback to UNKNOWN

### Risk 4: Low Test Coverage
**Mitigation**:
- Write tests first (TDD)
- Daily coverage review
- Mandatory PR tests

---

## ✅ ACCEPTANCE CRITERIA (SPRINT 1-2 COMPLETE)

### Functional
- [ ] Session repository working (CRUD + TTL)
- [ ] Embedding classifier accuracy >85%
- [ ] LLM fallback working
- [ ] Pattern/keyword load from DB
- [ ] All 8 router steps functional
- [ ] Routing accuracy >80%

### Non-functional
- [ ] P99 latency <500ms
- [ ] Test coverage >60%
- [ ] No blocking bugs
- [ ] Documentation updated

### Quality Gates
- [ ] All tests passing
- [ ] Code review approved
- [ ] Performance benchmarks met
- [ ] Security review passed

---

## 📚 DOCUMENTATION UPDATES

After sprint completion, update:
1. **README.md**: Current status, how to run
2. **ARCHITECTURE.md**: Updated diagrams
3. **API_DOCS.md**: Router API examples
4. **TROUBLESHOOTING.md**: Common issues + fixes

---

## 🎉 SPRINT DEMO SCRIPT

### Demo Flow (End of Sprint 1-2)
1. **Show session persistence**
   - Send message
   - Kill server
   - Restart
   - Send follow-up message (context maintained)

2. **Show routing accuracy**
   - HR query → routed to HR domain
   - Catalog query → routed to catalog domain
   - Complex query → embedding classifier works

3. **Show metrics**
   - Test coverage report
   - Latency benchmarks
   - Routing accuracy on test set

---

**Next**: After Sprint 1-2, move to **SPRINT 3-4: Security Hardening**
