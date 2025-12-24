# 1. Tư duy tổng thể
- Một hệ = 3 tầng tách biệt tuyệt đối
```
Interface Layer
↓
Global Router (Decision System)
↓
Domain Engines (Business Systems)

```

- Router không làm nghiệp vụ
- Domain không tự route
- Interface không biết logic

Nếu trộn → chết khi scale.

# 2. Sơ đồ kiến trúc tổng
- Router = Decision System
- Domain Engine = Clean Architecture
- Knowledge Engine = RAG/LLM pipeline
- Router chọn engine, không chọn “domain chung chung”
- Không engine nào biết router tồn tại

```
┌──────────────────────── USER ────────────────────────┐
│                                                      │
│  Natural language, typo, slang, ambiguity            │
│                                                      │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────── ROUTER ORCHESTRATOR ──────────────┐
│                                                       │
│  STEP 0  Session load / create    					│ 
│  Step 0.5: Normalize input                            │                    
│                                                       │
│  STEP 1  Meta-task detection                          │
│          (help, reset, greeting, control)             │
│                                                       │
│  STEP 2  Global Pattern (hard rule)                   │
│          deterministic, priority-based                │
│                                                       │
│  STEP 3  Keyword Hint (soft boost)                    │
│          scoring hint only                            │
│                                                       │
│  STEP 4  Embedding Classifier                         │
│          semantic routing                             │
│                                                       │
│  STEP 5  LLM Classifier (fallback)                    │
│                                                       │
│  OUTPUT                                               │
│    - domain                                           │
│    - intent                                           │
│    - intent_type: OPERATION | KNOWLEDGE               │
│    - slots                                            │
│                                                       │
│  FULL TRACE FOR AUDIT                                 │
│                                                       │
└───────────────┬───────────────────┬───────────────────┘
                │                   │
                │                   │
                ▼                   ▼

┌──────────── HR DOMAIN ENGINE ────────────┐     ┌──── HR KNOWLEDGE ENGINE ─────┐
│ (Clean Architecture – Deterministic)     │     │ (Pipeline – Probabilistic)  │
│                                         │     │                              │
│  Entry Handler                           │     │  Retriever                  │
│   └─ map intent → use case               │     │   ├─ vector search           │
│                                         │     │   ├─ keyword search          │
│  Use Cases                               │     │                              │
│   ├─ create_leave_request                │     │  Prompt Templates            │
│   ├─ query_leave_balance                 │     │   ├─ system                  │
│   ├─ approve_leave                      │     │   ├─ QA                      │
│                                         │     │                              │
│  Entities                                │     │  LLM Answer Generator        │
│   ├─ Employee                            │     │                              │
│   ├─ LeaveRequest                       │     │  Citation / Confidence       │
│   └─ Policy                              │     │                              │
│                                         │     │  Read-only                   │
│  Ports                                   │     │                              │
│   ├─ Repository                          │     └──────────────────────────────┘
│   ├─ Notification                        │
│                                         │
│  Adapters                                │
│   ├─ SQL / SAP                           │
│   └─ Email                               │
│                                         │
│  OUTPUT                                  │
│   - SUCCESS | REJECT | NEED_MORE_INFO    │
│   - deterministic result                │
│                                         │
└─────────────────────────────────────────┘


┌──────────────────── SHARED SUPPORT ───────────────────┐
│                                                        │
│  Observability                                         │
│   - routing trace                                      │
│   - domain audit                                       │
│                                                        │
│  Config / Feature Flags                                │
│                                                        │
│  Security / AuthZ                                      │
│                                                        │
└────────────────────────────────────────────────────────┘


```

## 2.1 ROUTER ORCHESTRATOR - IN / OUT TỪNG STEP
- Router = decision system
- Mọi step đều ghi trace.
- STEP 0 — Session Load / Create
```
IN

{
  "raw_message": "string",
  "user_id": "string",
  "session_id": "optional"
}


PROCESS

load hoặc tạo session

lấy last_domain, context

OUT

{
  "session_id": "string",
  "last_domain": "optional",
  "conversation_state": {}
}
```
- STEP 0.5 — NORMALIZE INPUT (BẮT BUỘC)
```
Mục tiêu

	Chuẩn hoá đầu vào trước mọi quyết định

	Không suy luận intent

	Không inject domain

	Không gọi LLM domain

IN
{
  "raw_message": "string",
  "session_state": {
    "last_domain": "optional",
    "slots_memory": {}
  }
}

PROCESS (QUY ƯỚC CỐ ĐỊNH)

	trim whitespace

	lower-case (trừ entity)

	remove emoji / noise

	normalize unicode

	chuẩn hoá ngày tháng:

	"mai" → ISO date

	"tháng sau" → range

	expand viết tắt phổ biến

	không rewrite semantic

	không thêm từ

	không infer intent

OUT
{
  "normalized_message": "string",
  "normalized_entities": {
    "dates": [
      {
        "raw": "mai",
        "value": "2025-12-17",
        "confidence": 0.9
      }
    ]
  },
  "language": "vi",
  "noise_level": "LOW | MEDIUM | HIGH"
}

RULES (CẤM VI PHẠM)

	STEP 0.5 không được

		set domain

		set intent

		ghi session state

		Chỉ tạo dữ liệu trung gian cho STEP 1+
```
- STEP 1 — Meta-task Detection
```
Mục tiêu: xử lý lệnh điều khiển, không routing domain

IN

{
  "normalized_message": "string",
  "normalized_entities": {},
  "session_state": {}
}

OUT (nếu match)

{
  "handled": true,
  "response": "string",
  "type": "META"
}


OUT (nếu không match)

{
  "handled": false
}

```
- STEP 2 — Global Pattern Match (Hard Rule)
```
Mục tiêu: quyết định chắc chắn

IN

{
  "message": "string"
}


OUT (nếu match)

{
  "matched": true,
  "domain": "hr",
  "intent": "query_leave_balance",
  "intent_type": "OPERATION",
  "slots": {},
  "confidence": 1.0,
  "source": "PATTERN"
}


OUT (nếu fail)

{
  "matched": false
}
```
- STEP 3 — Keyword Hint (Soft)
```
Mục tiêu: gợi ý, không quyết định

IN

{
  "message": "string"
}


OUT

{
  "boost": {
    "hr": 0.4,
    "operations": 0.1
  }
}


Không domain final. Không intent.
```
- STEP 4 — Embedding Classifier
```
Mục tiêu: semantic routing

IN

{
  "message": "string",
  "boost": {
    "hr": 0.4
  }
}


OUT (nếu vượt threshold)

{
  "domain": "hr",
  "intent": "create_leave_request",
  "intent_type": "OPERATION",
  "slots": {
    "start_date": "2025-12-20"
  },
  "confidence": 0.82,
  "source": "EMBEDDING"
}


OUT (nếu fail)

{
  "classified": false
}
```
- STEP 5 — LLM Classifier (Fallback)
```
Mục tiêu: hiểu câu khó

IN

{
  "message": "string",
  "context": {}
}


OUT

{
  "domain": "hr",
  "intent": "knowledge_policy_leave",
  "intent_type": "KNOWLEDGE",
  "confidence": 0.65,
  "source": "LLM"
}
```
- STEP 6 — UNKNOWN
```
IN

{
  "all_steps_failed": true
}


OUT

{
  "status": "UNKNOWN",
  "ask_user": true,
  "options": ["HR", "Operations"]
}
```

## 2.2 ROUTER → ENGINE CONTRACT
- DomainRequest (chuẩn)
```
{
  "domain": "hr",
  "intent": "create_leave_request",
  "intent_type": "OPERATION",
  "slots": {},
  "user_context": {
    "user_id": "u123",
    "role": "employee"
  }
}
```
## 2.3 HR DOMAIN ENGINE — IN / OUT
- Entry Handler
```
IN

{
  "intent": "query_leave_balance",
  "slots": {},
  "user_context": {}
}


OUT

{
  "status": "SUCCESS",
  "data": {
    "leave_balance": 7
  },
  "audit": {
    "policy_checked": true
  }
}


Không có confidence. Không có fallback.
```

## 2.4 HR KNOWLEDGE ENGINE — IN / OUT
- Knowledge Request
```
IN

{
  "question": "Nghỉ phép năm tối đa bao nhiêu ngày?",
  "domain": "hr"
}


OUT

{
  "answer": "Nhân viên được nghỉ tối đa 12 ngày phép năm...",
  "citations": ["policy_2024.pdf#p3"],
  "confidence": 0.78
}


Read-only. Không audit nghiệp vụ.
```

## 2.5 OUTPUT VỀ USER (HỢP NHẤT)
```
{
  "message": "Bạn còn 7 ngày phép",
  "source": "HR_DOMAIN",
  "trace_id": "abc123"
}

```

## 2.6 Session State Contract
```
SessionState {
  session_id: string
  user_id: string

  active_domain: string | null
  last_domain: string | null

  last_intent: string | null
  last_intent_type: OPERATION | KNOWLEDGE | null

  pending_intent: string | null
  missing_slots: string[]

  slots_memory: {
    [slot_name]: value
  }

  retry_count: number
  escalation_flag: boolean

  created_at
  updated_at
}

```
Quy ước:

- Router chỉ đọc / ghi session
- Domain không giữ state
- Slot luôn merge vào slots_memory

# 3. SLOT LIFECYCLE — KHÓA QUYỀN RÕ
- Thêm Slot Lifecycle Rule.
```
Router:
- extract slot (best effort)
- không validate nghiệp vụ

Domain:
- validate slot
- quyết định slot đủ / thiếu
- không ghi session trực tiếp

Session Layer:
- persist slot
- clear slot khi intent hoàn tất

```
- Response domain khi thiếu slot:
```
{
  "status": "NEED_MORE_INFO",
  "missing_slots": ["start_date", "end_date"]
}

```

# 4. INTENT TAXONOMY — 1 NGUỒN SỰ THẬT
- Thêm file/bảng intent_registry.yaml.
```
- intent: query_leave_balance
  domain: hr
  intent_type: OPERATION
  required_slots: []
  optional_slots: []
  source_allowed: [PATTERN, EMBEDDING]

- intent: knowledge_policy_leave
  domain: hr
  intent_type: KNOWLEDGE
  required_slots: []
  source_allowed: [EMBEDDING, LLM]

```
- Router chỉ route intent có trong registry.
- Domain chỉ handle intent thuộc registry.


# 5. ROUTE COMMIT RULE — PSEUDOCODE BẮT BUỘC
```
if meta.handled:
    return meta.response

if pattern.matched:
    commit(pattern)

elif embedding.confidence >= 0.8:
    commit(embedding)

elif llm.confidence >= 0.65:
    commit(llm)

else:
    goto UNKNOWN

```
- Cấm override bằng code domain.

# 6.FAILURE MODE ENUM — DÙNG CHUNG TOÀN HỆ
- Thêm DomainResult Enum.
```
SUCCESS
NEED_MORE_INFO
REJECT_POLICY
REJECT_PERMISSION
INVALID_REQUEST
SYSTEM_ERROR

```
- Router xử lý:

	NEED_MORE_INFO → hỏi user
	REJECT_* → message cố định
	SYSTEM_ERROR → escalation

# 7.OBSERVABILITY — KHÓA TRACE
- Thêm Trace Spec.
```
trace_id: UUID (sinh tại STEP 0)

span:
- router.step.meta
- router.step.pattern
- router.step.embedding
- domain.hr.usecase.query_leave_balance
- knowledge.hr.retrieve

```	
- Log tối thiểu:
```
trace_id
step
input_hash
output
decision_source
confidence

```

# 8. UI BEHAVIOR THEO INTENT_TYPE
- Thêm Output Policy.
```
if intent_type == OPERATION:
    - require confirmation nếu destructive
    - không hiển thị confidence

if intent_type == KNOWLEDGE:
    - luôn hiển thị citation
    - không gọi domain

```

# 9. TYPE DEFINITIONS — SCHEMA BẮT BUỘC
- Tất cả types phải được định nghĩa rõ ràng.
- Dùng TypeScript hoặc Pydantic cho Python.
- Không dùng `any`, `object`, `dict` không rõ ràng.

## 9.1 Router Types
```typescript
// Router Input
interface RouterRequest {
  raw_message: string;           // required, non-empty, max 5000 chars
  user_id: string;               // required, UUID format
  session_id?: string;           // optional, UUID format
  metadata?: {
    platform?: string;            // "web" | "mobile" | "api"
    timestamp?: string;           // ISO 8601
  };
}

// Router Output
interface RouterResponse {
  trace_id: string;              // UUID, required
  domain: string | null;         // snake_case, required if routed
  intent: string | null;         // snake_case, required if routed
  intent_type: "OPERATION" | "KNOWLEDGE" | null;
  slots: Record<string, unknown>; // required, empty object if none
  confidence: number | null;     // 0.0-1.0, null if PATTERN
  source: "META" | "PATTERN" | "EMBEDDING" | "LLM" | "UNKNOWN";
  message?: string;              // user-facing message
  status: "ROUTED" | "META_HANDLED" | "UNKNOWN";
  trace: RouterTrace;            // required
}

// Session State
interface SessionState {
  session_id: string;            // UUID, required
  user_id: string;               // UUID, required
  active_domain: string | null;  // snake_case or null
  last_domain: string | null;    // snake_case or null
  last_intent: string | null;    // snake_case or null
  last_intent_type: "OPERATION" | "KNOWLEDGE" | null;
  pending_intent: string | null; // snake_case or null
  missing_slots: string[];       // required, empty array if none
  slots_memory: Record<string, unknown>; // required
  retry_count: number;           // >= 0, default 0
  escalation_flag: boolean;      // default false
  created_at: string;            // ISO 8601, required
  updated_at: string;            // ISO 8601, required
}

// Normalized Input
interface NormalizedInput {
  normalized_message: string;    // required, non-empty
  normalized_entities: {
    dates?: Array<{
      raw: string;
      value: string;             // ISO date or range
      confidence: number;        // 0.0-1.0
    }>;
    numbers?: Array<{
      raw: string;
      value: number;
      unit?: string;
    }>;
  };
  language: string;              // ISO 639-1 code, default "vi"
  noise_level: "LOW" | "MEDIUM" | "HIGH";
}
```

## 9.2 Domain Engine Types
```typescript
// Domain Request
interface DomainRequest {
  domain: string;                // required, snake_case
  intent: string;                // required, snake_case
  intent_type: "OPERATION" | "KNOWLEDGE";
  slots: Record<string, unknown>; // required
  user_context: {
    user_id: string;             // UUID, required
    role: string;                // required
    permissions?: string[];      // optional
  };
  trace_id: string;              // UUID, required
}

// Domain Response
interface DomainResponse {
  status: "SUCCESS" | "NEED_MORE_INFO" | "REJECT_POLICY" | 
          "REJECT_PERMISSION" | "INVALID_REQUEST" | "SYSTEM_ERROR";
  data?: Record<string, unknown>; // required if SUCCESS
  missing_slots?: string[];      // required if NEED_MORE_INFO
  message?: string;              // user-facing message
  audit?: {
    policy_checked: boolean;
    timestamp: string;           // ISO 8601
    [key: string]: unknown;
  };
  error_code?: string;           // snake_case, required if error
  error_details?: Record<string, unknown>;
}
```

## 9.3 Knowledge Engine Types
```typescript
// Knowledge Request
interface KnowledgeRequest {
  question: string;              // required, non-empty
  domain: string;                // required, snake_case
  context?: {
    user_id?: string;
    previous_questions?: string[];
  };
  trace_id: string;              // UUID, required
}

// Knowledge Response
interface KnowledgeResponse {
  answer: string;                // required, non-empty
  citations: string[];           // required, array of references
  confidence: number;            // 0.0-1.0, required
  sources?: Array<{
    title: string;
    url?: string;
    page?: number;
    excerpt?: string;
  }>;
  metadata?: {
    retrieval_method: "vector" | "keyword" | "hybrid";
    tokens_used?: number;
  };
}
```

# 10. CODE STYLE & NAMING CONVENTIONS — BẮT BUỘC
- Tuân thủ 100%, không exception.

## 10.1 Naming Rules
```
Files:
- router_orchestrator.py (snake_case)
- domain_engine.py (snake_case)
- session_manager.py (snake_case)

Classes:
- RouterOrchestrator (PascalCase)
- DomainEngine (PascalCase)
- SessionManager (PascalCase)

Functions:
- normalize_input() (snake_case)
- detect_meta_task() (snake_case)
- commit_route() (snake_case)

Variables:
- session_state (snake_case)
- normalized_message (snake_case)
- trace_id (snake_case)

Constants:
- MAX_MESSAGE_LENGTH = 5000 (UPPER_SNAKE_CASE)
- EMBEDDING_THRESHOLD = 0.8 (UPPER_SNAKE_CASE)

Enums:
- IntentType.OPERATION (PascalCase.upper)
- DomainResult.SUCCESS (PascalCase.upper)
```

## 10.2 Code Structure Rules
```
1. Mỗi file chỉ 1 class chính
2. Functions tối đa 50 dòng
3. Classes tối đa 300 dòng
4. Nested levels tối đa 3
5. Import order: stdlib → third-party → local
6. Type hints bắt buộc cho Python 3.12+
7. Docstrings cho tất cả public functions/classes
```

## 10.3 Error Handling Pattern
```python
# BẮT BUỘC: Dùng custom exceptions
class RouterError(Exception):
    """Base exception for router"""
    pass

class InvalidInputError(RouterError):
    """Input validation failed"""
    pass

class SessionNotFoundError(RouterError):
    """Session not found"""
    pass

# BẮT BUỘC: Luôn log trước khi raise
logger.error(f"Session not found: {session_id}", extra={
    "trace_id": trace_id,
    "session_id": session_id
})
raise SessionNotFoundError(f"Session {session_id} not found")

# BẮT BUỘC: Không catch và silent
# SAI:
try:
    result = process()
except:
    pass

# ĐÚNG:
try:
    result = process()
except SpecificError as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
    raise RouterError("Processing failed") from e
```

# 11. VALIDATION RULES — BẮT BUỘC TRƯỚC MỌI XỬ LÝ
- Validation layer riêng, không trộn với business logic.

## 11.1 Input Validation
```python
# Router Request Validation
def validate_router_request(request: RouterRequest) -> None:
    if not request.raw_message or not request.raw_message.strip():
        raise InvalidInputError("raw_message is required and non-empty")
    
    if len(request.raw_message) > 5000:
        raise InvalidInputError("raw_message exceeds 5000 characters")
    
    if not is_valid_uuid(request.user_id):
        raise InvalidInputError("user_id must be valid UUID")
    
    if request.session_id and not is_valid_uuid(request.session_id):
        raise InvalidInputError("session_id must be valid UUID if provided")

# Domain Request Validation
def validate_domain_request(request: DomainRequest) -> None:
    if request.domain not in DOMAIN_REGISTRY:
        raise InvalidInputError(f"Unknown domain: {request.domain}")
    
    if request.intent not in INTENT_REGISTRY:
        raise InvalidInputError(f"Unknown intent: {request.intent}")
    
    # Validate intent belongs to domain
    intent_info = INTENT_REGISTRY[request.intent]
    if intent_info.domain != request.domain:
        raise InvalidInputError(
            f"Intent {request.intent} does not belong to domain {request.domain}"
        )
    
    # Validate required slots
    missing = [
        slot for slot in intent_info.required_slots
        if slot not in request.slots
    ]
    if missing:
        raise InvalidInputError(f"Missing required slots: {missing}")
```

## 11.2 Output Validation
```python
# BẮT BUỘC: Validate output trước khi return
def validate_router_response(response: RouterResponse) -> None:
    if response.status == "ROUTED":
        if not response.domain:
            raise ValueError("domain is required when status is ROUTED")
        if not response.intent:
            raise ValueError("intent is required when status is ROUTED")
        if response.confidence is None and response.source != "PATTERN":
            raise ValueError("confidence is required for non-PATTERN sources")
    
    if response.confidence is not None:
        if not 0.0 <= response.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
```

# 12. ERROR HANDLING & RECOVERY — QUY TẮC CỐ ĐỊNH
- Mọi error phải có recovery path rõ ràng.

## 12.1 Error Categories
```
1. VALIDATION_ERROR: Input không hợp lệ
   → Return 400, message rõ ràng, không retry

2. SESSION_ERROR: Session không tồn tại/corrupt
   → Tạo session mới, log warning

3. ROUTING_ERROR: Không route được
   → Fallback to UNKNOWN, log info

4. DOMAIN_ERROR: Domain engine lỗi
   → Return SYSTEM_ERROR, escalate, log error

5. EXTERNAL_ERROR: LLM/DB/API external lỗi
   → Retry với exponential backoff, max 3 lần
   → Nếu fail → fallback hoặc SYSTEM_ERROR

6. TIMEOUT_ERROR: Timeout
   → Retry 1 lần, nếu fail → SYSTEM_ERROR
```

## 12.2 Retry Strategy
```python
# BẮT BUỘC: Retry chỉ cho external calls
@retry(
    max_attempts=3,
    backoff=exponential_backoff(initial=1.0, max=10.0),
    retry_on=(ExternalServiceError, TimeoutError),
    no_retry_on=(ValidationError, PermissionError)
)
async def call_llm_classifier(message: str) -> LLMClassificationResult:
    # Implementation
    pass

# BẮT BUỘC: Không retry cho domain logic
# Domain logic phải deterministic, không retry
```

## 12.3 Error Response Format
```python
# BẮT BUỘC: Format error response nhất quán
{
    "status": "SYSTEM_ERROR",
    "message": "User-friendly message",
    "error_code": "LLM_TIMEOUT",
    "error_details": {
        "service": "llm_classifier",
        "timeout_seconds": 30,
        "retry_count": 3
    },
    "trace_id": "uuid",
    "timestamp": "2025-12-17T10:30:00Z"
}
```

# 13. TESTING REQUIREMENTS — BẮT BUỘC TRƯỚC DEPLOY
- Coverage tối thiểu 80% cho business logic, 100% cho critical paths.

## 13.1 Test Structure
```
tests/
├── unit/
│   ├── router/
│   │   ├── test_normalize.py
│   │   ├── test_pattern_match.py
│   │   └── test_embedding_classifier.py
│   └── domain/
│       └── test_hr_engine.py
├── integration/
│   ├── test_router_to_domain.py
│   └── test_session_flow.py
└── e2e/
    └── test_full_conversation.py
```

## 13.2 Test Requirements
```python
# BẮT BUỘC: Mỗi function có test
# BẮT BUỘC: Test edge cases
# BẮT BUỘC: Test error cases
# BẮT BUỘC: Test với invalid input

# Example
def test_normalize_input_empty_string():
    """Test normalize với empty string"""
    with pytest.raises(InvalidInputError):
        normalize_input("")

def test_normalize_input_unicode():
    """Test normalize với unicode characters"""
    result = normalize_input("Xin chào 👋")
    assert result.normalized_message == "xin chào"
    assert result.noise_level == "LOW"

def test_pattern_match_priority():
    """Test pattern match theo priority"""
    # Test patterns với priority cao match trước
    pass
```

## 13.3 Test Data
```
# BẮT BUỘC: Test data riêng, không dùng production
# BẮT BUỘC: Mock external services
# BẮT BUỘC: Test với realistic data nhưng không sensitive
```

# 14. LOGGING & MONITORING — STANDARD FORMAT
- Tất cả logs phải structured, searchable.

## 14.1 Log Format
```python
# BẮT BUỘC: Structured logging
logger.info(
    "Router step completed",
    extra={
        "trace_id": trace_id,
        "step": "pattern_match",
        "domain": "hr",
        "intent": "query_leave_balance",
        "confidence": 1.0,
        "source": "PATTERN",
        "duration_ms": 45,
        "user_id": user_id,
        "session_id": session_id
    }
)

# BẮT BUỘC: Log levels
# DEBUG: Chi tiết internal flow
# INFO: Business events (routing decisions)
# WARNING: Recoverable issues (fallback used)
# ERROR: Errors cần attention
# CRITICAL: System failures
```

## 14.2 Metrics
```python
# BẮT BUỘC: Track metrics sau
METRICS = {
    "router_requests_total": Counter,
    "router_latency_seconds": Histogram,
    "router_errors_total": Counter,
    "domain_requests_total": Counter,
    "domain_latency_seconds": Histogram,
    "session_creates_total": Counter,
    "embedding_classifier_confidence": Histogram,
    "llm_classifier_confidence": Histogram,
}

# BẮT BUỘC: Labels cho metrics
router_requests_total.labels(
    domain="hr",
    source="PATTERN",
    status="SUCCESS"
).inc()
```

## 14.3 Alerting Rules
```
# BẮT BUỘC: Alerts cho
1. Error rate > 5% trong 5 phút
2. P95 latency > 2s trong 5 phút
3. UNKNOWN rate > 10% trong 10 phút
4. External service downtime
5. Session corruption rate > 1%
```

# 15. SECURITY RULES — BẮT BUỘC
- Security first, không compromise.

## 15.1 Input Sanitization
```python
# BẮT BUỘC: Sanitize input
def sanitize_input(raw_message: str) -> str:
    # Remove script tags
    # Escape special characters nếu cần
    # Validate encoding
    # Limit length
    pass

# BẮT BUỘC: Validate user_id, session_id
# Không trust client-provided IDs
def validate_user_access(user_id: str, session_id: str) -> bool:
    # Verify user owns session
    # Check permissions
    pass
```

## 15.2 Data Protection
```
# BẮT BUỘC:
1. Không log sensitive data (PII, passwords)
2. Encrypt session data nếu chứa sensitive
3. Sanitize logs trước khi output
4. Rate limiting cho API
5. Authentication required cho tất cả endpoints
```

## 15.3 Authorization
```python
# BẮT BUỘC: Check permissions trước mọi operation
def check_permission(
    user_id: str,
    domain: str,
    intent: str,
    intent_type: str
) -> bool:
    # Verify user có quyền access domain
    # Verify user có quyền thực hiện intent
    # OPERATION intents cần permission check
    # KNOWLEDGE intents có thể public
    pass
```

# 16. PERFORMANCE REQUIREMENTS — SLAs
- Performance là feature, không phải nice-to-have.

## 16.1 Latency Targets
```
STEP 0 (Session): < 50ms (P95)
STEP 0.5 (Normalize): < 10ms (P95)
STEP 1 (Meta): < 20ms (P95)
STEP 2 (Pattern): < 30ms (P95)
STEP 3 (Keyword): < 20ms (P95)
STEP 4 (Embedding): < 200ms (P95)
STEP 5 (LLM): < 2000ms (P95)
Domain Engine: < 500ms (P95)
Knowledge Engine: < 1500ms (P95)

Total Router: < 2500ms (P95)
```

## 16.2 Caching Rules
```python
# BẮT BUỘC: Cache
1. Session state: Cache 5 phút
2. Intent registry: Cache 1 giờ
3. Embedding vectors: Cache 24 giờ
4. Pattern matches: Không cache (deterministic)

# BẮT BUỘC: Cache invalidation
# Clear cache khi:
# - Intent registry updated
# - Session state changed
```

## 16.3 Resource Limits
```
# BẮT BUỘC: Limits
- Max message length: 5000 chars
- Max slots per request: 20
- Max session lifetime: 30 days
- Max retry count: 3
- Max concurrent requests per user: 10
```

# 17. DATABASE SCHEMA RULES — CONSISTENCY
- Schema versioning bắt buộc.

## 17.1 Session Table
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    active_domain VARCHAR(50),
    last_domain VARCHAR(50),
    last_intent VARCHAR(100),
    last_intent_type VARCHAR(20),
    pending_intent VARCHAR(100),
    missing_slots JSONB DEFAULT '[]',
    slots_memory JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    escalation_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
);
```

## 17.2 Audit Table
```sql
CREATE TABLE router_audit (
    trace_id UUID PRIMARY KEY,
    session_id UUID,
    user_id UUID NOT NULL,
    raw_message TEXT,
    normalized_message TEXT,
    domain VARCHAR(50),
    intent VARCHAR(100),
    intent_type VARCHAR(20),
    source VARCHAR(20),
    confidence DECIMAL(3,2),
    status VARCHAR(20),
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_domain_intent (domain, intent)
);
```

## 17.3 Migration Rules
```
# BẮT BUỘC:
1. Mọi schema change phải có migration
2. Migrations phải reversible
3. Test migrations trên staging trước
4. Backup trước khi migrate production
5. Version schema trong code
```

# 18. API VERSIONING — BACKWARD COMPATIBILITY
- API changes không được break existing clients.

## 18.1 Version Strategy
```
# URL versioning
/api/v1/router/route
/api/v2/router/route

# BẮT BUỘC:
1. Support ít nhất 2 versions cùng lúc
2. Deprecation notice ít nhất 3 tháng
3. Breaking changes chỉ trong major version
4. Minor version chỉ thêm fields optional
```

## 18.2 Response Compatibility
```python
# BẮT BUỘC: Không remove fields
# Chỉ thêm optional fields
# Deprecated fields vẫn return nhưng mark deprecated

{
    "domain": "hr",
    "intent": "query_leave_balance",
    # New field, optional
    "intent_category": "query",
    # Deprecated, vẫn return
    "old_field": "value"  # @deprecated
}
```

# 19. DEPLOYMENT & CI/CD — AUTOMATION
- Deployment phải automated, không manual steps.

## 19.1 CI Pipeline
```
# BẮT BUỘC: CI steps
1. Lint (black, flake8, mypy)
2. Unit tests (coverage >= 80%)
3. Integration tests
4. Security scan
5. Build Docker image
6. Push to registry
```

## 19.2 CD Pipeline
```
# BẮT BUỘC: CD steps
1. Deploy to staging
2. Run smoke tests
3. Deploy to production (blue-green)
4. Health check
5. Rollback nếu health check fail
```

## 19.3 Feature Flags
```python
# BẮT BUỘC: Feature flags cho
1. New routing algorithms
2. New domains
3. Experimental features
4. A/B testing

# Example
if feature_flags.is_enabled("new_embedding_model", user_id):
    result = new_embedding_classifier.classify(message)
else:
    result = old_embedding_classifier.classify(message)
```

# 20. DOCUMENTATION REQUIREMENTS — HANDOFF READY
- Documentation là code, phải maintain.

## 20.1 Code Documentation
```python
# BẮT BUỘC: Docstrings cho tất cả public APIs
def normalize_input(
    raw_message: str,
    session_state: SessionState
) -> NormalizedInput:
    """
    Normalize user input before routing.
    
    This function performs text normalization without inferring
    intent or domain. It only handles:
    - Whitespace trimming
    - Case normalization
    - Unicode normalization
    - Date/time expansion
    
    Args:
        raw_message: Raw user input message
        session_state: Current session state for context
        
    Returns:
        NormalizedInput with normalized message and entities
        
    Raises:
        InvalidInputError: If input is empty or invalid
        
    Example:
        >>> result = normalize_input("Xin chào 👋", session_state)
        >>> result.normalized_message
        'xin chào'
    """
    pass
```

## 20.2 Architecture Documentation
```
# BẮT BUỘC: Maintain
1. Architecture diagram (updated khi có thay đổi)
2. Sequence diagrams cho flows chính
3. API documentation (OpenAPI/Swagger)
4. Runbook cho operations
5. Troubleshooting guide
```

## 20.3 README Requirements
```
# BẮT BUỘC: README phải có
1. Quick start guide
2. Development setup
3. Testing instructions
4. Deployment guide
5. Configuration reference
6. Common issues & solutions
```

# 21. CODE REVIEW CHECKLIST — BẮT BUỘC
- Mọi PR phải pass checklist này.

```
□ Tuân thủ naming conventions
□ Type hints đầy đủ
□ Error handling đúng pattern
□ Validation đầy đủ
□ Tests pass (coverage >= 80%)
□ Logging structured
□ Security review passed
□ Performance impact assessed
□ Documentation updated
□ Migration script nếu có schema change
□ Backward compatibility checked
□ Feature flag nếu cần
```

# 22. RUNTIME CONFIGURATION — ENVIRONMENT VARIABLES
- Configuration externalized, không hardcode.

## 22.1 Required Config
```python
# BẮT BUỘC: Environment variables
ROUTER_CONFIG = {
    "EMBEDDING_THRESHOLD": float(os.getenv("EMBEDDING_THRESHOLD", "0.8")),
    "LLM_THRESHOLD": float(os.getenv("LLM_THRESHOLD", "0.65")),
    "MAX_MESSAGE_LENGTH": int(os.getenv("MAX_MESSAGE_LENGTH", "5000")),
    "SESSION_TTL_SECONDS": int(os.getenv("SESSION_TTL_SECONDS", "2592000")),
    "LLM_TIMEOUT_SECONDS": int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
    "ENABLE_LLM_FALLBACK": os.getenv("ENABLE_LLM_FALLBACK", "true").lower() == "true",
}

# BẮT BUỘC: Validate config on startup
def validate_config():
    if ROUTER_CONFIG["EMBEDDING_THRESHOLD"] < 0 or ROUTER_CONFIG["EMBEDDING_THRESHOLD"] > 1:
        raise ValueError("EMBEDDING_THRESHOLD must be between 0 and 1")
```

# 23. FINAL RULES — KHÔNG VI PHẠM
- Các rules này là absolute, không có exception.

```
1. Router không bao giờ gọi domain logic
2. Domain không bao giờ tự route
3. Session chỉ được modify bởi Router
4. Mọi step phải có trace
5. Mọi error phải có log
6. Mọi input phải validate
7. Mọi output phải validate
8. Không hardcode business logic
9. Không skip tests
10. Không deploy code chưa review
```