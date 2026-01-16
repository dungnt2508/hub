# BÁO CÁO AUDIT KIẾN TRÚC CHATBOT

**Ngày audit:** 2025-01-16  
**Phạm vi:** Router Orchestrator → Domain Engines → Session Management  
**Phương pháp:** Code review + Flow analysis

---

## A. KẾT LUẬN NGẮN: **NỬA VỜI**

**Lý do:**
- Router chạy đúng 1 lần ở entry point ✅
- Domain routing tách biệt rõ ràng ✅
- Session được load nhưng **KHÔNG được persist sau domain response** ❌
- Slot extraction có nhưng **KHÔNG merge vào session** ❌
- Thiếu state machine cho conversation flow ❌
- UNKNOWN handling mơ hồ, không có recovery path ❌

---

## B. LỖI NGHIÊM TRỌNG (BLOCKING ISSUES)

### B1. Session State Không Được Persist Sau Domain Response

**Vị trí:** `backend/interface/api_handler.py:107-115`, `backend/router/orchestrator.py:61-173`

**Vấn đề:**
- Router load session ở STEP 0 (`_step_0_session`)
- Domain xử lý và trả về `NEED_MORE_INFO` với `missing_slots`
- **Session KHÔNG được update với:**
  - `active_domain` (domain hiện tại đang xử lý)
  - `last_domain` (domain vừa route)
  - `pending_intent` (intent đang chờ slots)
  - `missing_slots` (slots còn thiếu)
  - `slots_memory` (slots đã extract)

**Hậu quả:**
- Request tiếp theo không biết đang trong flow nào
- User phải nhập lại toàn bộ thông tin
- Không thể resume conversation

**Code hiện tại:**
```python
# api_handler.py:107
router_response = await self.router.route(request)

# domain_dispatcher.py:123
domain_response = await handler.handle(domain_request)

# ❌ KHÔNG CÓ CODE UPDATE SESSION Ở ĐÂY
```

**Fix required:**
```python
# Sau domain_response, phải update session:
if domain_response.status == DomainResult.NEED_MORE_INFO:
    session_state.active_domain = domain
    session_state.pending_intent = intent
    session_state.missing_slots = domain_response.missing_slots
    await session_repository.save(session_state)
```

---

### B2. Slot Extraction Không Merge Vào Session

**Vị trí:** `backend/router/steps/pattern_step.py:139`, `backend/router/orchestrator.py:555`

**Vấn đề:**
- Pattern step extract slots: `slots = self._extract_slots(message, pattern, slots_extraction)`
- Slots được đưa vào `RouterResponse.slots`
- **Slots KHÔNG được merge vào `session_state.slots_memory`**

**Hậu quả:**
- Multi-turn conversation không thể accumulate slots
- User phải nhập lại thông tin đã cung cấp

**Code hiện tại:**
```python
# pattern_step.py:139
slots = self._extract_slots(message, pattern, slots_extraction)

# orchestrator.py:555
return RouterResponse(
    slots=result.get("slots", {}),  # ❌ Chỉ pass qua, không merge
    ...
)

# ❌ KHÔNG CÓ: session_state.merge_slots(slots)
```

**Fix required:**
```python
# Trong orchestrator, sau khi extract slots:
if result.get("slots"):
    session_state.merge_slots(result["slots"])
    await session_repository.save(session_state)
```

---

### B3. UNKNOWN Handling Không Có Recovery Path

**Vị trí:** `backend/router/orchestrator.py:160-162`

**Vấn đề:**
- UNKNOWN response chỉ trả về message cố định
- **KHÔNG có:**
  - Disambiguation (hỏi user chọn domain)
  - Fallback to last_domain nếu có
  - Escalation path
  - Retry với context

**Code hiện tại:**
```python
# orchestrator.py:562-574
def _build_unknown_response(self, trace_id: str, trace: RouterTrace) -> RouterResponse:
    return RouterResponse(
        status="UNKNOWN",
        message="Xin lỗi, tôi chưa hiểu câu hỏi của bạn. Bạn có thể diễn đạt lại không?",
        # ❌ KHÔNG CÓ options, không có fallback
    )
```

**Fix required:**
```python
def _build_unknown_response(self, trace_id: str, trace: RouterTrace, session_state: SessionState) -> RouterResponse:
    # Nếu có last_domain, suggest resume
    if session_state.last_domain:
        message = f"Bạn muốn tiếp tục với {session_state.last_domain} hay chuyển sang domain khác?"
        options = [session_state.last_domain, "Khác"]
    else:
        message = "Bạn muốn hỏi về domain nào?"
        options = ["HR", "Catalog", "DBA"]
    
    return RouterResponse(
        status="UNKNOWN",
        message=message,
        options=options,  # ✅ Có disambiguation
    )
```

---

## C. LỖI KIẾN TRÚC (STRUCTURAL ISSUES)

### C1. Router Không Sử Dụng Session Context Cho Routing Decision

**Vị trí:** `backend/router/orchestrator.py:116-120`

**Vấn đề:**
- Router load session nhưng **KHÔNG dùng `active_domain`, `pending_intent` để boost routing**
- Nếu user đang trong flow HR và nói "ngày mai", router sẽ route lại từ đầu thay vì tiếp tục flow

**Code hiện tại:**
```python
# orchestrator.py:117
meta_result = await self._step_1_meta(normalized, session_state, router_trace, span)
# ❌ KHÔNG CHECK: if session_state.pending_intent → continue flow
```

**Fix required:**
```python
# Trước STEP 1, check pending intent:
if session_state.pending_intent and session_state.active_domain:
    # User đang trong flow, check nếu message là slot value
    if self._is_slot_value(normalized, session_state.missing_slots):
        # Route trực tiếp về domain đang active
        return self._build_continuation_response(session_state, normalized)
```

---

### C2. Domain Entry Handler Không Validate Session State

**Vị trí:** `backend/domain/hr/entry_handler.py:53`, `backend/domain/catalog/entry_handler.py:89`

**Vấn đề:**
- Domain handler nhận `DomainRequest` nhưng **KHÔNG có access đến session state**
- Không thể check `pending_intent` để biết đây là continuation hay new request
- Không thể merge `slots_memory` từ session vào request slots

**Code hiện tại:**
```python
# domain_dispatcher.py:97-109
domain_request = DomainRequest(
    slots=router_response.slots or {},  # ❌ Chỉ có slots mới, không merge với session
    ...
)
```

**Fix required:**
```python
# Trong domain_dispatcher, merge session slots:
session_slots = session_state.slots_memory.copy()
session_slots.update(router_response.slots or {})
domain_request = DomainRequest(
    slots=session_slots,  # ✅ Merge với session
    ...
)
```

---

### C3. Intent Mapping Hard-code Trong Catalog Handler

**Vị trí:** `backend/domain/catalog/entry_handler.py:55-79`

**Vấn đề:**
- Intent mapping hard-code trong `CatalogEntryHandler.__init__`
- Thêm intent mới phải sửa code
- HR handler không có mapping (dùng trực tiếp intent name)

**Code hiện tại:**
```python
# catalog/entry_handler.py:55-79
self.intent_mapping = {
    "search_products": "catalog.search",
    "query_product_detail": "catalog.info",
    # ... hard-code
}
```

**Fix required:**
- Move intent mapping ra config file (`config/intent_registry.yaml`)
- Load mapping ở router level, pass vào domain handler
- Standardize intent naming convention

---

### C4. Thiếu State Machine Cho Conversation Flow

**Vị trí:** Toàn bộ flow

**Vấn đề:**
- Flow hiện tại là linear: Router → Domain → Response
- **KHÔNG có state machine** để quản lý:
  - `IDLE` → `ROUTING` → `PROCESSING` → `NEED_INFO` → `COMPLETE`
  - Transition guards (khi nào chuyển state)
  - State-specific actions

**Hậu quả:**
- Khó debug conversation flow
- Khó handle edge cases (user cancel, timeout, retry)
- Khó test state transitions

**Fix required:**
```python
# Tạo ConversationStateMachine
class ConversationState(Enum):
    IDLE = "idle"
    ROUTING = "routing"
    PROCESSING = "processing"
    NEED_INFO = "need_info"
    COMPLETE = "complete"
    ERROR = "error"

# Store state trong session_state
session_state.conversation_state = ConversationState.PROCESSING
```

---

### C5. Domain Response Không Có Next Action

**Vị trí:** `backend/schemas/domain_types.py:42-52`

**Vấn đề:**
- `DomainResponse` chỉ có `status`, `data`, `message`
- **KHÔNG có `next_action`** để router biết phải làm gì tiếp:
  - `ASK_SLOT` (hỏi slot cụ thể)
  - `CONFIRM` (xác nhận trước khi execute)
  - `CONTINUE` (tiếp tục flow)
  - `END` (kết thúc)

**Code hiện tại:**
```python
# domain_types.py:42-52
@dataclass
class DomainResponse:
    status: DomainResult
    data: Optional[Dict[str, Any]] = None
    missing_slots: Optional[list[str]] = None
    # ❌ KHÔNG CÓ: next_action
```

**Fix required:**
```python
@dataclass
class DomainResponse:
    status: DomainResult
    next_action: Optional[Literal["ASK_SLOT", "CONFIRM", "CONTINUE", "END"]] = None
    next_action_params: Optional[Dict[str, Any]] = None  # slot_name, confirm_data, etc.
```

---

## D. NHỮNG ĐIỂM LÀM ĐÚNG, GIỮ LẠI

### D1. Router Chạy Đúng 1 Lần Ở Entry Point ✅

**Vị trí:** `backend/interface/api_handler.py:107`

**Đánh giá:**
- Router chỉ được gọi 1 lần trong `APIHandler.handle_request()`
- Không có re-routing trong domain handlers
- Đúng nguyên tắc: Router = Decision System, chỉ quyết định 1 lần

---

### D2. Domain Routing Tách Biệt Rõ Ràng ✅

**Vị trí:** `backend/interface/domain_dispatcher.py:37-123`

**Đánh giá:**
- Domain dispatcher tách biệt hoàn toàn với router
- Mỗi domain có entry handler riêng
- Domain không biết router tồn tại (đúng Clean Architecture)

---

### D3. Routing Pipeline Tuyến Tính, Có Fallback ✅

**Vị trí:** `backend/router/orchestrator.py:110-162`

**Đánh giá:**
- Flow: Meta → Pattern → Embedding → LLM → UNKNOWN
- Mỗi step có error handling riêng
- Parallel execution cho Pattern + Keyword (tối ưu latency)

---

### D4. Trace/Audit Đầy Đủ ✅

**Vị trí:** `backend/router/orchestrator.py:88-97`, `backend/schemas/router_types.py:56-84`

**Đánh giá:**
- Mỗi step ghi trace với input/output/duration
- OpenTelemetry integration
- Có thể debug được mọi quyết định routing

---

### D5. Session Contract Rõ Ràng ✅

**Vị trí:** `backend/schemas/session_types.py:9-55`

**Đánh giá:**
- `SessionState` có đủ fields theo spec
- Có methods `merge_slots()`, `clear_slots()`
- Validation trong `__post_init__`

**Lưu ý:** Contract đúng nhưng **không được sử dụng đầy đủ** (xem B2)

---

## E. SƠ ĐỒ FLOW ĐỀ XUẤT

```
┌─────────────────────────────────────────────────────────────┐
│                    USER MESSAGE                              │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              API HANDLER (Interface Layer)                  │
│  - Validate metadata                                        │
│  - Create RouterRequest                                     │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           ROUTER ORCHESTRATOR (Decision System)            │
│                                                             │
│  STEP 0: Session Load/Create                               │
│    ├─ Load session từ Redis                                │
│    └─ Create nếu chưa có                                   │
│                                                             │
│  STEP 0.5: Normalize Input                                   │
│    ├─ Trim, lowercase                                       │
│    ├─ Normalize dates                                       │
│    └─ Extract entities                                      │
│                                                             │
│  STEP 0.6: Check Continuation (MỚI)                         │
│    ├─ Nếu session_state.pending_intent:                     │
│    │   └─ Check nếu message là slot value                   │
│    │       └─ Route về active_domain                        │
│    └─ Nếu không: tiếp tục flow                             │
│                                                             │
│  STEP 1: Meta-task Detection                                │
│    └─ help, reset, cancel → return META_HANDLED            │
│                                                             │
│  STEP 2-3: Pattern + Keyword (parallel)                     │
│    ├─ Pattern match → return ROUTED                        │
│    └─ Keyword boost → pass to Embedding                    │
│                                                             │
│  STEP 4: Embedding Classifier                               │
│    └─ confidence >= 0.8 → return ROUTED                    │
│                                                             │
│  STEP 5: LLM Classifier (fallback)                          │
│    └─ confidence >= 0.65 → return ROUTED                     │
│                                                             │
│  STEP 6: UNKNOWN                                            │
│    ├─ Check last_domain → suggest resume                    │
│    └─ Return options for disambiguation                     │
│                                                             │
│  STEP 7: Persist Session (MỚI)                              │
│    ├─ Update active_domain, last_domain                     │
│    ├─ Merge slots vào slots_memory                         │
│    └─ Save session to Redis                                 │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DOMAIN DISPATCHER                               │
│  - Map domain → handler                                     │
│  - Merge session slots với router slots (MỚI)               │
│  - Create DomainRequest                                     │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DOMAIN ENTRY HANDLER                           │
│  - Map intent → use case                                    │
│  - Execute use case                                         │
│  - Return DomainResponse với next_action (MỚI)              │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         SESSION UPDATE (MỚI)                                 │
│  - Nếu NEED_MORE_INFO:                                      │
│    ├─ Update pending_intent                                 │
│    ├─ Update missing_slots                                  │
│    └─ Save session                                          │
│  - Nếu SUCCESS:                                             │
│    ├─ Clear pending_intent                                  │
│    ├─ Clear missing_slots                                   │
│    └─ Save session                                          │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         RESPONSE FORMATTER                                  │
│  - Format với personalization                               │
│  - Return to user                                           │
└─────────────────────────────────────────────────────────────┘
```

**Thay đổi chính:**
1. ✅ Thêm STEP 0.6: Check Continuation (resume flow)
2. ✅ Thêm STEP 7: Persist Session sau routing
3. ✅ Domain Dispatcher merge session slots
4. ✅ Domain Response có next_action
5. ✅ Session Update sau domain response

---

## F. CHECKLIST CẢI TIẾN ƯU TIÊN

### Priority 1: CRITICAL (Blocking Issues)

- [ ] **F1.1: Implement Session Persistence Sau Domain Response**
  - File: `backend/interface/api_handler.py`
  - Thêm session update sau `domain_dispatcher.dispatch()`
  - Update `active_domain`, `last_domain`, `pending_intent`, `missing_slots`
  - Test: Multi-turn conversation với NEED_MORE_INFO

- [ ] **F1.2: Implement Slot Merge Vào Session**
  - File: `backend/router/orchestrator.py`
  - Sau khi extract slots, merge vào `session_state.slots_memory`
  - Save session ngay sau merge
  - Test: User nhập slots qua nhiều turn

- [ ] **F1.3: Implement UNKNOWN Recovery Path**
  - File: `backend/router/orchestrator.py:_build_unknown_response()`
  - Check `session_state.last_domain` để suggest resume
  - Return options cho disambiguation
  - Test: UNKNOWN → suggest → user chọn → route đúng

---

### Priority 2: HIGH (Structural Issues)

- [ ] **F2.1: Implement Continuation Check**
  - File: `backend/router/orchestrator.py`
  - Thêm STEP 0.6: Check `pending_intent` trước routing
  - Nếu message là slot value → route về `active_domain`
  - Test: User đang trong flow HR → nhập "ngày mai" → tiếp tục flow

- [ ] **F2.2: Domain Dispatcher Merge Session Slots**
  - File: `backend/interface/domain_dispatcher.py:97-109`
  - Merge `session_state.slots_memory` với `router_response.slots`
  - Pass merged slots vào `DomainRequest`
  - Test: Slots từ turn trước + turn hiện tại → domain nhận đủ

- [ ] **F2.3: Add Next Action To Domain Response**
  - File: `backend/schemas/domain_types.py:42-52`
  - Thêm `next_action` và `next_action_params`
  - Update domain handlers trả về next_action
  - Router sử dụng next_action để update session

---

### Priority 3: MEDIUM (Improvements)

- [ ] **F3.1: Move Intent Mapping To Config**
  - File: `config/intent_registry.yaml` (tạo mới)
  - Move hard-code mapping từ `CatalogEntryHandler` ra config
  - Load mapping ở router level
  - Standardize intent naming

- [ ] **F3.2: Implement Conversation State Machine**
  - File: `backend/schemas/session_types.py` (thêm field)
  - File: `backend/router/conversation_state_machine.py` (tạo mới)
  - Define states: IDLE, ROUTING, PROCESSING, NEED_INFO, COMPLETE, ERROR
  - Implement transition guards và actions

- [ ] **F3.3: Router Sử Dụng Session Context**
  - File: `backend/router/orchestrator.py`
  - Boost routing nếu có `last_domain`
  - Check `pending_intent` để quyết định routing strategy

---

### Priority 4: LOW (Nice to Have)

- [ ] **F4.1: Add Slot Validation At Router Level**
  - Validate slot format (date, number, etc.) trước khi pass domain
  - Return error sớm nếu slot invalid

- [ ] **F4.2: Add Conversation Timeout**
  - Clear `pending_intent` nếu user không respond trong X phút
  - Reset session state về IDLE

- [ ] **F4.3: Add Escalation Path**
  - Nếu retry_count > threshold → escalate to human
  - Set `escalation_flag` trong session

---

## G. METRICS ĐỂ ĐO LƯỜNG CẢI TIẾN

1. **Session Persistence Rate**: % requests có session được update đúng
2. **Slot Accumulation Rate**: % multi-turn conversations accumulate slots thành công
3. **UNKNOWN Recovery Rate**: % UNKNOWN requests được resolve qua disambiguation
4. **Continuation Success Rate**: % continuation flows hoàn thành thành công
5. **Average Turns To Complete**: Số turn trung bình để hoàn thành 1 intent

---

## H. KẾT LUẬN

**Điểm mạnh:**
- Kiến trúc tách biệt rõ ràng (Router → Domain)
- Routing pipeline có fallback
- Trace/audit đầy đủ

**Điểm yếu:**
- Session không được persist → mất context
- Slot không accumulate → user phải nhập lại
- UNKNOWN không có recovery → dead-end

**Khuyến nghị:**
- Ưu tiên fix Priority 1 (3 issues blocking)
- Sau đó implement Priority 2 (3 structural issues)
- Priority 3-4 có thể làm dần

**Timeline ước tính:**
- Priority 1: 2-3 ngày
- Priority 2: 3-4 ngày
- Priority 3: 5-7 ngày
- Priority 4: 2-3 ngày

**Tổng: 12-17 ngày để đạt mức production-ready**
