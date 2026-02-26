# Luồng Hệ Thống (System Flow)

## Tổng Quan

Tài liệu mô tả **luồng xử lý** chi tiết của Agentic Sales Platform từ khi nhận request đến khi trả response.

---

## Luồng Tổng Quan

```
Client Request
    ↓
[API Layer] FastAPI Endpoint
    ↓
[Middleware] Auth + Tenant Isolation
    ↓
[Orchestration] HybridOrchestrator
    ├→ [Tier 1] Fast Path (Regex) → Response
    ├→ [Tier 2] Knowledge Path (Cache/FAQ) → Response
    └→ [Tier 3] Agentic Path → AgentOrchestrator → Response
    ↓
[Logging] Background Tasks (Decision, Turn, Analytics)
    ↓
Client Response
```

=> **Điểm linh hoạt ăn tiền:** Hệ thống không "ném" mọi tin nhắn vào LLM. Tier 1 xử lý chào hỏi nhanh $0. Tier 2 trả FAQ/cache rẻ. Chỉ tin phức tạp mới vào Tier 3 - tiết kiệm token và chi phí.

---

## Luồng Chi Tiết

### 1. Luồng Vào Request

```mermaid
sequenceDiagram
    participant Client as Client (Web/Zalo/FB)
    participant API as FastAPI Endpoint
    participant Auth as AuthMiddleware
    participant Hybrid as HybridOrchestrator

    Client->>API: POST /api/chat/message
    API->>Auth: Validate JWT Token
    Auth->>Auth: Extract tenant_id, user_id
    Auth-->>API: Request State populated
    API->>Hybrid: handle_message(tenant_id, bot_id, message)
    Hybrid-->>API: Response + UI Data
    API-->>Client: JSON Response
```

---

### 2. Luồng Điều Phối Hybrid

```mermaid
graph TD
    Start[Incoming Message] --> GetSession[Get/Create Session]
    GetSession --> GetState[Get Current State]

    GetState --> Tier1{Fast Path Check}
    Tier1 -->|Social Pattern Match| FastResponse[Instant Response]
    Tier1 -->|No Match| Tier2{Knowledge Path}

    Tier2 -->|Semantic Cache Hit| CacheResponse[Cached Response]
    Tier2 -->|FAQ Match High Confidence| FAQResponse[FAQ Response]
    Tier2 -->|No Match or Low Confidence| Tier3[Agentic Path]

    Tier3 --> AgentOrch[AgentOrchestrator.run]

    FastResponse --> Finalize[_finalize_response]
    CacheResponse --> Finalize
    FAQResponse --> Finalize
    AgentOrch --> Finalize

    Finalize --> Background[Background Tasks]
    Background --> LogTurn[Log ConversationTurn]
    Background --> LogDecision[Log DecisionEvent]
    Background --> UpdateState[Update Session State]

    Finalize --> End[Return Response]
```

---

### 3. Luồng Xử Lý Agentic

```mermaid
sequenceDiagram
    participant Hybrid as HybridOrchestrator
    participant Agent as AgentOrchestrator
    participant Context as ContextSnapshotting
    participant History as ConvHistory
    participant SM as StateMachine
    participant LLM as LLM Provider
    participant Tools as ToolExecutor
    participant DB as Database

    Hybrid->>Agent: run(message, session_id, state, tenant_id)

    Note over Agent: Phase 1: Context Preparation
    Agent->>Context: Get active slots
    Context->>DB: SELECT * FROM context_slots WHERE session_id...
    DB-->>Context: List[RuntimeContextSlot]
    Context-->>Agent: context_snapshot: Dict

    Agent->>History: Get recent turns
    History->>DB: SELECT * FROM conversation_turns LIMIT 10
    DB-->>History: List[ConversationTurn]
    History-->>Agent: history: List[Dict]

    Note over Agent: Phase 2: Tool Filtering
    Agent->>SM: get_allowed_tools(current_state)
    SM-->>Agent: allowed_tool_names: List[str]

    Note over Agent: Phase 3: System Prompt
    Agent->>Agent: Build system_prompt<br/>+ Inject context_slots<br/>+ Add tool instructions

    Note over Agent: Phase 4: Reasoning Loop (max 3 turns)
    loop Until Response or Max Turns
        Agent->>LLM: generate_response(system_prompt, message, tools, history)
        LLM-->>Agent: response + tool_calls

        alt Has Tool Calls
            Agent->>Tools: execute(tool_name, args, context_slots)
            Tools->>DB: Tool-specific operations
            DB-->>Tools: Tool results
            Tools-->>Agent: ExecutionResult
            Agent->>SM: decide_next_state(current_state, tool_name, result)
            SM-->>Agent: new_state
            Agent->>Agent: Update system_prompt with observation
        else No Tool Calls
            Agent-->>Hybrid: Final Response
        end
    end

    Agent-->>Hybrid: {response, usage, g_ui_data, new_state}
```

---

### 4. Luồng Thực Thi Tool

```mermaid
graph TD
    Start[Tool Call Requested] --> Validate{Tool Allowed?}

    Validate -->|Yes| GetHandler[Get Tool Handler]
    Validate -->|No| Error[Return Error: Tool not allowed]

    GetHandler --> ParseArgs[Parse Tool Arguments]
    ParseArgs --> CheckSlots{Arguments Missing?}

    CheckSlots -->|Yes| FallbackSlots[Fallback to Context Slots]
    CheckSlots -->|No| Execute[Execute Tool]
    FallbackSlots --> Execute

    Execute --> Handler{Handler Type}
    Handler -->|Catalog| CatalogHandler[CatalogStateHandler]
    Handler -->|Financial| FinancialHandler[FinancialStateHandler]
    Handler -->|Auto| AutoHandler[AutoStateHandler]
    Handler -->|Integration| IntegrationHandler[IntegrationHandler]

    CatalogHandler --> DBQuery[Query Database]
    FinancialHandler --> ExternalAPI[Call External API]
    AutoHandler --> Calculation[Perform Calculation]
    IntegrationHandler --> Webhook[Trigger Webhook]

    DBQuery --> Result[Format Result]
    ExternalAPI --> Result
    Calculation --> Result
    Webhook --> Result

    Result --> StateChange{Valid Transition?}
    StateChange -->|Service Decision| UpdateState[Update Session State]
    StateChange -->|No Transition| Return[Return ExecutionResult]
    UpdateState --> Return

    Error --> Return
    Return --> End[End]
```

---

### 5. Luồng Quản Lý Context Slots

```mermaid
sequenceDiagram
    participant User as User Message
    participant Agent as AgentOrchestrator
    participant Extractor as SlotExtractor
    participant LLM as LLM Provider
    participant DB as Database

    User->>Agent: "Tôi muốn xe màu đỏ"
    Agent->>Extractor: extract_slots(message)

    Extractor->>LLM: "Extract entities: color, product_type, etc."
    LLM-->>Extractor: {color: "đỏ", product_type: "xe"}

    Extractor->>DB: UPSERT context_slots
    DB-->>Extractor: Slots saved

    Note over Agent: Lượt tiếp theo
    User->>Agent: "Giá bao nhiêu?"
    Agent->>DB: Get active slots for session
    DB-->>Agent: {color: "đỏ", product_type: "xe"}

    Agent->>Agent: Inject slots vào system_prompt<br/>"CONTEXT: color=đỏ, product_type=xe"
    Agent->>LLM: generate_response(prompt with context)
    LLM-->>Agent: "Xe màu đỏ có giá..."
```

=> **Điểm linh hoạt ăn tiền:** Khách không cần lặp lại "xe màu đỏ" mỗi câu. Bot nhớ qua slots. Hội thoại tự nhiên hơn, token ít hơn.

---

## Quyết Định Thiết Kế Chủ Chốt

### 1. Tại sao 3 Tier?

**Tối ưu chi phí**:
- Tier 1 (Fast Path): Xử lý ~30% request với cost = $0
- Tier 2 (Knowledge): ~40% với cost < $0.01
- Tier 3 (Agentic): Chỉ ~30% cost cao

**Tối ưu độ trễ**:
- Fast Path: < 50ms (không gọi mạng)
- Knowledge Path: < 500ms (vector search local)
- Agentic: Biến động (AI reasoning)

---

### 2. Tại sao tách AgentOrchestrator?

**Phân tách trách nhiệm**:
- HybridOrchestrator: Logic routing (tier nào?)
- AgentOrchestrator: Logic suy luận (suy luận thế nào?)

**Testability**:
- Test logic Agent độc lập
- Mock LLM dễ dàng

---

### 3. Tại sao State Machine?

**An toàn**:
- Ngăn dùng Tool sai (vd: không "purchase" khi chưa "view")
- Hành trình khách được dẫn dắt

**Giới hạn ngữ cảnh**:
- Mỗi state có ý nghĩa nghiệp vụ rõ
- Tool được filter theo state → giảm token

---

### 4. Tại sao Background Tasks?

**Hiệu năng**:
- Không block API response
- Logging chạy async

**Resilience**:
- Logging fail không ảnh hưởng trải nghiệm user

---

## Đặc Tính Hiệu Năng

### Độ trễ (P95)

| Tier | Latency | Thành phần |
|------|---------|------------|
| Fast Path | 10–50ms | Pattern matching + DB session lookup |
| Knowledge Path | 100–500ms | Vector search (pgvector) + confidence |
| Agentic Path | 1–5s | LLM inference (500–2000ms) + Tool (200–1000ms) + DB |

### Token dùng (hội thoại điển hình)

| Thành phần | Tokens | Ghi chú |
|------------|--------|---------|
| System Prompt | 200–400 | Base + domain knowledge |
| Context Slots | 50–100 | Context nhúng |
| Conversation History | 300–800 | 10 lượt gần nhất |
| Tool Definitions | 400–600 | Function calling schemas |
| User Message | 10–100 | Câu hỏi thực tế |
| **Tổng Input** | **~1500** | Mỗi request agentic |
| LLM Response | 100–300 | Text + function call |

---

**Tài liệu liên quan**:
- [SIDEBAR_MAPPING_TABLE.md](../knowledge/pages/SIDEBAR_MAPPING_TABLE.md)
- [INTENT_USAGE_POLICY.md](../knowledge/INTENT_USAGE_POLICY.md)

**Trạng thái Tài liệu**: Phản ánh triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.
