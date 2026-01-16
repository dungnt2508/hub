# PRODUCTION TESTING GUIDE - CHATBOT ARCHITECTURE

**Ngày tạo:** 2025-01-16  
**Phiên bản:** 1.0  
**Mục đích:** Hướng dẫn test toàn bộ features đã implement sau audit

---

## MỤC LỤC

1. [Setup và Prerequisites](#setup-và-prerequisites)
2. [Test Priority 1: Critical Issues](#test-priority-1-critical-issues)
3. [Test Priority 2: High Priority Issues](#test-priority-2-high-priority-issues)
4. [Test Priority 3: Medium Priority Issues](#test-priority-3-medium-priority-issues)
5. [Test Priority 4: Low Priority Issues](#test-priority-4-low-priority-issues)
6. [Integration Tests](#integration-tests)
7. [Performance Tests](#performance-tests)
8. [Troubleshooting](#troubleshooting)

---

## SETUP VÀ PREREQUISITES

### 1.1 Kiểm tra Dependencies

```bash
# Check Redis is running
redis-cli ping
# Expected: PONG

# Check PostgreSQL is running
psql -U bot_user -d bot_db -c "SELECT 1;"
# Expected: 1 row returned

# Check Python environment
python --version
# Expected: Python 3.12+

# Install dependencies
cd bot
pip install -r requirements.txt
```

### 1.2 Setup Environment Variables

Tạo file `.env` trong `bot/` directory:

```env
# Database
DATABASE_URL=postgresql://bot_user:bot_pw@localhost:5432/bot_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Session
SESSION_TTL_SECONDS=2592000
CONVERSATION_TIMEOUT_MINUTES=10

# Escalation
ESCALATION_RETRY_THRESHOLD=3

# Router
ENABLE_PATTERN=true
ENABLE_EMBEDDING=true
ENABLE_LLM_FALLBACK=true
EMBEDDING_THRESHOLD=0.8
LLM_THRESHOLD=0.65
```

### 1.3 Seed Test Data

```bash
# Seed routing rules (nếu chưa có)
python -m backend.scripts.seed_routing_data

# Create test tenant
python -m backend.scripts.create_tenant --name test-tenant --plan basic
```

### 1.4 Start Services

```bash
# Start bot API (terminal 1)
cd bot
python -m uvicorn backend.interface.multi_tenant_bot_api:app --host 0.0.0.0 --port 8386

# Verify API is running
curl http://localhost:8386/health
# Expected: {"status": "ok"}
```

---

## TEST PRIORITY 1: CRITICAL ISSUES

### Test F1.1: Session Persistence Sau Domain Response

**Mục tiêu:** Verify session được update đúng sau domain response

#### Test Case 1.1.1: NEED_MORE_INFO Persistence

**Steps:**
1. Gửi request tạo leave request thiếu slots:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "NEED_MORE_INFO",
  "message": "Vui lòng cung cấp: start_date, end_date, reason",
  "missing_slots": ["start_date", "end_date", "reason"],
  "next_action": "ASK_SLOT",
  "session_id": "<session-id>"
}
```

**Verify:**
```bash
# Check session trong Redis
redis-cli GET "session:<session-id>"
# Expected: JSON có:
# - active_domain: "hr"
# - pending_intent: "create_leave_request"
# - missing_slots: ["start_date", "end_date", "reason"]
# - last_domain: "hr"
# - last_intent: "create_leave_request"
```

#### Test Case 1.1.2: SUCCESS Persistence

**Steps:**
1. Gửi request query leave balance (không cần slots):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-previous>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_balance": 7
  },
  "session_id": "<same-session-id>"
}
```

**Verify:**
```bash
# Check session trong Redis
redis-cli GET "session:<session-id>"
# Expected: JSON có:
# - active_domain: null
# - pending_intent: null
# - missing_slots: []
# - last_domain: "hr"
# - last_intent: "query_leave_balance"
# - slots_memory: {} (cleared)
```

---

### Test F1.2: Slot Merge Vào Session

**Mục tiêu:** Verify slots được merge vào session và persist

#### Test Case 1.2.1: Multi-turn Slot Accumulation

**Steps:**
1. Turn 1: Tạo leave request với start_date:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép từ ngày 2025-02-01",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: NEED_MORE_INFO với missing_slots: ["end_date", "reason"]
- Session có: `slots_memory: {"start_date": "2025-02-01"}`

2. Turn 2: Cung cấp end_date:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "đến ngày 2025-02-05",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-turn-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: NEED_MORE_INFO với missing_slots: ["reason"]
- Session có: `slots_memory: {"start_date": "2025-02-01", "end_date": "2025-02-05"}` (merged)

3. Turn 3: Cung cấp reason:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "nghỉ phép gia đình",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-turn-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: SUCCESS với leave request created
- Session có: `slots_memory: {}` (cleared after success)

**Verify:**
```bash
# Check session sau mỗi turn
redis-cli GET "session:<session-id>"
# Verify slots_memory được accumulate đúng
```

---

### Test F1.3: UNKNOWN Recovery Path

**Mục tiêu:** Verify UNKNOWN có recovery path với disambiguation

#### Test Case 1.3.1: UNKNOWN Without Last Domain

**Steps:**
1. Gửi message không rõ ràng (new session):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "xyz abc 123",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "UNKNOWN",
  "message": "Bạn muốn hỏi về domain nào? Vui lòng chọn một trong các lựa chọn sau:",
  "options": ["HR", "Catalog", "DBA"],
  "source": "UNKNOWN"
}
```

#### Test Case 1.3.2: UNKNOWN With Last Domain

**Steps:**
1. Gửi message HR trước (để set last_domain):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

2. Gửi message không rõ ràng (cùng session):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "xyz abc 123",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-step-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "UNKNOWN",
  "message": "Bạn muốn tiếp tục với HR hay chuyển sang domain khác?",
  "options": ["hr", "Khác"],
  "source": "UNKNOWN"
}
```

---

## TEST PRIORITY 2: HIGH PRIORITY ISSUES

### Test F2.1: Continuation Check

**Mục tiêu:** Verify continuation flow khi user đang trong active flow

#### Test Case 2.1.1: Continuation với Date Slot

**Steps:**
1. Bắt đầu leave request (thiếu slots):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:** NEED_MORE_INFO với missing_slots: ["start_date", "end_date", "reason"]

2. Cung cấp date (short message - slot value):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "2025-02-01",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-step-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: NEED_MORE_INFO (vẫn thiếu end_date và reason)
- Router trace có: `source: "CONTINUATION"`
- Session có: `slots_memory: {"start_date": "2025-02-01"}`

**Verify:**
```bash
# Check router trace
# Response phải có trace với step "router.step.continuation"
# Và decision_source: "CONTINUATION"
```

#### Test Case 2.1.2: Continuation với "mai" (tomorrow)

**Steps:**
1. Bắt đầu leave request
2. User nói "mai" (tomorrow):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "mai",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: NEED_MORE_INFO
- Router trace có: `source: "CONTINUATION"`
- Session có: `slots_memory: {"start_date": "<tomorrow-iso-date>"}` (normalized)

---

### Test F2.2: Domain Dispatcher Merge Session Slots

**Mục tiêu:** Verify slots từ session được merge với router slots

#### Test Case 2.2.1: Session Slots + Router Slots Merge

**Steps:**
1. Turn 1: Cung cấp start_date (slot được lưu trong session)
2. Turn 2: Cung cấp end_date và reason trong cùng message:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "đến ngày 2025-02-05 vì nghỉ phép gia đình",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Domain nhận được: `slots: {"start_date": "<from-session>", "end_date": "2025-02-05", "reason": "nghỉ phép gia đình"}`
- Response: SUCCESS (nếu pattern match extract được cả end_date và reason)

**Verify:**
```bash
# Check logs để verify domain dispatcher merge slots
# Log phải có: "Slots merged from session and router"
# Với: session_slots_count, router_slots_count, merged_slots_count
```

---

### Test F2.3: Next Action To Domain Response

**Mục tiêu:** Verify domain response có next_action

#### Test Case 2.3.1: NEED_MORE_INFO với Next Action

**Steps:**
1. Gửi request thiếu slots:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "NEED_MORE_INFO",
  "message": "Vui lòng cung cấp: start_date, end_date, reason",
  "missing_slots": ["start_date", "end_date", "reason"],
  "next_action": "ASK_SLOT",
  "next_action_params": {
    "slot_name": "start_date",
    "all_missing": ["start_date", "end_date", "reason"]
  }
}
```

#### Test Case 2.3.2: SUCCESS với Next Action

**Steps:**
1. Gửi request đầy đủ slots:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_balance": 7
  },
  "next_action": "END"
}
```

---

## TEST PRIORITY 3: MEDIUM PRIORITY ISSUES

### Test F3.1: Intent Mapping From Config

**Mục tiêu:** Verify intent mapping được load từ config

#### Test Case 3.1.1: Catalog Intent Mapping

**Steps:**
1. Gửi catalog search request:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tìm kiếm sản phẩm workflow",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Router route về: `domain: "catalog", intent: "search_products"`
- Domain handler map: `search_products` → `catalog.search` (use_case_key từ registry)
- Response: SUCCESS với search results

**Verify:**
```bash
# Check logs
# Phải có: "Intent mapped: search_products → catalog.search"
# Không có hard-code mapping trong CatalogEntryHandler
```

#### Test Case 3.1.2: Add New Intent To Registry

**Steps:**
1. Thêm intent mới vào `config/intent_registry.yaml`:
```yaml
- intent: query_product_reviews
  domain: catalog
  intent_type: KNOWLEDGE
  required_slots: []
  optional_slots: [product_id]
  source_allowed: [PATTERN, EMBEDDING, LLM]
  description: "Query product reviews"
  use_case_key: catalog.info
```

2. Restart API server
3. Gửi request với intent mới:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Xem đánh giá sản phẩm",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Intent được route và map đúng
- Không cần sửa code CatalogEntryHandler

---

### Test F3.2: Conversation State Machine

**Mục tiêu:** Verify state machine transitions đúng

#### Test Case 3.2.1: State Transitions Flow

**Steps:**
1. New request → Check state:
```bash
# Check session state
redis-cli GET "session:<session-id>"
# Expected: conversation_state: "idle"
```

2. Gửi request → State should be ROUTING:
```bash
# Check logs hoặc trace
# Expected: conversation_state: "routing"
```

3. Domain processing → State should be PROCESSING:
```bash
# Check logs
# Expected: conversation_state: "processing"
```

4. NEED_MORE_INFO → State should be NEED_INFO:
```bash
# Check session
# Expected: conversation_state: "need_info"
```

5. SUCCESS → State should be COMPLETE then IDLE:
```bash
# Check session
# Expected: conversation_state: "complete" → "idle"
```

**Verify:**
```bash
# Check state transitions trong logs
# Phải có: "State transition: idle → routing"
# Phải có: "State transition: routing → processing"
# Phải có: "State transition: processing → need_info"
# Phải có: "State transition: need_info → idle"
```

#### Test Case 3.2.2: Invalid State Transition

**Steps:**
1. Manually set invalid state trong Redis:
```bash
redis-cli SET "session:<session-id>" '{"conversation_state": "complete", ...}'
```

2. Gửi request → Should handle gracefully:
```bash
# Expected: Log warning về invalid transition
# System vẫn hoạt động (không crash)
```

---

### Test F3.3: Router Sử Dụng Session Context

**Mục tiêu:** Verify router boost routing dựa trên last_domain

#### Test Case 3.3.1: Context Boost với Last Domain

**Steps:**
1. Gửi HR request (set last_domain):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

2. Gửi ambiguous message (có thể route về HR hoặc Catalog):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tìm kiếm thông tin",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-step-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Router boost HR domain (last_domain) thêm 0.1
- Nếu embedding confidence HR = 0.75, sau boost = 0.85 → route về HR
- Log phải có: "Applied session context boost"

**Verify:**
```bash
# Check router trace
# Embedding step phải có boost cho "hr" domain
# LLM step (nếu chạy) phải boost confidence nếu match last_domain
```

---

## TEST PRIORITY 4: LOW PRIORITY ISSUES

### Test F4.1: Slot Validation At Router Level

**Mục tiêu:** Verify slot format validation

#### Test Case 4.1.1: Date Slot Validation

**Steps:**
1. Gửi request với invalid date format:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép từ ngày 32/13/2025",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Router validate và reject invalid date
- Log warning: "Invalid slot format: start_date"
- Slots không được merge vào session
- Domain vẫn nhận request nhưng với empty/invalid slots

#### Test Case 4.1.2: Number Slot Validation

**Steps:**
1. Gửi request với invalid number:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tìm sản phẩm có giá abc",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Router validate và reject invalid number
- Log warning về invalid slot format

#### Test Case 4.1.3: Valid Date Normalization

**Steps:**
1. Gửi request với date "mai":
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép từ ngày mai",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Normalize step extract: `"mai"` → `"2025-01-17"` (tomorrow)
- Slot validator validate và convert về ISO format
- Session có: `slots_memory: {"start_date": "2025-01-17"}`

---

### Test F4.2: Conversation Timeout

**Mục tiêu:** Verify conversation timeout clear pending state

#### Test Case 4.2.1: Timeout Clear Pending Intent

**Steps:**
1. Bắt đầu leave request (set pending_intent):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi muốn xin nghỉ phép",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

2. Wait 10+ minutes (hoặc set `CONVERSATION_TIMEOUT_MINUTES=1` để test nhanh)

3. Gửi request mới (cùng session):
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Xin chào",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id-from-step-1>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Log: "Conversation timeout detected, clearing pending state"
- Session có:
  - `pending_intent: null`
  - `active_domain: null`
  - `missing_slots: []`
  - `conversation_state: "idle"`
- Request được xử lý như new conversation (không continue flow cũ)

**Verify:**
```bash
# Check session trước và sau timeout
redis-cli GET "session:<session-id>"
# Verify pending state đã được clear
```

---

### Test F4.3: Escalation Path

**Mục tiêu:** Verify escalation khi retry_count > threshold

#### Test Case 4.3.1: Escalation After Retry Threshold

**Steps:**
1. Set `ESCALATION_RETRY_THRESHOLD=2` trong `.env` và restart

2. Gửi request gây error (3 lần):
```bash
# Request 1: Invalid input
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Invalid request that causes error",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
# Expected: ERROR response, retry_count = 1

# Request 2: Another error
# Expected: ERROR response, retry_count = 2

# Request 3: Another error
# Expected: ESCALATION response, retry_count = 0, escalation_flag = true
```

**Expected Response (Request 3):**
```json
{
  "status": "UNKNOWN",
  "source": "ESCALATION",
  "message": "Xin lỗi, tôi gặp khó khăn trong việc hiểu yêu cầu của bạn. Vui lòng liên hệ với nhân viên hỗ trợ để được giúp đỡ.",
  "session_id": "<session-id>"
}
```

**Verify:**
```bash
# Check session
redis-cli GET "session:<session-id>"
# Expected:
# - escalation_flag: true
# - retry_count: 0 (reset after escalation)
```

#### Test Case 4.3.2: Reset Retry Count On Success

**Steps:**
1. Gửi request gây error (retry_count = 1)
2. Gửi request thành công:
```bash
curl -X POST http://localhost:8386/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "<session-id>",
    "metadata": {
      "tenant_id": "<your-tenant-id>"
    }
  }'
```

**Expected:**
- Response: SUCCESS
- Session có: `retry_count: 0` (reset)

---

## INTEGRATION TESTS

### Test I1: End-to-End Multi-Turn Conversation

**Mục tiêu:** Test toàn bộ flow từ đầu đến cuối

#### Scenario: Create Leave Request Flow

**Steps:**
1. **Turn 1:** User bắt đầu request
```bash
Message: "Tôi muốn xin nghỉ phép"
Expected: NEED_MORE_INFO, missing: [start_date, end_date, reason]
Session: pending_intent=create_leave_request, active_domain=hr
```

2. **Turn 2:** User cung cấp start_date
```bash
Message: "từ ngày mai"
Expected: NEED_MORE_INFO, missing: [end_date, reason]
Session: slots_memory={start_date: "2025-01-17"}, pending_intent=create_leave_request
Router: source=CONTINUATION (vì detect "mai" là slot value)
```

3. **Turn 3:** User cung cấp end_date
```bash
Message: "đến ngày 2025-01-20"
Expected: NEED_MORE_INFO, missing: [reason]
Session: slots_memory={start_date: "2025-01-17", end_date: "2025-01-20"}
```

4. **Turn 4:** User cung cấp reason
```bash
Message: "nghỉ phép gia đình"
Expected: SUCCESS, leave request created
Session: pending_intent=null, slots_memory={}, conversation_state=idle
```

**Verify:**
- Tất cả slots được accumulate đúng
- Session state transitions đúng
- Continuation flow hoạt động
- Final state được clear đúng

---

### Test I2: Cross-Domain Conversation

**Mục tiêu:** Test switching giữa domains

#### Scenario: HR → Catalog → HR

**Steps:**
1. **HR Request:**
```bash
Message: "Tôi còn bao nhiêu ngày phép?"
Expected: SUCCESS, last_domain=hr
```

2. **Catalog Request:**
```bash
Message: "Tìm kiếm sản phẩm"
Expected: SUCCESS, last_domain=catalog
```

3. **Ambiguous Request (should boost HR vì last_domain):**
```bash
Message: "Thông tin về nghỉ phép"
Expected: Route về HR (boost từ last_domain)
```

**Verify:**
- last_domain được update đúng
- Context boost hoạt động
- Session state transitions đúng

---

## PERFORMANCE TESTS

### Test P1: Concurrent Requests

**Mục tiêu:** Test system với concurrent load

**Steps:**
```bash
# Sử dụng Apache Bench hoặc similar tool
ab -n 100 -c 10 -H "X-API-Key: <your-api-key>" \
  -p request.json -T application/json \
  http://localhost:8386/api/v1/chat
```

**Expected:**
- Tất cả requests được xử lý
- Không có session conflicts
- Response time < 2s cho 95% requests

---

### Test P2: Session Persistence Under Load

**Mục tiêu:** Test session persistence với high load

**Steps:**
1. Tạo 100 sessions
2. Gửi requests concurrent cho các sessions
3. Verify tất cả sessions được persist đúng

**Expected:**
- Không có data loss
- Session state được update đúng
- Redis không bị overload

---

## TROUBLESHOOTING

### Common Issues

#### Issue 1: Session Not Persisting

**Symptoms:**
- Session không được save sau domain response
- Slots không accumulate

**Debug:**
```bash
# Check Redis connection
redis-cli ping

# Check session repository logs
# Look for: "Session saved" hoặc "Failed to save session"

# Check API handler logs
# Look for: "_update_session_after_domain_response"
```

**Fix:**
- Verify Redis is running
- Check SESSION_TTL_SECONDS config
- Verify session_repository.save() không throw exception

---

#### Issue 2: Continuation Not Working

**Symptoms:**
- User đang trong flow nhưng không continue được

**Debug:**
```bash
# Check session state
redis-cli GET "session:<session-id>"
# Verify: pending_intent, active_domain, missing_slots

# Check router trace
# Look for: "router.step.continuation"
# Verify: continued=true
```

**Fix:**
- Verify continuation step được gọi
- Check _is_slot_value() logic
- Verify normalized_entities có dates/numbers

---

#### Issue 3: State Machine Invalid Transitions

**Symptoms:**
- Log warnings về invalid state transitions

**Debug:**
```bash
# Check conversation_state trong session
# Verify state transitions trong logs
```

**Fix:**
- Check state machine transitions definitions
- Verify transition guards
- Ensure state được update đúng

---

#### Issue 4: Escalation Not Triggering

**Symptoms:**
- retry_count > threshold nhưng không escalate

**Debug:**
```bash
# Check retry_count trong session
redis-cli GET "session:<session-id>"
# Verify: retry_count, escalation_flag

# Check config
echo $ESCALATION_RETRY_THRESHOLD
```

**Fix:**
- Verify ESCALATION_RETRY_THRESHOLD config
- Check retry_count được increment đúng
- Verify escalation check ở router entry

---

### Debug Commands

```bash
# Check session state
redis-cli GET "session:<session-id>"

# List all sessions
redis-cli KEYS "session:*"

# Check router trace (nếu có trace_id)
# Look in logs hoặc trace storage

# Monitor Redis
redis-cli MONITOR

# Check API logs
tail -f logs/bot.log | grep "router\|session\|domain"
```

---

## TEST CHECKLIST

### Priority 1 ✅
- [ ] F1.1: Session persistence sau NEED_MORE_INFO
- [ ] F1.1: Session persistence sau SUCCESS
- [ ] F1.2: Slot merge vào session (multi-turn)
- [ ] F1.3: UNKNOWN recovery với last_domain
- [ ] F1.3: UNKNOWN recovery không có last_domain

### Priority 2 ✅
- [ ] F2.1: Continuation với date slot
- [ ] F2.1: Continuation với "mai"
- [ ] F2.2: Session slots merge với router slots
- [ ] F2.3: Next action ASK_SLOT
- [ ] F2.3: Next action END

### Priority 3 ✅
- [ ] F3.1: Intent mapping từ config
- [ ] F3.1: Add new intent không cần sửa code
- [ ] F3.2: State transitions flow
- [ ] F3.2: Invalid transition handling
- [ ] F3.3: Context boost với last_domain

### Priority 4 ✅
- [ ] F4.1: Date slot validation
- [ ] F4.1: Number slot validation
- [ ] F4.1: Date normalization ("mai" → ISO)
- [ ] F4.2: Conversation timeout clear pending
- [ ] F4.3: Escalation after retry threshold
- [ ] F4.3: Retry count reset on success

### Integration ✅
- [ ] End-to-end multi-turn conversation
- [ ] Cross-domain conversation
- [ ] Concurrent requests
- [ ] Session persistence under load

---

## METRICS TO MONITOR

### Success Metrics
- **Session Persistence Rate:** > 99%
- **Slot Accumulation Rate:** > 95%
- **Continuation Success Rate:** > 90%
- **UNKNOWN Recovery Rate:** > 80%
- **Average Turns To Complete:** < 3 turns

### Performance Metrics
- **P95 Response Time:** < 2s
- **P99 Response Time:** < 5s
- **Error Rate:** < 1%
- **Escalation Rate:** < 5%

---

## NEXT STEPS

Sau khi pass tất cả tests:

1. **Load Testing:** Test với production-like load
2. **Stress Testing:** Test với extreme load
3. **Security Testing:** Test authentication, authorization
4. **Monitoring Setup:** Setup alerts cho metrics
5. **Documentation:** Update API docs với new features

---

**Lưu ý:** Tất cả test cases phải được run trong môi trường test/staging trước khi deploy production.
