# System Architecture

## Overview

Bot V2 là một hệ thống chatbot đa-tenant được thiết kế với nguyên tắc:
- **Deterministic**: Hành vi xác định, không đoán mò
- **Auditable**: Mọi câu trả lời đều có thể truy vết về nguồn dữ liệu
- **No Hallucination**: Không tạo ra thông tin không có trong database
- **Controlled Knowledge**: Hệ thống kiến thức có kiểm soát, không phải AI chat tự do

## Architecture Layers

### 1. API Layer (FastAPI)

**Routers:**
- `bot.py`: Public API cho chatbot queries
- `admin.py`: Admin API cho dashboard

**Schemas:**
- `schemas/bot.py`: Bot API request/response schemas
- `schemas/admin.py`: Admin API response schemas
- `schemas/converters.py`: Domain objects → Schema converters

**Responsibilities:**
- Request validation (Pydantic schemas)
- Authentication/Authorization (tenant isolation)
- Response formatting (domain → schema conversion)
- Error handling

### 2. Domain Layer

**Domain Objects:**
- `domain/tenant.py`: Tenant, TenantSecret, Channel
- `domain/catalog.py`: Product, ProductAttribute, UseCase, FAQ, Comparison, Guardrail
- `domain/intent.py`: Intent, IntentPattern, IntentHint, IntentAction
- `domain/migration.py`: MigrationJob, MigrationVersion
- `domain/observability.py`: ConversationLog, FailedQuery

**Characteristics:**
- Pure Python objects (no Pydantic)
- Business logic objects
- Independent of API layer
- Used throughout service layer

### 3. Service Layer

**Orchestration:**
- `BotService`: Main orchestrator (chỉ điều phối, không xử lý nghiệp vụ)
- `DomainHandlerService`: Routes to appropriate domain services

**Routing & Intent:**
- `RoutingService`: Intent routing (pattern matching + optional LLM)
- `IntentService`: Intent action execution

**Domain Services (tách riêng từng domain):**
- `ProductService`: Product queries
- `FAQService`: FAQ queries
- `UseCaseService`: Suitability queries
- `ComparisonService`: Product comparison

**Support Services:**
- `GuardrailService`: Safety checks (uses GuardrailPolicy)
- `MigrationService`: Data migration jobs

**Responsibilities:**
- Business logic
- Orchestration
- Domain-specific handlers
- **Không query DB trực tiếp** (delegate to repositories)
- **Không chứa API schemas** (dùng domain objects)

### 4. Policy Layer

**Policies:**
- `policies/guardrail_policy.py`: Guardrail enforcement rules

**Responsibilities:**
- Business rules và policies
- Tách biệt khỏi service logic
- Reusable across services

### 5. Context Layer

**Contexts:**
- `contexts/request_context.py`: RequestContext object

**Responsibilities:**
- Type-safe context passing
- Chứa: tenant_id, channel_id, query_text, intent_name, domain, action_config
- Thay thế việc truyền dict lung tung

### 6. Error Layer

**Custom Exceptions:**
- `errors/domain_errors.py`:
  - `IntentNotFoundError`
  - `GuardrailViolationError`
  - `DataNotFoundError`
  - `NoActionConfiguredError`

**Responsibilities:**
- Standardized error handling
- Tránh if-else rải rác
- Clear error semantics

### 7. Repository Layer

**Repositories:**
- `TenantRepository`
- `CatalogRepository`
- `IntentRepository`
- `MigrationRepository`
- `ObservabilityRepository`

**Responsibilities:**
- Data access
- Tenant isolation (enforced at query level)
- SQL query execution
- **Trả về domain objects** (không phải Pydantic models)
- **Không gọi LLM**

### 8. Database Layer

**PostgreSQL với schema:**
- Core platform tables
- Catalog/knowledge tables (read-only runtime)
- Intent/routing tables
- Migration/versioning tables
- Observability tables

**Principles:**
- Single source of truth
- Read-only runtime tables (catalog)
- Tenant isolation via tenant_id
- No inference, only explicit data

## Data Flow

### Query Processing Flow

```
API Router
    │
    ▼ (Request → QueryRequest schema)
[BotService - Orchestrator]
    │
    ▼ (Create RequestContext)
[GuardrailService]
    │
    ├─ GuardrailPolicy.check_query()
    │
    ├─ Violated? → Raise GuardrailViolationError
    │
    └─ Passed → Continue
        │
        ▼
[RoutingService]
    │
    ├─ Pattern Matching (shortlist intents)
    │
    ├─ Multiple candidates? → LLM Resolution (optional)
    │   └─ LLM chỉ chọn intent_id từ DB
    │
    └─ Intent Selected (domain object)
        │
        ▼
[IntentService]
    │
    ├─ Get Actions (by priority)
    │
    └─ Execute First Action
        │
        ├─ query_db → DomainHandlerService
        │   │
        │   ├─ ProductService (product info, price)
        │   ├─ FAQService (FAQ answers)
        │   ├─ UseCaseService (suitability)
        │   └─ ComparisonService (product comparison)
        │
        ├─ handoff → CTA
        │
        ├─ refuse → Refusal Message
        │
        └─ rag → (Not implemented)
            │
            ▼
[Response Assembly]
    │
    ▼ (Domain objects → Schemas via converters)
[Logging]
    │
    ├─ ConversationLog (domain object)
    └─ FailedQuery (if failed)
        │
        ▼
Response to User (QueryResponse schema)
```

### Layer Separation

```
API Layer (Schemas)
    ↕ converters
Domain Layer (Pure Objects)
    ↕
Service Layer (Business Logic)
    ↕
Repository Layer (Data Access)
    ↕
Database Layer
```

## Tenant Isolation

Tenant isolation được enforce ở mọi layer:

1. **API Layer**: Extract tenant_id từ header
2. **Service Layer**: Pass tenant_id to repositories
3. **Repository Layer**: Add `WHERE tenant_id = :tenant_id` to all queries
4. **Database Layer**: Index on tenant_id for performance

## Intent Resolution

### Pattern Matching (Shortlist)

1. Query `intent_patterns` table
2. Match patterns:
   - `keyword`: Simple keyword matching
   - `phrase`: Phrase matching
   - `regex`: Regular expression matching
3. Return intents with matching patterns

### LLM Resolution (Optional)

1. If multiple candidates after pattern matching
2. Get `intent_hints` for all candidates
3. Build prompt with hints
4. Call LLM to choose intent
5. Match LLM response to intent name
6. Fallback to highest priority if no match

**Important**: LLM chỉ dùng để chọn intent từ database, KHÔNG tạo intent mới.

## Domain Handlers

Domain handlers được tách thành các service riêng biệt, mỗi service chỉ phụ trách 1 domain:

### ProductService

- **Methods**:
  - `get_product_info()`: Get product với attributes
  - `get_price()`: Get product price
- **Source**: `products` + `product_attributes` tables
- **No reasoning**: Chỉ trả về data có sẵn
- **No guessing**: Nếu không có → raise `DataNotFoundError`
- **Returns**: Domain objects hoặc dict

### FAQService

- **Methods**:
  - `get_faq_answer()`: Match question với FAQ
- **Source**: `faqs` table
- **Scope**: global or product-specific
- **Matching**: Keyword matching với question
- **Returns**: FAQ answer dict hoặc None

### UseCaseService

- **Methods**:
  - `check_suitability()`: Check product suitability
- **Source**: `use_cases` table
- **Matching**: Keyword matching với use case description
- **Result**: allowed/disallowed/unknown dict

### ComparisonService

- **Methods**:
  - `compare_products()`: Compare two products
- **Source**: `comparisons` table
- **Requirement**: Comparison phải được khai báo trước
- **Filtering**: Chỉ so sánh attributes trong `allowed_attributes`
- **Raises**: `DataNotFoundError` nếu comparison không allowed

### DomainHandlerService

- **Responsibilities**:
  - Route query_db actions to appropriate domain service
  - Handle intent → domain service mapping
  - Fallback to FAQ if no specific handler matches
- **Does NOT**: Query database directly, process business logic

## Guardrails

Guardrails được check TRƯỚC khi xử lý query:

1. `GuardrailService` loads guardrail cho tenant (domain object)
2. `GuardrailPolicy.check_query()` enforces rules
3. If violation → raise `GuardrailViolationError` với fallback_message
4. If passed → continue processing

**Separation of Concerns:**
- `GuardrailService`: Service layer, loads data
- `GuardrailPolicy`: Policy layer, enforces rules
- Rules tách biệt khỏi service logic, dễ thay đổi

## Migration System

Migration jobs chạy async:

1. Create job với status "pending"
2. Background worker picks up job
3. Update status to "processing"
4. Process based on `source_type`:
   - excel: Parse Excel file
   - cms: Import from CMS
   - crawl: Web crawling
   - ai: AI-generated content
5. Update status to "completed" or "failed"

Migration versions:
- Track approved versions
- Only approved versions are used in runtime

## Observability

### Conversation Logs

Log mọi query:
- tenant_id
- channel_id
- intent (if matched)
- domain
- success/failure
- timestamp

### Failed Queries

Log queries that failed:
- tenant_id
- query text
- reason (no intent matched, guardrail violation, etc.)
- timestamp

## Error Handling

Error handling sử dụng custom exceptions để tránh if-else rải rác:

### Custom Exceptions

- `IntentNotFoundError`: Không tìm thấy intent phù hợp
- `GuardrailViolationError`: Query vi phạm guardrails (có fallback_message)
- `DataNotFoundError`: Data không tồn tại trong database
- `NoActionConfiguredError`: Intent không có action được cấu hình

### Error Flow

**No Intent Matched:**
- `RoutingService` returns None
- `BotService` raises `IntentNotFoundError`
- Log to `failed_queries` và `conversation_logs`
- Return generic refusal message

**Guardrail Violation:**
- `GuardrailPolicy` detects violation
- `GuardrailService` raises `GuardrailViolationError`
- `BotService` catches và return fallback_message
- Log to `conversation_logs` với success=false

**Missing Data:**
- Domain services raise `DataNotFoundError`
- `DomainHandlerService` catches và return None
- Do NOT guess or infer
- Log if appropriate

**No Action Configured:**
- `IntentService` returns empty actions list
- `BotService` raises `NoActionConfiguredError`
- Log và return error message

## Architecture Principles

### Separation of Concerns

1. **Domain vs Schemas**: 
   - Domain objects (pure Python) cho business logic
   - Schemas (Pydantic) cho API contracts
   - Converters để chuyển đổi

2. **Service Separation**:
   - Mỗi service chỉ phụ trách 1 domain
   - BotService chỉ điều phối, không xử lý nghiệp vụ
   - DomainHandlerService routes, không query DB

3. **Policy Separation**:
   - Rules tách biệt khỏi service logic
   - Policies reusable và dễ thay đổi

4. **Context Management**:
   - RequestContext thay thế dict
   - Type-safe context passing

### Forbidden Patterns

❌ **Repository gọi LLM**
❌ **Service trả về raw SQL result**
❌ **Router chứa logic nghiệp vụ**
❌ **LLM query DB trực tiếp**
❌ **Chat history làm input domain logic**
❌ **Service layer lệ thuộc API schemas**
❌ **God Object (service quá lớn)**

### Allowed Patterns

✅ **Repository trả về domain objects**
✅ **Service dùng domain objects**
✅ **Router dùng schemas (qua converters)**
✅ **LLM chỉ chọn intent_id từ DB**
✅ **BotService chỉ điều phối**
✅ **Mỗi service 1 domain**
✅ **Policies tách biệt**

## Performance Considerations

1. **Indexing**: Index on tenant_id, foreign keys
2. **Connection Pooling**: SQLAlchemy async pool
3. **Caching**: (Future) Cache tenant configs, intents
4. **Async Operations**: Background workers for migrations
5. **Domain Objects**: Lightweight, no ORM overhead

## Security

1. **Tenant Isolation**: Enforced at database level
2. **Secrets**: Stored encrypted in `tenant_secrets`
3. **API Keys**: Validate via headers
4. **Input Validation**: Pydantic models

## Scalability

1. **Horizontal Scaling**: Stateless services
2. **Database**: Read replicas for queries
3. **Background Jobs**: Separate worker processes
4. **Caching**: Redis for tenant configs (future)
5. **Service Isolation**: Mỗi domain service có thể scale riêng

## Code Organization

```
backend/
├── domain/              # Pure business objects (no Pydantic)
│   ├── tenant.py
│   ├── catalog.py
│   ├── intent.py
│   ├── migration.py
│   └── observability.py
├── schemas/             # Pydantic models (API contracts)
│   ├── bot.py
│   ├── admin.py
│   └── converters.py   # Domain → Schema conversion
├── repositories/        # Data access (returns domain objects)
│   ├── tenant_repository.py
│   ├── catalog_repository.py
│   ├── intent_repository.py
│   ├── migration_repository.py
│   └── observability_repository.py
├── services/           # Business logic
│   ├── bot_service.py           # Orchestrator only
│   ├── domain_handler_service.py # Routes to domain services
│   ├── routing_service.py
│   ├── intent_service.py
│   ├── product_service.py        # Product domain
│   ├── faq_service.py            # FAQ domain
│   ├── use_case_service.py       # Suitability domain
│   ├── comparison_service.py      # Comparison domain
│   ├── guardrail_service.py
│   └── migration_service.py
├── policies/           # Business rules
│   └── guardrail_policy.py
├── contexts/           # Runtime contexts
│   └── request_context.py
├── errors/             # Custom exceptions
│   └── domain_errors.py
└── routers/            # API endpoints (uses schemas)
    ├── bot.py
    └── admin.py
```