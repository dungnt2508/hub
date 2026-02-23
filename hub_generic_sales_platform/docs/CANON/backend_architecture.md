# Backend Architecture

## Overview

Agentic Sales Platform sử dụng **Clean Architecture** (Hexagonal Architecture) kết hợp với **100% Async** processing để đảm bảo khả năng mở rộng, bảo trì và hiệu năng cao.

## Layer Structure

```text
app/
├── core/                    # Layer 1: DOMAIN (Business Logic)
│   ├── config/              # Configuration management (Pydantic Settings)
│   ├── domain/              # Domain entities (Pydantic models)  
│   ├── interfaces/          # Ports (Abstract interfaces)
│   ├── services/            # Domain services (pure business logic)
│   └── shared/              # Shared utilities
│
├── application/             # Layer 2: APPLICATION (Use Cases)
│   ├── orchestrators/       # Workflow orchestration
│   │   ├── hybrid_orchestrator.py    # 3-tier processing logic
│   │   └── agent_orchestrator.py     # Agentic reasoning engine
│   └── services/            # Application services
│       ├── agent_tool_registry.py    # Tool registration
│       ├── catalog_state_handler.py  # Catalog operations
│       ├── slot_extractor.py         # Context extraction
│       └── session_state.py          # Session management
│
├── infrastructure/          # Layer 3: INFRASTRUCTURE (Technical Details)
│   ├── database/            
│   │   ├── models/          # SQLAlchemy ORM models
│   │   └── repositories/    # Data access implementation
│   ├── llm/                 # LLM provider adapters
│   │   ├── openai_provider.py
│   │   ├── circuit_breaker.py
│   │   └── factory.py
│   └── search/              # Vector search (pgvector)
│
└── interfaces/              # Layer 4: BOUNDARY (External interfaces)
    ├── api/                 # FastAPI REST endpoints
    ├── middleware/          # Auth, tenant isolation, logging
    └── webhooks/            # External platform integrations
```

## Core Principles

### 1. Dependency Rule
Dependencies chỉ được point inward (từ ngoài vào trong):
- `interfaces` → `application` → `core`
- `infrastructure` → `core` (through ports)
- **Không bao giờ**: `core` → `infrastructure`

### 2. Domain Independence
- Domain entities (`core/domain`) không phụ thuộc vào database, framework, hay external services
- Sử dụng Pydantic models cho validation và serialization
- SQLAlchemy models chỉ tồn tại trong `infrastructure/database/models`

### 3. Async-First
- 100% async/await cho database operations
- AsyncSession từ SQLAlchemy 2.0
- Background tasks cho logging và telemetry

## Hybrid Orchestration Architecture

### HybridOrchestrator
**File**: `app/application/orchestrators/hybrid_orchestrator.py`

```python
async def handle_message(tenant_id, bot_id, message, session_id):
    # Tier 1: Fast Path (Regex)
    if self._check_social_patterns(message):
        return instant_response
    
    # Tier 2: Knowledge Path (Semantic Cache + FAQ)
    cached = await semantic_cache.search(message)
    if cached and confidence > 0.85:
        return cached_response
    
    # Tier 3: Agentic Path (LLM + Tools)
    return await agent_orchestrator.run(message, session_id, state, tenant_id)
```

**Responsibilities**:
- Quyết định processing tier dựa trên message complexity
- Quản lý session lifecycle
- Background logging (DecisionEvent, ConversationTurn)
- Cost tracking

### AgentOrchestrator
**File**: `app/application/orchestrators/agent_orchestrator.py`

**Core Flow**:
1. **Context Snapshotting**: Lấy active slots từ database
2. **History Retrieval**: Load last N turns từ conversation history
3. **Tool Filtering**: Filter tools based on current state (StateMachine)
4. **System Prompt Construction**: Inject slots + instructions
5. **Reasoning Loop**: LLM → Tool Call → Observation → Response

**Key Features**:
- History injection vào LLM messages
- Context slot injection vào system prompt
- Tool execution với fallback to slots
- State transition management

## State Management

### StateMachine
**File**: `app/core/domain/state_machine.py`

Định nghĩa allowed tools cho mỗi lifecycle state:

```python
STATE_SKILL_MAP = {
    LifecycleState.IDLE: ["search_offerings", "compare_offerings", ...],
    LifecycleState.BROWSING: ["search_offerings", "get_offering_details", ...],
    LifecycleState.VIEWING: ["get_offering_details", "compare_offerings", ...],
    LifecycleState.COMPARING: ["compare_offerings", "get_offering_details", ...],
    LifecycleState.ANALYZING: ["get_market_data", "search_offerings", ...],
    LifecycleState.PURCHASING: ["trigger_web_hook", "search_offerings", ...],
}
```

**Valid Transitions**:
- IDLE → BROWSING, ANALYZING
- BROWSING → VIEWING, IDLE
- VIEWING → COMPARING, PURCHASING, IDLE
- etc.

## Tool System

### Tool Registration
**File**: `app/application/services/agent_tool_registry.py`

Sử dụng decorator pattern:

```python
@agent_tools.register_tool(
    name="search_offerings",
    description="Tìm sản phẩm...",
    capability="offering_search"
)
async def handle_search_offerings(query: str, **kwargs):
    # Implementation
```

### Tool Handlers
**Location**: `app/application/services/*_state_handler.py`

- **CatalogStateHandler**: search, get_details, compare
- **FinancialStateHandler**: get_market_data, strategic_analysis
- **AutoStateHandler**: trade_in_valuation
- **EducationStateHandler**: assessment_test
- **IntegrationHandler**: trigger_web_hook

## Data Flow

### Request Flow
```
Client Request
  ↓
FastAPI Endpoint (interfaces/api)
  ↓
Middleware (Auth, Tenant Isolation)
  ↓
HybridOrchestrator (application/orchestrators)
  ↓ (if Agentic Path)
AgentOrchestrator
  ↓
ToolExecutor → StateHandler
  ↓
Repository (infrastructure/database)
  ↓
PostgreSQL
```

### Response Construction
```
Tool Result
  ↓
AgentOrchestrator (format response)
  ↓
HybridOrchestrator (_finalize_response)
  ↓
Background Tasks (logging, analytics)
  ↓
API Response → Client
```

## Multi-Tenancy

### Tenant Isolation
- Mọi query đều require `tenant_id`
- Row-level security qua application logic
- Middleware inject `tenant_id` từ JWT token
- Repositories enforce tenant filtering

### Session Management
- Session mapping to Bot và Tenant
- Conversation history scoped to session
- Context slots scoped to session
- State persistence per session

## LLM Integration

### Provider Architecture
**Location**: `app/infrastructure/llm/`

```python
class ILLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        system_prompt: str,
        user_message: str,
        tools: List[Dict],
        messages_history: List[Dict]  # NEW: History support
    ) -> Dict[str, Any]:
        pass
```

### OpenAIProvider Implementation
- Supports conversation history
- Function calling (tools)
- Circuit breaker pattern for resilience
- Token usage tracking

## Observability

### Decision Logging
**Table**: `runtime_decision_events`

Ghi lại mọi quyết định của hệ thống:
- Decision type (FAST_PATH, KNOWLEDGE_PATH, AGENTIC_PATH)
- Decision reason
- Estimated cost
- Token usage
- Latency

### Analytics
- Cost per session
- Token consumption by tier
- Tool usage frequency
- Conversion funnel

## Performance Optimizations

### 1. Background Tasks
- Turn logging
- Decision event recording
- State updates
→ Không block API response

### 2. Vector Search
- pgvector với HNSW indexing
- Pre-computed embeddings
- Confidence thresholding

### 3. Caching Strategy
- Semantic cache cho repeated queries
- Session state caching
- Tool result caching (planned)

---

**Architecture Status**: Production-grade foundation, optimized for scale  
**Last Updated**: February 2026
