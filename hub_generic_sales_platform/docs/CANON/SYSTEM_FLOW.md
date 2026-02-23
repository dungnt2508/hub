# System Flow

## Overview

Tài liệu này mô tả luồng xử lý chi tiết của Agentic Sales Platform từ khi nhận request đến khi trả response.

## High-Level Flow

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

## Detailed Flows

### 1. Request Entry Flow

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

### 2. Hybrid Orchestration Flow

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

### 3. Agentic Processing Flow

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
    
    Note over Agent: Phase 3: System Prompt Construction
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

### 4. Tool Execution Flow

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

### 5. Context Slot Management Flow

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
    
    Note over Agent: Next Turn
    User->>Agent: "Giá bao nhiêu?"
    Agent->>DB: Get active slots for session
    DB-->>Agent: {color: "đỏ", product_type: "xe"}
    
    Agent->>Agent: Inject slots into system_prompt<br/>"CONTEXT: color=đỏ, product_type=xe"
    Agent->>LLM: generate_response(prompt with context)
    LLM-->>Agent: "Xe màu đỏ có giá..."
```

## Key Design Decisions

### 1. Why 3-Tier Processing?

**Cost Optimization**:
- Tier 1 (Fast Path): Xử lý ~30% requests với cost = $0
- Tier 2 (Knowledge): Xử lý ~40% requests với cost < $0.01
- Tier 3 (Agentic): Chỉ ~30% requests tốn cost cao

**Latency Optimization**:
- Fast Path: < 50ms (no network calls)
- Knowledge Path: < 500ms (local vector search)
- Agentic: Variable (AI reasoning)

### 2. Why Separate AgentOrchestrator?

**Separation of Concerns**:
- HybridOrchestrator: Routing logic (which tier?)
- AgentOrchestrator: Reasoning logic (how to reason?)

**Testability**:
- Có thể unit test Agent logic độc lập
- Mock LLM responses dễ dàng

### 3. Why State Machine?

**Safety**:
- Prevent invalid tool usage (e.g., không thể "purchase" khi chưa "view")
- Guided user journey

**Context Scoping**:
- Mỗi state có ý nghĩa business rõ ràng
- Tools được filter theo state để giảm token cost

### 4. Why Background Tasks?

**Performance**:
- Không block API response
- Logging diễn ra async

**Resilience**:
- Nếu logging fail, không ảnh hưởng user experience

## Performance Characteristics

### Latency Breakdown (P95)

| Tier | Latency | Components |
|------|---------|-----------|
| Fast Path | 10-50ms | Pattern matching + DB session lookup |
| Knowledge Path | 100-500ms | Vector search (pgvector) + Confidence scoring |
| Agentic Path | 1-5s | LLM inference (500-2000ms) + Tool execution (200-1000ms) + DB ops |

### Token Usage (Typical Conversation)

| Component | Tokens | Notes |
|-----------|--------|-------|
| System Prompt | 200-400 | Base instructions + domain knowledge |
| Context Slots | 50-100 | Injected user context |
| Conversation History | 300-800 | Last 10 turns (smart truncation) |
| Tool Definitions | 400-600 | Function calling schemas |
| User Message | 10-100 | Actual query |
| **Total Input** | **~1500** | Per agentic request |
| LLM Response | 100-300 | Natural language + function call |

---

**Documents Liên Quan**:
- [SIDEBAR_MAPPING_TABLE.md](../knowledge/pages/SIDEBAR_MAPPING_TABLE.md)
- [INTENT_USAGE_POLICY.md](../knowledge/INTENT_USAGE_POLICY.md)

**Flow Documentation**: Reflects production implementation  
**Last Updated**: February 2026
```
