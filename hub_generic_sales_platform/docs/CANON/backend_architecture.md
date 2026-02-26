# Kiến Trúc Backend

## Tổng Quan

Agentic Sales Platform sử dụng **Clean Architecture** (Hexagonal Architecture) kết hợp **100% Async** để đảm bảo khả năng mở rộng, bảo trì và hiệu năng cao.

=> **Điểm linh hoạt ăn tiền:** Domain không phụ thuộc DB hay framework. Đổi PostgreSQL sang MongoDB, đổi FastAPI sang NestJS - phần lõi nghiệp vụ vẫn nguyên.

---

## Cấu Trúc Lớp (Layer Structure)

```text
app/
├── core/                    # Layer 1: DOMAIN (Logic nghiệp vụ thuần)
│   ├── config/              # Cấu hình (Pydantic Settings)
│   ├── domain/              # Entity nghiệp vụ (Pydantic models)
│   ├── interfaces/          # Ports (Interface trừu tượng)
│   ├── services/            # Domain services
│   └── shared/              # Tiện ích dùng chung
│
├── application/             # Layer 2: APPLICATION (Use Cases)
│   ├── orchestrators/       # Điều phối luồng
│   │   ├── hybrid_orchestrator.py    # Logic 3-tier
│   │   └── agent_orchestrator.py     # Động cơ suy luận Agentic
│   └── services/
│       ├── agent_tool_registry.py    # Đăng ký Tool
│       ├── catalog_state_handler.py  # Thao tác catalog
│       ├── slot_extractor.py         # Trích xuất context
│       └── session_state.py          # Quản lý phiên
│
├── infrastructure/          # Layer 3: INFRASTRUCTURE (Chi tiết kỹ thuật)
│   ├── database/            # SQLAlchemy, repositories
│   ├── llm/                 # Adapter LLM (OpenAI, circuit breaker)
│   └── search/              # Vector search (pgvector)
│
└── interfaces/              # Layer 4: BOUNDARY (Giao diện bên ngoài)
    ├── api/                 # FastAPI REST
    ├── middleware/          # Auth, tenant isolation
    └── webhooks/            # Tích hợp nền tảng
```

---

## Nguyên Tắc Cốt Lõi

### 1. Quy Tắc Phụ Thuộc
Phụ thuộc chỉ được trỏ **từ ngoài vào trong**:
- `interfaces` → `application` → `core`
- `infrastructure` → `core` (qua ports)
- **Không bao giờ**: `core` → `infrastructure`

### 2. Domain Độc Lập
- Entity trong `core/domain` không phụ thuộc DB, framework hay dịch vụ ngoài
- Dùng Pydantic models cho validation và serialization
- SQLAlchemy models chỉ nằm trong `infrastructure/database/models`

### 3. Async-First
- 100% async/await cho DB
- AsyncSession từ SQLAlchemy 2.0
- Background tasks cho logging và telemetry

---

## Kiến Trúc Điều Phối Hybrid

### HybridOrchestrator
**File**: `app/application/orchestrators/hybrid_orchestrator.py`

```python
async def handle_message(tenant_id, bot_id, message, session_id):
    # Tier 1: Fast Path (Regex)
    if self._check_social_patterns(message):
        return instant_response

    # Tier 2: Knowledge Path (Cache + FAQ)
    cached = await semantic_cache.search(message)
    if cached and confidence > 0.85:
        return cached_response

    # Tier 3: Agentic Path (LLM + Tools)
    return await agent_orchestrator.run(message, session_id, state, tenant_id)
```

**Trách nhiệm**:
- Chọn tier xử lý dựa trên độ phức tạp tin nhắn
- Quản lý vòng đời phiên
- Background logging (DecisionEvent, Turn)
- Theo dõi chi phí

=> **Điểm linh hoạt ăn tiền:** ~30% request đi Fast Path (cost $0), ~40% đi Knowledge (cost thấp), chỉ ~30% đi Agentic (cost cao). Tiết kiệm 50–70% chi phí LLM so với việc gọi AI cho mọi tin nhắn.

---

### AgentOrchestrator
**File**: `app/application/orchestrators/agent_orchestrator.py`

**Luồng chính**:
1. **Context Snapshotting**: Lấy slots active từ DB
2. **History Retrieval**: Load N lượt gần nhất
3. **Tool Filtering**: Lọc Tool theo trạng thái hiện tại (StateMachine)
4. **System Prompt**: Nhúng slots + hướng dẫn
5. **Reasoning Loop**: LLM → Gọi Tool → Observation → Response

**Tính năng**:
- Nhúng history vào LLM
- Nhúng context slots vào system prompt
- Thực thi Tool với fallback từ slots
- Quản lý chuyển trạng thái

---

## Quản Lý Trạng Thái (State Machine)

**File**: `app/core/domain/state_machine.py`

Định nghĩa Tool được phép cho mỗi lifecycle state:

```python
STATE_SKILL_MAP = {
    LifecycleState.IDLE: ["search_offerings", "compare_offerings", ...],
    LifecycleState.BROWSING: ["search_offerings", "get_offering_details", ...],
    LifecycleState.VIEWING: ["get_offering_details", "compare_offerings", ...],
    LifecycleState.COMPARING: ["compare_offerings", "get_offering_details", ...],
    LifecycleState.ANALYZING: ["get_market_data", "search_offerings", ...],
    LifecycleState.PURCHASING: ["trigger_web_hook", "search_offerings", ...],
    # ... 13 trạng thái tổng cộng
}
```

**Chuyển trạng thái hợp lệ**:
- IDLE → BROWSING, SEARCHING, ANALYZING
- BROWSING → VIEWING, IDLE
- VIEWING → COMPARING, PURCHASING, IDLE
- v.v. (xem VALID_TRANSITIONS)

---

## Hệ Thống Tool

### Đăng Ký Tool
**File**: `app/application/services/agent_tool_registry.py`

Dùng decorator pattern:

```python
@agent_tools.register_tool(
    name="search_offerings",
    description="Tìm sản phẩm...",
    capability="offering_search"
)
async def handle_search_offerings(query: str, **kwargs):
    # Implementation
```

### Handler Theo Ngành
**Vị trí**: `app/application/services/*_state_handler.py`

| Handler | Tool | Ngành |
|---------|------|-------|
| CatalogStateHandler | search, get_details, compare | Mọi ngành |
| FinancialStateHandler | get_market_data, strategic_analysis | Tài chính |
| AutoStateHandler | trade_in_valuation | Ô tô |
| EducationStateHandler | assessment_test | Giáo dục |
| IntegrationHandler | trigger_web_hook | Tích hợp CRM/PMS |

=> **Điểm linh hoạt ăn tiền:** Thêm ngành mới chỉ cần viết Handler mới và đăng ký Tool. Core Orchestrator không phải sửa.

---

## Luồng Dữ Liệu

### Request Flow
```
Client Request
  ↓
FastAPI Endpoint (interfaces/api)
  ↓
Middleware (Auth, Tenant Isolation)
  ↓
HybridOrchestrator (application/orchestrators)
  ↓ (nếu Agentic Path)
AgentOrchestrator
  ↓
ToolExecutor → StateHandler
  ↓
Repository (infrastructure/database)
  ↓
PostgreSQL
```

### Response Flow
```
Kết quả Tool
  ↓
AgentOrchestrator (định dạng response)
  ↓
HybridOrchestrator (_finalize_response)
  ↓
Background Tasks (logging, analytics)
  ↓
API Response → Client
```

---

## Multi-Tenancy

### Tenant Isolation
- Mọi query đều bắt buộc `tenant_id`
- Row-level security qua logic ứng dụng
- Middleware inject `tenant_id` từ JWT
- Repositories filter theo tenant

### Quản Lý Phiên
- Phiên gắn với Bot và Tenant
- Lịch sử hội thoại theo phiên
- Context slots theo phiên
- Trạng thái lưu theo phiên

---

## Tích Hợp LLM

### Kiến Trúc Provider
**Vị trí**: `app/infrastructure/llm/`

```python
class ILLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        system_prompt: str,
        user_message: str,
        tools: List[Dict],
        messages_history: List[Dict]
    ) -> Dict[str, Any]:
        pass
```

**OpenAIProvider**:
- Hỗ trợ conversation history
- Function calling (tools)
- Circuit breaker cho resilience
- Theo dõi token usage

---

## Quan Sát (Observability)

### Decision Logging
**Bảng**: `runtime_decision_event`

Ghi mọi quyết định:
- Decision type (FAST_PATH, KNOWLEDGE_PATH, AGENTIC_PATH)
- Lý do quyết định
- Chi phí ước tính
- Token usage
- Latency

### Phân Tích
- Chi phí theo phiên
- Token consumption theo tier
- Tần suất dùng Tool
- Phễu chuyển đổi

---

## Tối Ưu Hiệu Năng

### 1. Background Tasks
- Log Turn
- Ghi Decision event
- Cập nhật state
→ Không block API response

### 2. Vector Search
- pgvector với HNSW indexing
- Embedding tính sẵn
- Confidence thresholding

### 3. Caching
- Semantic cache cho query lặp
- Cache trạng thái phiên
- Cache kết quả Tool (kế hoạch)

---

**Trạng thái Tài liệu**: Phản ánh triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.
