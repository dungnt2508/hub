# ĐÁNH GIÁ KIẾN TRÚC DBA DOMAIN

**Phạm vi:** DBA domain routing, risk assessment, execution pipeline, LLM integration, frontend sandbox  
**Ngày:** 2026-01-11  
**Mục tiêu:** Xác định hệ thống có thể vận hành an toàn cho DBA domain hay không

---

## 1. SƠ ĐỒ KIẾN TRÚC

### Luồng Pipeline Thực Tế

```
YÊU CẦU TỪ USER
    ↓
┌─────────────────────────────────────────┐
│ ROUTING LAYER (orchestrator.py)        │
│ Steps: Session → Normalize → Meta →    │
│        Pattern → Keyword → Embedding → │
│        LLM Classifier                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ DOMAIN ENTRY (entry_handler.py)        │
│ Maps intent → use case                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ USE CASE LAYER (base_use_case.py)      │
│ 4 Gates: Production → Scope →          │
│          Permission → Validation        │
└─────────────────────────────────────────┘
    ↓ (gates pass)
┌─────────────────────────────────────────┐
│ MCP CLIENT (adapters/mcp_db_client.py) │
│ Execute predefined SQL via MCP          │
└─────────────────────────────────────────┘
    ↓ (returns data)
    TRẢ KẾT QUẢ CHO USER

LUỒNG RIÊNG CHO SANDBOX:
┌─────────────────────────────────────────┐
│ FRONTEND → /risk-assessment             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Risk Service: Simulate gates            │
└─────────────────────────────────────────┘
    ↓ (nếu GO hoặc GO-WITH-CONDITIONS)
┌─────────────────────────────────────────┐
│ FRONTEND → /execute-playbook            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Pipeline (pipeline_orchestrator.py):    │
│ 1. Risk (CHẠY LẠI)                      │
│ 2. Execution Plan Generator             │
│ 3. DB Executor                          │
│ 4. Interpretation Layer                 │
└─────────────────────────────────────────┘
```

### Vấn Đề Về Tầng

#### [ARCHITECTURE BREAK] ĐÁNH GIÁ RISK BỊ TRÙNG LẶP

**Vị trí:** `dba_routes.py` L431-440

```python
# STEP 1: Run risk assessment first
risk_assessment = await dba_risk_assessment_service.run_assessment(...)
```

**Vấn đề:**  
- Frontend gọi endpoint `/risk-assessment` trước
- User xem kết quả risk  
- Frontend gọi `/execute-playbook`  
- **Backend CHẠY LẠI risk assessment tại L431**  

**Tác động:**  
- Risk gates được đánh giá 2 LẦN  
- Kết quả risk từ frontend bị BỎ QUA  
- User quyết định dựa trên kết quả risk KHÁC  
- KHÔNG đảm bảo quyết định giống nhau 2 lần (dữ liệu phụ thuộc thời gian)

#### THIẾU: Risk Result Passthrough

**Mong đợi:**  
```
/execute-playbook nhận risk_assessment_id hoặc full result
→ Bỏ qua việc chạy lại, dùng kết quả đã validate
```

**Thực tế:**  
```
/execute-playbook bỏ qua risk check từ frontend
→ Chạy lại toàn bộ risk assessment
```

---

## 2. DEAD CODE / DƯ THỪA

### Routing Layer Không Dùng Cho DBA

**File:** `router/orchestrator.py` (671 dòng)  
**Mục đích:** Phân loại intent 5 bước (Pattern → Keyword → Embedding → LLM)  

**Vấn đề:**  
Luồng DBA sandbox BỎ QUA routing hoàn toàn:
- Frontend → `/api/dba/risk-assessment` (trực tiếp)  
- Frontend → `/api/dba/execute-playbook` (trực tiếp)  
- KHÔNG routing qua `RouterOrchestrator`  

**Dead Code:**  
- Intent registry DBA patterns (`intent_registry.yaml` L64-168)
- Pattern matching cho DBA intents
- Embedding classifier cho DBA
- LLM classifier cho DBA

**Tác động:**  
- 13 DBA intents được đăng ký nhưng KHÔNG dùng bởi sandbox
- Routing layer được maintain nhưng KHÔNG HOẠT ĐỘNG cho DBA domain

### Gate Execution Bị Trùng Lặp

**Files:**  
- `use_cases/base_use_case.py` L61-131 (execute method với gates)
- `risk_assessment_service.py` L287-355 (simulate gates)

**Vấn đề:**  
Gates được thực thi ở 3 nơi:
1. **Risk simulation** (frontend sandbox) - simulated gates
2. **Playbook execution** risk re-run (L431) - simulated gates lại
3. **Use case execution** (nếu gọi trực tiếp) - real gates

**Dư thừa:**  
- `ProductionSafetyGate` được check 2-3 lần
- `ScopeValidationGate` được check 2-3 lần  
- `PermissionGate` được check 2-3 lần

### Use Case Registry Trùng Lặp

**Files:**  
- `domain/use_case_registry.py` (đăng ký global)
- `dba_routes.py` L29-146 (hardcoded use case list)

**Tác động:**  
- Cùng dữ liệu use case ở 2 nơi
- Phải sync thủ công khi update

---

## 3. XUNG ĐỘT LOGIC

### [CRITICAL] Bypass Hard Gate

**File:** `dba_routes.py` L341, L415  

```python
user_role = "admin"  # Default for sandbox - can modify prod
```

**Vi phạm:**  
- Sandbox mặc định role `admin`
- Production safety gate check role (gates.py L57-110)  
- Admin role có `production_write: true` (giả định)
- KHÔNG chặn production rõ ràng trong sandbox mode

**Hậu quả:**  
Sandbox user có thể execute trên production nếu:
- Connection string chứa production DB
- User không thấy/hiểu cảnh báo risk

**Hành vi mong đợi:**  
Sandbox nên BẮT BUỘC `role = "viewer"` hoặc chặn production rõ ràng


### LLM Permission Boundary - ĐÚNG

**File:** `interpretation_layer.py` L2-15

```python
# LLM does NOT: generate SQL, modify queries, suggest DDL
# LLM ONLY: analyzes results, identifies patterns, recommends actions
```

**Trạng thái:** ✅ AN TOÀN  
- LLM được gọi SAU KHI DB execution hoàn tất
- LLM nhận RAW results (read-only)
- LLM không thể generate/modify SQL
- Placeholder implementation (L363-366) - chưa tích hợp

### DB Executor Plan Adherence - ĐÚNG

**File:** `db_executor.py` L103-214

**Trạng thái:** ✅ AN TOÀN  
- Steps được execute tuần tự (L145-172)
- KHÔNG reorder
- KHÔNG SQL generation
- Queries chỉ từ predefined templates

### GO/NO-GO Consistency - VI PHẠM

**File:** `dba_routes.py` L442-448

```python
if risk_assessment.final_decision == "NO-GO":
    return {"status": "blocked", ...}
```

**Vấn đề:**  
- Chỉ check NO-GO
- `GO-WITH-CONDITIONS` tiếp tục execution
- Conditions KHÔNG được enforce/validate trước execution

**Mong đợi:**  
```python
if risk_assessment.final_decision == "NO-GO":
    return blocked
if risk_assessment.final_decision == "GO-WITH-CONDITIONS":
    # Validate conditions đã được đáp ứng
    # HOẶC require explicit user override
```

---

## 4. VI PHẠM (NGHIÊM TRỌNG)

### ✅ LLM KHÔNG Generate SQL
**Trạng thái:** AN TOÀN  
**Bằng chứng:** `db_executor.py` L7, L86 cấm rõ ràng

### ✅ LLM KHÔNG Tự Execute
**Trạng thái:** AN TOÀN  
**Bằng chứng:** Interpretation layer được gọi SAU execution (stage 4, L398)

### [VI PHẠM] Write/DDL Không Bị Chặn

**File:** `execution_plan_generator.py` L77-460  

**Vấn đề:**  
Tất cả execution steps được đánh dấu `read_only: bool = True` trong ExecutionStep  
NHƯNG không có enforcement trong `db_executor.py`

**Thiếu:**  
```python
# db_executor.py nên validate TRƯỚC KHI execution
if not step.read_only:
    raise SecurityViolation("Write operations not allowed")
    
# HOẶC validate query không chứa:
# INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
```

**Trạng thái hiện tại:**  
- Execution plan KHAI BÁO read-only  
- Executor TIN TƯỞNG mà không validation  
- Không có runtime SQL parsing/blocking

### [VI PHẠM] Prod Safety Không Được Enforce

**File:** `gates.py` L57-110

```python
# Check for production override permission
if is_prod:
    role = request.user_context.get("role", "viewer")
    if role not in ["admin", "dba_lead"]:
        raise DomainPermissionError(...)
```

**Vấn đề:**  
- Check role, nhưng sandbox mặc định "admin"
- Không chặn ở database-level (connection string validation)
- Chỉ heuristic detection (L39-55): check nếu 'prod' trong string

**Thiếu:**  
- Explicit production DB registry
- Connection ID → environment mapping
- Sandbox mode nên BẮT BUỘC environment=staging

### ✅ Execution Có Raw Output Contract
**Trạng thái:** ĐÃ TRIỂN KHAI  
**Bằng chứng:**  
- `ExecutionResult` dataclass (db_executor.py L50-77)  
- Chứa: `step_results`, `columns`, `data`, `rows`
- Frontend hiển thị raw data (DBAExecutionPlaybook.tsx L319-348)

---

## 5. THÀNH PHẦN CÒN THIẾU

### ✅ Execution Plan Materialization  
**Trạng thái:** ĐÃ TRIỂN KHAI  
**File:** `execution_plan_generator.py`  
**Bằng chứng:** ExecutionPlan dataclass với structured steps

### ✅ Raw DB Output Contract  
**Trạng thái:** ĐÃ TRIỂN KHAI  
**File:** `db_executor.py` ExecutionResult  
**Bằng chứng:** Structured step results với raw data

### ✅ Interpretation Layer Tách Biệt  
**Trạng thái:** ĐÃ TRIỂN KHAI  
**File:** `interpretation_layer.py`  
**Bằng chứng:** Stage 4 của pipeline, nhận execution results

### ✅ Frontend Execution Display  
**Trạng thái:** ĐÃ TRIỂN KHAI  
**File:** `DBAExecutionPlaybook.tsx`  
**Bằng chứng:** 3-tab UI (Risk, Execution, Interpretation)

### [THIẾU] Khả Năng Test Sandbox Execution

**Trạng thái hiện tại:**  
- Không có test connections trong codebase
- Không có mock MCP client cho testing
- Không có integration tests cho pipeline

**Mong đợi:**  
```
tests/
  integration/
    test_dba_pipeline_execution.py
    test_risk_gates.py
  fixtures/
    mock_mcp_responses.json
    test_connections.yaml
```

**Files đã tìm:** Không tìm thấy test files cho DBA domain execution

---

## 6. FRONTEND REVIEW

### UI Flow vs Pipeline Mapping

**Frontend Flow:**  
```tsx
User chọn use case
  ↓
Gọi /risk-assessment → Risk tab được điền
  ↓
User review gates/warnings
  ↓
Nếu can_execute=true, user click Execute
  ↓
Gọi /execute-playbook → Execution + Interpretation tabs được điền
```

**Backend Pipeline:**  
```python
/risk-assessment → RiskAssessmentResult
  (frontend hiển thị)

/execute-playbook →
  1. Risk re-run (TRÙNG LẶP)
  2. Plan generation
  3. DB execution
  4. Interpretation
```

**Không khớp:**  
Frontend giả định risk từ bước 1 còn hợp lệ  
Backend bỏ qua và chạy lại (rủi ro race condition)

### [VI PHẠM] Phát Hiện Fake Success

**File:** `DBAExecutionPlaybook.tsx` L90-108

```tsx
interface PipelineExecutionData {
  risk_assessment: RiskAssessmentResult;
  execution_plan: any;  // Optional?
  execution_results: ExecutionResult;
  interpretation: InterpretationResult;
}
```

**Vấn đề:**  
TypeScript interface KHÔNG đánh dấu fields là Optional  
NHƯNG backend có thể return sớm tại L443-448 nếu NO-GO

**Hậu quả:**  
Frontend expect TẤT CẢ 4 stages có mặt  
Nếu NO-GO, `execution_results` = undefined → runtime error

**Fix cần thiết:**  
```tsx
execution_plan?: ExecutionPlan;
execution_results?: ExecutionResult;
interpretation?: InterpretationResult;
```

### ✅ Risk+Execution+Interpretation Tách Biệt

**Trạng thái:** ĐÚNG  
**Bằng chứng:**  
- 3 tabs riêng biệt trong UI
- Backend trả về separate objects
- Mỗi stage có distinct data contract

---

## 7. KẾ HOẠCH SỬA (THỨ TỰ ƯU TIÊN)

### 🔴 P0 - NGHIÊM TRỌNG (Security / Correctness)

#### 1. Fix Duplicate Risk Assessment
**Vị trí:** `dba_routes.py` L430-440  
**Hành động:**  
- **THÊM** `risk_result_id` query param cho `/execute-playbook`  
- **XÓA** risk re-run tại L431  
- **HOẶC** thêm explicit override flag `force_rerun=true` (logged + audited)

**Files:**  
- SỬA `dba_routes.py` execute_playbook endpoint
- THÊM risk result caching (in-memory hoặc DB)

#### 2. Enforce Read-Only Tại Runtime
**Vị trí:** `db_executor.py` L216-317 `_execute_step`  
**Hành động:**  
```python
# Trước MCP call:
dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
if any(kw in step.query.upper() for kw in dangerous_keywords):
    raise SecurityViolation(f"Write operation blocked: {step.type}")
```

**Files:**  
- SỬA `db_executor.py` _execute_step method

#### 3. Bắt Buộc Sandbox Dùng Non-Admin Role
**Vị trí:** `dba_routes.py` L341, L415  
**Hành động:**  
```python
# Xóa default admin
if os.getenv("SANDBOX_MODE", "false") == "true":
    user_role = "viewer"  # Bắt buộc read-only trong sandbox
else:
    user_role = request.headers.get('X-User-Role', 'viewer')
```

**Files:**  
- SỬA `dba_routes.py` risk_assessment và execute_playbook
- THÊM biến môi trường `SANDBOX_MODE`

#### 4. Fix GO-WITH-CONDITIONS Handling
**Vị trí:** `dba_routes.py` L442-448  
**Hành động:**  
```python
if risk_assessment.final_decision == "NO-GO":
    return blocked
elif risk_assessment.final_decision == "GO-WITH-CONDITIONS":
    # Log warning + require acknowledgment
    logger.warning("Executing with conditions", extra={"conditions": risk_assessment.warnings})
# Chỉ GO proceeds không cảnh báo
```

**Files:**  
- SỬA `dba_routes.py` execute_playbook
- THÊM condition logging

---

### 🟡 P1 - CAO (Maintainability / Redundancy)

#### 5. Xóa Dead Routing Code
**Hành động:**  
- **NẾU** DBA sandbox là use case chính: Document rằng routing KHÔNG được dùng
- **HOẶC** Tích hợp routing: đổi sandbox gọi router trước, sau đó `/execute-playbook`

**Quyết định cần thiết:**  
DBA domain có cần NLU routing không, hay explicit use case selection là đủ?

**Files cần review:**  
- `router/orchestrator.py` (giữ hay deprecate cho DBA?)
- `intent_registry.yaml` (xóa DBA intents nếu không dùng)

#### 6. Hợp Nhất Use Case Registry
**Hành động:**  
```python
# Trong dba_routes.py:
from ...domain.use_case_registry import get_use_cases_for_domain

@router.get("/use-cases")
async def get_dba_use_cases():
    return get_use_cases_for_domain("dba")
```

**Files:**  
- SỬA `dba_routes.py` get_dba_use_cases
- DÙNG `use_case_registry.py` làm single source

#### 7. Fix Frontend Type Safety
**Hành động:**  
```tsx
interface PipelineExecutionData {
  request_id: string;
  playbook: string;
  pipeline_status: 'success' | 'failed' | 'stopped' | 'blocked';
  risk_assessment: RiskAssessmentResult;
  execution_plan?: ExecutionPlan;  // Optional nếu blocked
  execution_results?: ExecutionResult;
  interpretation?: InterpretationResult;
}
```

**Files:**  
- SỬA `DBAExecutionPlaybook.tsx` interface
- THÊM conditional rendering cho missing stages

---

### 🟢 P2 - TRUNG BÌNH (Testing / Observability)

#### 8. Thêm Integration Tests
**Hành động:**  
- Tạo mock MCP client
- Test full pipeline flow
- Test gate blocking scenarios

**Files cần tạo:**  
```
backend/tests/integration/
  test_dba_pipeline.py
  test_risk_gates.py
  conftest.py (fixtures)
backend/tests/fixtures/
  mock_mcp_responses.json
  test_db_connections.yaml
```

#### 9. Thêm Execution Audit Trail
**Hành động:**  
- Log mọi execution với full context
- Lưu risk decision + execution result
- Link frontend request với backend execution

**Files:**  
- THÊM audit logging trong `pipeline_orchestrator.py`
- TẠO audit table/service

---

### 🔵 P3 - THẤP (Optimization)

#### 10. Deduplicate Gate Logic
**Hành động:**  
- Hợp nhất gate execution vào single service
- Dùng cùng gate runner cho risk simulation VÀ use case execution

**Files:**  
- TẠO `gate_executor_service.py`
- REFACTOR `base_use_case.py` và `risk_assessment_service.py`

---

## TÓM TẮT

### Hệ Thống Có Thể Vận Hành An Toàn Cho DBA Domain Không?

**Kết luận:** ⚠️ **CÓ ĐIỀU KIỆN** với các fix P0 ngay lập tức

**Khía cạnh an toàn:**  
✅ LLM không generate SQL  
✅ LLM không tự execute  
✅ DB executor tuân theo predefined plans  
✅ Raw output contract đã triển khai  
✅ Interpretation layer tách biệt  

**Rủi ro nghiêm trọng:**  
🔴 Duplicate risk assessment (race condition)  
🔴 Không có runtime write/DDL blocking  
🔴 Sandbox mặc định admin role  
🔴 GO-WITH-CONDITIONS bypass validation  

**Hành động khuyến nghị:**  
1. Apply fix P0 TRƯỚC KHI deploy production  
2. Thêm integration tests để verify fixes  
3. Deploy staging với forced `SANDBOX_MODE=true`  
4. Manual QA: test production connection blocking  

**Ước tính timeline:**  
- Fix P0: 2-3 ngày  
- Fix P1: 1 tuần  
- Test P2: 1 tuần  
- Tổng: 2-3 tuần đến production-ready  

---

## PHỤ LỤC: Danh Sách File

### Core DBA Files
```
backend/domain/dba/
  pipeline_orchestrator.py    (432 dòng) - 4-stage pipeline
  risk_assessment_service.py  (547 dòng) - Gate simulation
  execution_plan_generator.py (467 dòng) - Query templates
  db_executor.py              (340 dòng) - Sequential execution
  interpretation_layer.py     (482 dòng) - LLM analysis (stub)
  gates.py                    (299 dòng) - 4 hard gates
  entry_handler.py            (122 dòng) - Intent→use case mapping
  
  use_cases/
    base_use_case.py          (251 dòng) - Gate execution framework
    analyze_slow_query.py     (97 dòng)  - Example use case
    validate_custom_sql.py    (242 dòng) - SQL validation
    (+ 12 use cases khác)

backend/interface/routers/
  dba_routes.py               (528 dòng) - API endpoints

frontend/src/components/
  DBAExecutionPlaybook.tsx    (553 dòng) - 3-tab UI
  DBADashboard.tsx            (262 dòng) - Metrics display
```

### Hạ Tầng Hỗ Trợ
```
backend/router/
  orchestrator.py             (671 dòng) - 5-step routing (KHÔNG DÙNG cho DBA sandbox)
  
backend/schemas/
  dba_types.py               - Type definitions
  
config/
  intent_registry.yaml       (168 dòng) - Intent definitions (13 DBA intents)
```
