# Architectural Review: App/ folder - Agentic Sales Platform

**Ngày review**: 18/02/2026  
**Phạm vi**: folder `app/` dựa trên tài liệu `backend_architecture.md`, `architectural_review.md`, `STATE_VS_AGENTIC_ARCHITECTURE.md`  
**Tiêu chuẩn**: Điểm A- (theo architectural_review.md)

---

## ✅ Cải thiện đã thực hiện (18/02/2026)

| Hạng mục | Thay đổi |
|----------|----------|
| **Core Interfaces** | `session_repo.py`, `knowledge_repo.py` → import domain entities thay vì infra models |
| **AgentOrchestrator** | Xóa duplicate `get_tool_metadata`, thay `print` bằng `logger` |
| **Domain Behavior** | `RuntimeSession`: `is_handover_mode()`, `is_active()`; `RuntimeContextSlot`: `is_active()`; `TenantOffering`: `is_purchasable()` |
| **Orchestrators** | `HybridOrchestrator` dùng `session_obj.is_handover_mode()`, `AgentOrchestrator` dùng `s.is_active()` cho slots |

---

## Tổng quan

Báo cáo này đánh giá code hiện tại theo 5 tiêu chí:
1. Tuân thủ Clean Architecture (Dependency Rule)
2. Tính 100% Async trong Database và API
3. Luồng Fast/Knowledge/Agentic trong Orchestrators
4. Anemic Domain Model
5. Chấm điểm và đề xuất cải thiện

---

## 1. Clean Architecture - Kiểm tra Dependency Rule

### Quy tắc theo tài liệu
> Dependencies chỉ được point inward: `interfaces` → `application` → `core`  
> **Không bao giờ**: `core` → `infrastructure`

### Vi phạm phát hiện

#### 1.1 Core layer import Infrastructure (Vi phạm nghiêm trọng)

| File | Import từ Infrastructure | Mô tả |
|------|--------------------------|-------|
| `core/services/catalog_service.py` | `app.infrastructure.database.repositories` (7 repos), `app.infrastructure.database.models.offering` | Core service phụ thuộc trực tiếp vào implementation |
| `core/services/migration_service.py` | `MigrationJobRepository`, `MigrationJob`, `MigrationJobStatus` từ infra | Domain service gọi repository cụ thể |
| `core/services/attribute_resolver.py` | `TenantAttributeConfigRepository`, `TenantOfferingAttributeValue`, `DomainAttributeDefinition`, `TenantAttributeConfig` | |
| `core/services/auth_service.py` | `UserAccount`, `UserAccountRepository` từ infra | |
| `core/services/inventory_extension.py` | `InventoryRepository`, `InventoryLocationRepository`, `TenantInventoryItem`, `TenantOfferingVariant` | |
| `core/services/ai_parser_service.py` | `app.infrastructure.llm.factory.get_llm_provider` | Core gọi trực tiếp LLM factory |
| `core/services/migration_providers.py` | `MigrationJob` từ infra models | |

#### 1.2 Core Interfaces import Infrastructure (Vi phạm)

**File**: `core/interfaces/knowledge_repo.py`
```python
from app.infrastructure.database.models.offering import (...)
from app.infrastructure.database.models.knowledge import (...)
```
→ Interface (port) không được phụ thuộc vào implementation. Nên dùng **domain entities** từ `core/domain/knowledge.py`.

**File**: `core/interfaces/session_repo.py`
```python
from app.infrastructure.database.models.runtime import RuntimeSession, RuntimeTurn, RuntimeContextSlot
```
→ Interface đang tham chiếu **SQLAlchemy models** thay vì **domain entities** (`app.core.domain.runtime`). Vi phạm quy tắc "core không biết infrastructure".

#### 1.3 Application layer
- `HybridOrchestrator`, `AgentOrchestrator` import trực tiếp `FAQRepository`, `DecisionRepository`, `ContextSlotRepository`, etc. từ infrastructure.
- Theo Clean Architecture chuẩn: Application có thể depend on interfaces (ports), infrastructure inject implementation. Hiện tại application đang **hard-code** dependency vào concrete repositories.

### Đánh giá Clean Architecture: **6/10** (Vi phạm đáng kể)

**Vấn đề chính**: Core layer bị "leak" – nhiều services trong core gọi trực tiếp infrastructure, làm mất tính độc lập domain và khó test.

---

## 2. Tính 100% Async

### Database Operations

| Component | Trạng thái | Ghi chú |
|-----------|------------|---------|
| Repositories (session_repo, faq_repo, offering_repo, ...) | 100% async | Tất cả method dùng `async def` và `await self.db.execute()` |
| SessionService | 100% async | `get_or_create_session`, `log_user_message`, `log_bot_response` đều async |
| CatalogService | 100% async | `get_offering_for_bot`, `search_offerings` đều async |
| HybridOrchestrator | 100% async | `handle_message`, `_finalize_response` async |
| AgentOrchestrator | 100% async | `run`, `_execute_orchestration` async |
| ToolExecutor | 100% async | `execute` async |

### API Endpoints

| Endpoint | Trạng thái |
|----------|------------|
| `POST /chat/message` | `async def chat_message` |
| `POST /chat/widget-message` | `async def widget_chat_message` |
| `get_session` (dependency) | AsyncSession từ `get_session` |

### Điểm cần kiểm tra

- `PriceService` (nếu có HTTP call): Nên dùng `httpx.AsyncClient` thay vì sync client.
- `ScrapingService` (Playwright): Đã dùng `async_playwright` – đúng hướng async.

### Đánh giá Async: **9/10** (Tốt)

**Ghi chú**: Nếu `PriceService` hoặc bất kỳ service nào dùng HTTP sync, cần chuyển sang async.

---

## 3. Logic điều phối - HybridOrchestrator & AgentOrchestrator

### 3.1 HybridOrchestrator - Luồng Fast → Knowledge → Agentic

**Mã nguồn** (`hybrid_orchestrator.py`):

```
1. Session management (get_or_create_session)
2. HANDOVER: Nếu state = handover → log & return (không LLM)
3. TIER 1 - Fast Path: _check_social_patterns(message) → nếu match → return ngay
   - Skip khi state = "purchasing" (hợp lý: không trả lời "xin chào" khi đang thanh toán)
4. TIER 2 - Knowledge Path: 
   - Skip khi state ∈ {viewing, comparing, purchasing, searching}
   - Semantic Cache → nếu hit → return
   - FAQ (chỉ khi idle/browsing) → nếu match → return
5. TIER 3 - Agentic Path: agent_orchestrator.run(...)
```

**Đánh giá**: Luồng đúng theo tài liệu. State-driven skip Tier 2 cho các state "nặng" là hợp lý.

### 3.2 AgentOrchestrator - Think-Act-Observe

**Mã nguồn** (`agent_orchestrator.py`):

```
1. Lưu user message (turn_repo.create)
2. _execute_orchestration:
   a. Context Snapshotting: slots_repo.get_by_session → context_snapshot
   b. History: turn_repo.get_by_session(limit=10) → history
   c. Bot context: session_repo, bot_repo
   d. Filter Tools: StateMachine.get_allowed_tools(state) ∩ bot_capabilities
   e. Intent extraction: intent_handler.extract_intent
   f. System prompt: inject context_slots, intent, allowed tools
   g. Reasoning Loop (max 3 turns):
      - LLM generate_response (tools, history)
      - Nếu có tool_calls → FlowDecisionService.can_execute_tool
      - ToolExecutor.execute
      - FlowDecisionService.decide_next_state
      - Observation → next message
3. Lưu bot response (turn_repo.create)
```

**Đánh giá**: 
- Đúng luồng Think → Act → Observe.
- State Machine constraint tools: `available_tools = [t for t in all_possible_tools if t["name"] in state_allowed_tools]`.
- FlowDecisionService validate tool execution và state transition.

**Ghi chú nhỏ**: Dòng duplicate `all_possible_tools = agent_tools.get_tool_metadata(...)` (lặp 2 lần) – nên xóa.

### Đánh giá Orchestration: **9/10** (Đúng luồng, logic rõ ràng)

---

## 4. Anemic Domain Model

Tài liệu `architectural_review.md` cảnh báo:
> "Some domain models are anemic (data-only, no behavior). Consider adding domain validation methods to entities."

### Các entity chỉ có data, thiếu behavior

| Entity | File | Mô tả |
|--------|------|-------|
| `KnowledgeDomain` | core/domain/knowledge.py | Chỉ fields (id, code, name, ...) |
| `TenantOffering` | core/domain/knowledge.py | Chỉ fields |
| `TenantOfferingVersion` | core/domain/knowledge.py | Chỉ fields |
| `TenantOfferingAttributeValue` | core/domain/knowledge.py | Chỉ fields |
| `Bot` | core/domain/bot.py | Chỉ fields |
| `BotVersion` | core/domain/bot.py | Chỉ fields |
| `RuntimeSession` | core/domain/runtime.py | Chỉ fields |
| `RuntimeTurn` | core/domain/runtime.py | Chỉ fields |
| `RuntimeContextSlot` | core/domain/runtime.py | Chỉ fields |
| `BotFAQ` | core/domain/knowledge.py | Chỉ fields |
| `BotUseCase` | core/domain/knowledge.py | Chỉ fields |
| `BotComparison` | core/domain/knowledge.py | Chỉ fields |
| `RuntimeDecisionEvent` | core/domain/decision.py | Chỉ fields |
| `LifecycleState`, `Intent` | core/domain/runtime.py | Enum – acceptable |

### Ngoại lệ có behavior

| Entity | File | Behavior |
|--------|------|----------|
| `StateMachine` | core/domain/state_machine.py | `get_allowed_tools()`, `is_transition_valid()` |
| `FlowDecisionService` | core/services/flow_decision_service.py | `can_execute_tool()`, `decide_next_state()`, `validate_transition()` |

### Ví dụ behavior nên thêm

1. **RuntimeSession**: 
   - `can_transition_to(new_state: LifecycleState) -> bool`
   - `is_handover_mode() -> bool`

2. **RuntimeContextSlot**:
   - `is_active() -> bool` (kiểm tra status)

3. **TenantOffering**:
   - `is_purchasable() -> bool` (status == ACTIVE và không archived)

4. **BotFAQ**:
   - `matches_query(query: str) -> bool` (nếu có logic so sánh đơn giản)

### Đánh giá Domain Model: **5/10** (Nhiều Anemic, cần bổ sung behavior)

---

## 5. Chấm điểm tổng thể và đề xuất

### Bảng điểm

| Tiêu chí | Điểm | Ghi chú |
|----------|------|---------|
| Clean Architecture | 6/10 | Core → Infrastructure violations |
| 100% Async | 9/10 | DB & API đều async |
| Orchestration Logic | 9/10 | Fast/Knowledge/Agentic đúng |
| Domain Model | 5/10 | Nhiều Anemic entities |
| **Trung bình** | **7.25/10** | |

### So với chuẩn A- (architectural_review.md)

Tài liệu đánh giá A- với:
- Clean separation of concerns
- 100% async
- Intelligent context management
- Tool system với state constraints
- Multi-tenant isolation

**Điểm hiện tại ước lượng: B+ ~ A-** (gần A- nhưng Clean Architecture cần cải thiện).

---

## Đề xuất cải thiện để đạt điểm A

### Ưu tiên 1 – Clean Architecture (Critical)

1. **Tách Core khỏi Infrastructure**
   - `CatalogService` → inject `IOfferingRepository`, `IOfferingVersionRepository`, ... qua constructor.
   - `AuthService` → inject `IUserAccountRepository` (interface trong core).
   - `MigrationService` → inject `IMigrationJobRepository`.
   - `AIParserService` → inject `ILLMProvider` (đã có interface).

2. **Sửa Core Interfaces**
   - `knowledge_repo.py`: Dùng `domain.BotFAQ`, `domain.TenantOffering`, ... thay vì infra models.
   - `session_repo.py`: Dùng `domain.RuntimeSession`, `domain.RuntimeTurn`, `domain.RuntimeContextSlot` thay vì infra models.

3. **Dependency Injection**
   - Wire repositories vào services ở `main.py` hoặc `dependencies.py`.
   - Application/Infrastructure chỉ inject vào Application layer; Core nhận interfaces qua constructor.

### Ưu tiên 2 – Rich Domain Model

4. **Thêm behavior cho entities**
   - `RuntimeSession`: `can_transition_to()`, `is_active()`.
   - `TenantOffering`: `is_purchasable()`.
   - `RuntimeContextSlot`: `is_active()`.

5. **Domain validation**
   - Pydantic validators trong entities cho business rules.
   - VD: `TenantOffering` không cho status chuyển trực tiếp DRAFT → ARCHIVED.

### Ưu tiên 3 – Code quality

6. **Xóa code trùng lặp**
   - `agent_orchestrator.py` dòng 117–118: xóa duplicate `get_tool_metadata`.

7. **Thay `print` bằng logger**
   - `agent_orchestrator.py`: thay `print("[AGENT-LOG]...")` bằng `self.logger.debug/info`.

### Ưu tiên 4 – Theo architectural_review.md

8. **Connection pooling** – cấu hình rõ pool size.
9. **Redis caching** – semantic cache, session state.
10. **Structured logging** – correlation ID, JSON format.
11. **Observability** – Prometheus metrics (đã có), thêm distributed tracing nếu cần.

---

## Kết luận

| Hạng | Điều kiện | Hiện tại |
|------|-----------|----------|
| **A** | Clean Arch đúng, Rich Domain, Async 100%, Orchestration đúng | Chưa đạt (Core → Infra violations) |
| **A-** | Gần như A, một số trade-off chấp nhận được | Gần đạt (Orchestration & Async tốt) |
| **B+** | Cấu trúc ổn, có vi phạm quan trọng | **≈ Hiện tại** |

**Hành động tiếp theo**: Ưu tiên sửa vi phạm Clean Architecture (Core → Infrastructure) và bổ sung behavior cho domain entities. Sau khi hoàn thành, dự án có thể tiến gần tới mức A.

---

**Người review**: AI Architect  
**Ngày**: 18/02/2026
