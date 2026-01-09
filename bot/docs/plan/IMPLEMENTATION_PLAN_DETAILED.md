# 🗂️ KỀ HOẠCH TRIỂN KHAI CHI TIẾT - HUB BOT

**Cập nhật**: 8 Tháng 1, 2025  
**Giai đoạn**: Phase 1 → Phase 4  
**Total Duration**: 5 tuần (25 ngày làm việc)

---

## 📅 TIMELINE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: ROUTER FOUNDATION                   │
│                         (Week 1 - 2)                            │
├─────────────────────────────────────────────────────────────────┤
│ Mon-Fri (Week 1): Core Implementation                           │
│ Mon-Fri (Week 2): Testing & Hardening                           │
│ Deliverable: Demo-ready routing with audit trail              │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 2: DOMAIN ENGINES                        │
│                    (Week 2-3, partial)                          │
├─────────────────────────────────────────────────────────────────┤
│ Mon-Fri: Domain layer implementation                            │
│ Deliverable: HR domain + Catalog domain fully working          │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: KNOWLEDGE ENGINE                          │
│                    (Week 3-4)                                   │
├─────────────────────────────────────────────────────────────────┤
│ Mon-Fri: RAG pipeline, vector store integration                │
│ Deliverable: Q&A system working with knowledge base            │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 4: EXPERIENCE & PRODUCTION READY                  │
│                    (Week 4-5)                                   │
├─────────────────────────────────────────────────────────────────┤
│ Mon-Fri: Monitoring, admin panel, deployment                   │
│ Deliverable: Production-ready system                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔴 PHASE 1: ROUTER FOUNDATION (Week 1-2)

### Goal
> "Message → Route Decision → Audit Trail" works end-to-end

### Success Criteria
- [ ] Router trả về routing decision cho 95% messages
- [ ] Trace được mọi quyết định routing
- [ ] Confidence score hợp lý (0.6-1.0)
- [ ] Error rate < 2%
- [ ] Response time < 200ms

---

### Week 1: Core Implementation

#### **Day 1-2: Session Repository Implementation** 🔴 CRITICAL

**Priority**: 🔴 Blocking all routing tests

**What to build**:
```python
# backend/infrastructure/session_repository.py
class ISessionRepository(ABC):
    async def get(self, session_id: str) -> Optional[SessionState]
    async def save(self, session: SessionState) -> None
    async def delete(self, session_id: str) -> None
    async def clear_expired(self) -> int

class RedisSessionRepository(ISessionRepository):
    # Implementation using aioredis
    # TTL = 30 days (SESSION_TTL_SECONDS)
    # Cache = 5 minutes per request
```

**Files to create**:
- `backend/infrastructure/session_repository.py` (150 lines)

**Files to modify**:
- `backend/router/steps/session_step.py` - use RedisSessionRepository
- `backend/infrastructure/__init__.py` - export

**Tests to add**:
- `tests/unit/test_session_repository.py` (100+ lines)
- Test TTL expiry
- Test cache invalidation
- Test concurrent access

**Acceptance Criteria**:
```
✅ Session persists across requests
✅ Session TTL auto-expires
✅ Concurrent requests don't conflict
✅ Response time < 50ms
```

---

#### **Day 2-3: Embedding Classifier Implementation** 🔴 CRITICAL

**Priority**: 🔴 Enable intelligent routing

**What to build**:
```python
# backend/router/steps/embedding_step.py
class EmbeddingClassifierStep:
    async def __init__(self):
        # Load sentence-transformer model
        # Pre-compute embeddings for intent examples
        # Load from cache if available
    
    async def execute(self, message: str) -> Dict[str, Any]:
        # Encode message to embedding
        # Compare with intent embeddings
        # Return top match if confidence > threshold
```

**Dependencies**:
- Add to requirements.txt: `sentence-transformers>=2.2.2`
- Add torch if using local model (comment for now)

**Files to create**:
- `backend/infrastructure/embedding_model.py` (200 lines)
- `backend/infrastructure/intent_embeddings.py` (150 lines)

**Files to modify**:
- `backend/router/steps/embedding_step.py` - implement execute()
- `requirements.txt` - uncomment sentence-transformers

**Tests to add**:
- `tests/unit/test_embedding_classifier.py` (150+ lines)
- Test message → embedding conversion
- Test intent matching accuracy
- Test confidence scoring
- Test with Vietnamese language examples

**Data to prepare**:
- Create intent training examples in `config/intent_examples.yaml`
- For each intent: 3-5 examples in Vietnamese

**Acceptance Criteria**:
```
✅ Embedding model loads in < 2 seconds
✅ Accuracy on test set > 85%
✅ Response time < 200ms per message
✅ Handles Vietnamese unicode correctly
```

---

#### **Day 3-4: Error Handling & Validation** 🟠 IMPORTANT

**Priority**: 🟠 Enable robust routing

**What to fix**:
1. Environment variable validation on startup
2. Comprehensive error handling in orchestrator
3. Graceful degradation when steps fail

**Files to create**:
- `backend/shared/validators.py` (150 lines)

**Files to modify**:
- `backend/shared/config.py` - add Config.validate()
- `backend/router/orchestrator.py` - add error recovery
- `backend/interface/api.py` - fix CORS issue

**CORS Fix** (SECURITY):
```python
# BEFORE
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
cors_origins.append("*")  # INSECURE!

# AFTER
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
if "*" in cors_origins:
    logger.warning("⚠️  CORS allow_origins=['*'] - INSECURE! Use specific origins.")
    # In production, this should fail startup
```

**Config Validation**:
```python
class Config:
    @classmethod
    def validate(cls) -> None:
        """Validate all required configs on startup"""
        required = ["OPENAI_API_KEY", "DATABASE_URL", "REDIS_URL"]
        missing = [k for k in required if not getattr(cls, k, None)]
        if missing:
            raise ConfigError(f"Missing required env vars: {missing}")
        
        # Validate formats
        if not cls.DATABASE_URL.startswith("postgresql"):
            raise ConfigError("DATABASE_URL must be PostgreSQL")
```

**Tests to add**:
- `tests/unit/test_config_validation.py` (100 lines)
- `tests/unit/test_error_handling.py` (150 lines)

**Acceptance Criteria**:
```
✅ Startup fails with clear message if config invalid
✅ Each step failure is caught and logged
✅ Router returns UNKNOWN intent instead of crashing
✅ Response time doesn't spike on errors
```

---

#### **Day 4-5: Pattern & Keyword Steps Enhancement** 🟡 IMPROVE

**Priority**: 🟡 Improve routing accuracy

**What to improve**:
1. Enhance keyword hint with multilingual support
2. Add more patterns to intent registry
3. Add pattern validation

**Files to modify**:
- `config/intent_registry.yaml` - add 20+ patterns per domain
- `backend/router/steps/keyword_step.py` - add multilingual
- `backend/router/steps/pattern_step.py` - add validation

**New Pattern Examples**:
```yaml
patterns:
  - pattern: "(phép|nghỉ|leave|vacation|ngày)"
    domain: hr
    intent: query_leave_balance
    priority: 50
  
  - pattern: "(tạo|xin|đề xuất|request)\\s+(phép|nghỉ|leave)"
    domain: hr
    intent: create_leave_request
    priority: 60
```

**Tests to add**:
- `tests/unit/test_pattern_matching.py` (100 lines)
- `tests/unit/test_keyword_hint.py` (80 lines)

**Acceptance Criteria**:
```
✅ Pattern library has 50+ rules
✅ Multilingual matching works
✅ No false positives in test set
✅ Priority system works correctly
```

---

### Week 2: Testing & Validation

#### **Day 1-2: Integration Testing** 🟠 IMPORTANT

**Priority**: 🟠 Validate router flow end-to-end

**What to test**:
- Session flow: create → update → retrieve
- Pattern matching → domain routing
- Embedding matching → confidence scoring
- LLM fallback when embedding fails
- Error recovery

**Files to create**:
- `tests/integration/test_router_flow.py` (300+ lines)

**Test scenarios**:
```python
async def test_complete_routing_flow():
    """Test message → routing → response"""
    request = RouterRequest(...)
    response = await router.route(request)
    
    # Assertions:
    assert response.domain in ["hr", "catalog"]
    assert response.confidence >= 0.6
    assert response.trace_id
    assert len(response.routing_trace) > 0

async def test_session_persistence():
    """Test session state across requests"""
    # Request 1
    response1 = await router.route(request1)
    session_id = response1.session_id
    
    # Request 2 with same session
    response2 = await router.route(request2)
    assert response2.session_id == session_id

async def test_error_recovery():
    """Test system continues when external API fails"""
    # Mock embedding service to fail
    # System should fallback to LLM
    # Should return valid result
```

**Acceptance Criteria**:
```
✅ All 15+ routing scenarios pass
✅ Session persistence works
✅ Error handling doesn't crash
✅ Response time < 500ms
✅ Code coverage > 70%
```

---

#### **Day 2-3: Unit Test Suite** 🟠 IMPORTANT

**Priority**: 🟠 Cover each step thoroughly

**What to test**:
- Each router step independently
- Each exception type
- Edge cases

**Files to create/expand**:
- `tests/unit/test_router_steps.py` (200+ lines)
- `tests/unit/test_exceptions.py` (100 lines)
- `tests/unit/test_schemas.py` (80 lines)

**Test matrix**:
```
┌──────────────┬──────────────┬─────────────┐
│ Step         │ Happy Path   │ Error Cases │
├──────────────┼──────────────┼─────────────┤
│ Session      │ ✓            │ 3 scenarios │
│ Normalize    │ ✓            │ 2 scenarios │
│ Meta Task    │ ✓            │ 2 scenarios │
│ Pattern      │ ✓            │ 3 scenarios │
│ Keyword      │ ✓            │ 2 scenarios │
│ Embedding    │ ✓            │ 3 scenarios │
│ LLM          │ ✓            │ 3 scenarios │
└──────────────┴──────────────┴─────────────┘
```

**Acceptance Criteria**:
```
✅ Coverage > 80%
✅ All critical paths tested
✅ Error messages are clear
✅ Edge cases handled
```

---

#### **Day 3-5: Load & Performance Testing** 🟡 OPTIMIZE

**Priority**: 🟡 Ensure system can handle traffic

**What to test**:
- Response time under load
- Throughput
- Memory usage
- Cache effectiveness

**Files to create**:
- `tests/performance/test_load.py` (150 lines)

**Load test scenarios**:
```python
async def test_concurrent_requests(n=100):
    """Test 100 concurrent requests"""
    tasks = [
        router.route(create_request(i))
        for i in range(n)
    ]
    results = await asyncio.gather(*tasks)
    
    # Calculate metrics:
    # - Average latency
    # - P95 latency
    # - Throughput (req/sec)
    # - Error rate
```

**Performance targets**:
```
┌──────────────────┬─────────┬──────────┐
│ Metric           │ Target  │ Critical │
├──────────────────┼─────────┼──────────┤
│ P95 Latency      │ 200ms   │ 500ms    │
│ Throughput       │ 50 req/s│ 10 req/s │
│ Error Rate       │ < 1%    │ < 5%     │
│ Memory per req   │ < 50MB  │ < 100MB  │
└──────────────────┴─────────┴──────────┘
```

**Acceptance Criteria**:
```
✅ P95 latency < 200ms
✅ Throughput > 50 req/sec
✅ Error rate < 1%
✅ Memory stable
```

---

#### **Day 4-5: Documentation & Demo Prep** 📝 FINAL

**Priority**: 📝 Make it production-ready

**What to create**:
- Phase 1 completion checklist
- API documentation
- Demo scenario scripts

**Files to create**:
- `docs/PHASE1_COMPLETE.md` - Phase 1 summary
- `docs/API_REFERENCE.md` - API endpoints
- `examples/demo_routing.py` - Demo script

**Acceptance Criteria**:
```
✅ All Phase 1 todos completed
✅ Code passes lint/format/type-check
✅ Documentation updated
✅ Demo script works
✅ Ready for stakeholder demo
```

---

## 🟠 PHASE 2: DOMAIN ENGINES (Week 2-3)

### Goal
> "Each domain handles its business logic independently"

**Parallel with Phase 1 Week 2**

---

### **Sprint 2.1: HR Domain** (Days 1-5)

#### **Day 1-2: Implement HR Repository**

**What to build**:
```python
# backend/domain/hr/adapters/postgresql_repository.py
class PostgreSQLHRRepository(IHRRepository):
    async def get_employee(self, employee_id: str) -> Optional[Employee]
    async def get_leave_balance(self, employee_id: str) -> LeaveBalance
    async def create_leave_request(self, request: LeaveRequest) -> LeaveRequest
    async def get_leave_requests(self, employee_id: str) -> List[LeaveRequest]
    async def approve_leave(self, request_id: str, approver_id: str) -> LeaveRequest
```

**Database queries** to implement:
- SELECT employee by ID
- SELECT leave balance by employee
- INSERT leave request
- SELECT leave requests with filters
- UPDATE leave request status

**Files to create/modify**:
- `backend/domain/hr/adapters/postgresql_repository.py` - full impl (250 lines)
- `backend/domain/hr/entities/` - add more entities if needed

**Tests to add**:
- `tests/unit/test_hr_repository.py` (200 lines)
- `tests/integration/test_hr_domain.py` (150 lines)

---

#### **Day 2-3: Use Cases Implementation**

**What to build**:
```python
# backend/domain/hr/use_cases/query_leave_balance.py
class QueryLeaveBalanceUseCase:
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Extract user_id from context
        # Query repository for leave balance
        # Apply RBAC if needed
        # Return formatted response

# backend/domain/hr/use_cases/create_leave_request.py
class CreateLeaveRequestUseCase:
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Validate dates
        # Check leave balance
        # Create request
        # Trigger approval workflow
        # Send notification
```

**Files to modify**:
- `backend/domain/hr/use_cases/query_leave_balance.py` (150 lines)
- `backend/domain/hr/use_cases/create_leave_request.py` (200 lines)
- `backend/domain/hr/use_cases/approve_leave.py` (180 lines)

**Tests to add**:
- `tests/unit/test_hr_use_cases.py` (250 lines)

---

#### **Day 3-4: RBAC & Permissions**

**What to build**:
```python
# backend/domain/hr/middleware/rbac.py
class RBACMiddleware:
    async def check_permission(self, user_id: str, action: str) -> bool:
        # Get user roles
        # Check if role has permission
        # Return True/False
    
    async def can_create_leave_request(self, user_id: str) -> bool:
    async def can_approve_leave_request(self, user_id: str) -> bool:
    async def can_view_others_leave(self, user_id: str) -> bool:
```

**Files to modify**:
- `backend/domain/hr/middleware/rbac.py` - full implementation

**Permission Matrix**:
```
┌──────────┬─────────────────┬──────────────┬─────────────┐
│ Role     │ Create Request  │ Approve      │ View Other  │
├──────────┼─────────────────┼──────────────┼─────────────┤
│ Employee │ ✓ Own only      │ ✗            │ ✗           │
│ Manager  │ ✓               │ ✓ Team only  │ ✓ Team only │
│ Admin    │ ✓               │ ✓            │ ✓           │
└──────────┴─────────────────┴──────────────┴─────────────┘
```

---

#### **Day 4-5: Error Handling & Validation**

**What to add**:
- Input validation (dates, reasons)
- Business rule validation (leave balance check)
- Error responses
- Audit logging

**Files to create/modify**:
- `backend/domain/hr/entities/` - add validators
- `backend/domain/hr/entry_handler.py` - error handling

**Validation Rules**:
```python
# Date validation
assert start_date <= end_date
assert start_date >= today

# Balance validation
assert remaining_balance >= days_requested

# Policy validation
assert leave_type in allowed_types
assert reason not empty
```

---

### **Sprint 2.2: Catalog Domain** (Days 1-3, parallel)

**What to build**:
- Catalog entry handler
- Link to knowledge engine
- Catalog API integration

**Files to create**:
- `backend/domain/catalog/entry_handler.py` (150 lines)

**Acceptance Criteria**:
```
✅ HR domain 100% working
✅ Catalog domain structure ready
✅ Both domains pass tests
✅ No cross-domain conflicts
```

---

## 🟡 PHASE 3: KNOWLEDGE ENGINE (Week 3-4)

### Goal
> "RAG pipeline retrieves relevant knowledge for Q&A"

---

### **Sprint 3.1: RAG Pipeline** (Days 1-4)

#### **Day 1-2: Vector Store Setup**

**What to build**:
```python
# backend/infrastructure/vector_store.py
class QdrantVectorStore:
    async def __init__(self, url: str):
        self.client = qdrant_async_client(url)
    
    async def index_documents(self, documents: List[Document]):
        # Split into chunks
        # Generate embeddings
        # Store in Qdrant
    
    async def search(self, query: str, top_k: int) -> List[Document]:
        # Encode query
        # Search in Qdrant
        # Return top-k results
```

**Files to create**:
- `backend/infrastructure/vector_store.py` (200 lines)

**Qdrant setup**:
```
Collections to create:
- hr_policies (for HR knowledge)
- catalog_products (for catalog knowledge)
- faq (for FAQ)

Each collection:
- Vector dimension: 1536 (OpenAI embedding)
- Distance metric: Cosine
- Payload: metadata (source, type, timestamp)
```

---

#### **Day 2-3: Knowledge Ingestion**

**What to build**:
```python
# backend/knowledge/knowledge_ingester.py
class DocumentIngester:
    async def ingest_from_url(self, url: str, domain: str):
        # Fetch document
        # Split into chunks
        # Generate embeddings
        # Store metadata
    
    async def ingest_from_file(self, file_path: str, domain: str):
        # Parse file (PDF, DOCX, TXT)
        # Split into chunks
        # Generate embeddings
        # Store metadata
    
    async def update_ingestion(self, doc_id: str):
        # Re-index document
        # Update timestamps
```

**Files to create**:
- `backend/knowledge/knowledge_ingester.py` (250 lines)

---

#### **Day 3-4: RAG Orchestrator**

**What to build**:
```python
# backend/knowledge/rag_orchestrator.py
class RAGOrchestrator:
    async def answer_question(self, query: str, domain: str) -> Answer:
        # Search knowledge base
        # Retrieve top-3 documents
        # Build context
        # Call LLM for answer
        # Add sources
    
    async def generate_answer_with_context(
        self, 
        query: str, 
        context: str
    ) -> str:
        # Call LLM with context window
        # Handle token limits
        # Extract answer
```

**Files to create/modify**:
- `backend/knowledge/rag_orchestrator.py` (200 lines)
- Modify `backend/knowledge/hr_knowledge_engine.py` (200 lines)
- Modify `backend/knowledge/catalog_knowledge_engine.py` (200 lines)

---

#### **Day 4-5: Knowledge Sync & Updates**

**What to build**:
```python
# backend/knowledge/catalog_knowledge_sync.py
class CatalogKnowledgeSync:
    async def sync_from_catalog(self):
        # Fetch from catalog service
        # Check for updates
        # Re-index if changed
        # Log sync results
    
    async def schedule_sync(self):
        # Run every 24 hours
        # Handle failures gracefully
```

**Files to modify**:
- `backend/knowledge/catalog_knowledge_sync.py` (200 lines)
- `backend/scripts/scheduled_sync_catalog_knowledge.py` (150 lines)

---

### **Sprint 3.2: Testing & Validation** (Days 3-5)

**What to test**:
- Document ingestion
- Vector search accuracy
- RAG pipeline
- Response quality

**Files to create**:
- `tests/integration/test_rag_pipeline.py` (200 lines)
- `tests/unit/test_vector_store.py` (150 lines)

**Acceptance Criteria**:
```
✅ Knowledge base ingested
✅ Search returns relevant results
✅ RAG answers are accurate
✅ Integration test passes
```

---

## 🟢 PHASE 4: PRODUCTION READY (Week 4-5)

### Goal
> "System ready for production deployment"

---

### **Sprint 4.1: Monitoring & Observability**

**What to build**:
- Prometheus metrics
- Grafana dashboards
- Alerting rules
- Log aggregation

**Files to create**:
- `backend/infrastructure/monitoring.py` (150 lines)
- `config/prometheus_alerts.yaml` (100 lines)
- `config/grafana_dashboards.json` (500 lines)

---

### **Sprint 4.2: Admin Panel Completion**

**What to build**:
- Admin dashboard with metrics
- Pattern management UI
- User management UI
- Audit logs viewer

**Files to modify**:
- `frontend/src/app/admin/*` (multiple pages)

---

### **Sprint 4.3: API Documentation**

**What to create**:
- OpenAPI/Swagger spec
- API reference guide
- Error code documentation
- Integration examples

**Files to create**:
- `docs/API_REFERENCE.md`
- `openapi.yaml`

---

### **Sprint 4.4: Deployment Readiness**

**What to do**:
- Docker image optimization
- Kubernetes manifests
- Database migrations
- Backup strategy

**Files to create/modify**:
- `Dockerfile` - optimize
- `kubernetes/` - manifests
- Database backup scripts

---

### **Sprint 4.5: Security Audit**

**What to check**:
- [ ] CORS properly restricted
- [ ] All inputs validated
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Rate limiting working
- [ ] Secrets not in git
- [ ] HTTPS enforced

---

## 📊 DELIVERABLES TIMELINE

```
Week 1 (Phần 1)
├── Day 1-2: Session Repository ✓ → Tests pass
├── Day 2-3: Embedding Classifier ✓ → 85%+ accuracy
├── Day 3-4: Error Handling ✓ → Config validated
├── Day 4-5: Pattern Enhancement ✓ → 50+ rules
└── **Milestone**: Phase 1 Part 1 complete

Week 1-2 (Phần 2)
├── Day 1-2: Integration Testing ✓ → 70% coverage
├── Day 2-3: Unit Tests ✓ → 80%+ coverage
├── Day 3-5: Load Testing ✓ → Meets performance targets
├── Day 4-5: Documentation ✓ → Ready for demo
└── **Milestone**: Phase 1 complete - DEMO READY

Week 2-3 (Song song)
├── Day 1-5: HR Domain ✓ → 100% working
├── Day 1-3: Catalog Domain ✓ → Structure ready
└── **Milestone**: Phase 2 complete

Week 3-4
├── Day 1-4: RAG Pipeline ✓ → Ingestion works
├── Day 3-5: Knowledge Sync ✓ → Auto-sync working
└── **Milestone**: Phase 3 complete - Q&A works

Week 4-5
├── Day 1-2: Monitoring ✓ → Dashboards live
├── Day 2-3: Admin Panel ✓ → All pages functional
├── Day 3-4: Documentation ✓ → Complete
├── Day 4-5: Security ✓ → Audit passed
└── **Milestone**: PRODUCTION READY ✅
```

---

## 🎯 SUCCESS METRICS

### Phase 1
- [ ] 95%+ messages route correctly
- [ ] Confidence score 0.6-1.0
- [ ] Response time < 200ms P95
- [ ] Error rate < 1%
- [ ] Test coverage > 80%

### Phase 2
- [ ] HR domain handles 100% use cases
- [ ] All use cases tested
- [ ] No cross-domain conflicts
- [ ] Permission system works

### Phase 3
- [ ] Knowledge base indexed
- [ ] Search accuracy > 90%
- [ ] Q&A system working
- [ ] < 5 second end-to-end latency

### Phase 4
- [ ] 100% production criteria met
- [ ] Security audit passed
- [ ] All documentation complete
- [ ] Ready for customer deployment

---

## 📋 RISK MITIGATION

### High Risk Items

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Embedding model too slow | Pre-compute + cache | AI/ML |
| LLM API cost too high | Rate limiting + caching | Backend |
| Database performance | Connection pooling + query optimization | Backend |
| Vector store scaling | Sharding strategy | Data Eng |
| Frontend complexity | Component-based design | Frontend |

---

## 👥 RESOURCE ALLOCATION

```
┌─────────────┬──────────┬──────────┬──────────┐
│ Component   │ Week 1-2 │ Week 3-4 │ Week 4-5 │
├─────────────┼──────────┼──────────┼──────────┤
│ Backend     │ 3 devs   │ 2 devs   │ 1 dev    │
│ Frontend    │ 1 dev    │ 1 dev    │ 2 devs   │
│ DevOps      │ 0.5 dev  │ 0.5 dev  │ 1 dev    │
│ QA          │ 1 dev    │ 2 devs   │ 2 devs   │
└─────────────┴──────────┴──────────┴──────────┘
```

---

## 📝 FILES TO CREATE/MODIFY

### Total
- **New Files**: 25+
- **Modified Files**: 35+
- **Lines of Code**: 5000+
- **Test Files**: 15+
- **Test Lines**: 2000+

---


