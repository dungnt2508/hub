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

### Use Case Registry Trùng Lặp - CRITICAL

**Files:**  
- `domain/dba/entry_handler.py` L48-60 (đăng ký 11 use cases)
- `dba_routes.py` L29-146 (hardcoded 11 use cases với metadata)
- `domain/use_case_registry.py` L78-96 (discover từ entry_handler, thiếu metadata)
- `config/intent_registry.yaml` L64-168 (13 intents, không được dùng cho sandbox)
- `domain/dba/use_cases/__init__.py` (export 13 use cases, chỉ 11 được đăng ký)

**Vấn đề chi tiết:**

1. **Entry Handler vs Routes:**
   - `entry_handler.py`: Đăng ký 11 use cases (class instances)
   - `dba_routes.py`: Hardcode 11 use cases với metadata (name, description, icon, slots)
   - Metadata chỉ có trong routes, KHÔNG có trong entry_handler

2. **Use Case Registry thiếu metadata:**
   - `use_case_registry.py` discover từ entry_handler
   - Chỉ có intent names, THIẾU: description, icon, slots, playbook mapping

3. **Use Case count mismatch:**
   - Entry handler: 11 use cases
   - Routes: 11 use cases
   - `__init__.py`: 13 use cases (thêm `store_query_metrics`, `get_active_alerts`)
   - Intent registry: 13 intents
   - `store_query_metrics`, `get_active_alerts` KHÔNG được đăng ký trong entry_handler

4. **Playbook mapping hardcoded:**
   - `dba_routes.py` L455-465: playbook_map chỉ có 7 mappings
   - Thiếu mapping cho: `analyze_query_regression`, `validate_custom_sql`, `compare_sp_blitz_vs_custom`, `incident_triage`

**Tác động:**  
- Cùng dữ liệu use case ở 4+ nơi (entry_handler, routes, registry, yaml)
- Phải sync thủ công khi thêm/sửa use case
- Dễ xảy ra inconsistency (ví dụ: 11 vs 13 use cases)
- Metadata (description, icon) không được centralize
- Playbook mapping thiếu và hardcoded

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

## 7. NỢ KỸ THUẬT: DANH SÁCH VẤN ĐỀ

### 🔴 CRITICAL - Security & Correctness

1. **Duplicate Risk Assessment** (L431-440)
   - Risk được chạy 2 lần (frontend + backend)
   - Race condition, kết quả không nhất quán

2. **Runtime Write/DDL Not Enforced** (db_executor.py)
   - ExecutionStep có `read_only: True` nhưng không validate
   - Không block INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE

3. **Sandbox Defaults to Admin Role** (dba_routes.py L341, L415)
   - Sandbox mode mặc định `role="admin"`
   - Bypass production safety gates

4. **GO-WITH-CONDITIONS Bypass** (dba_routes.py L442-448)
   - Conditions không được validate/enforce
   - User có thể execute mà không acknowledge

### 🟡 STRUCTURAL - Architecture & Maintainability

5. **Use Case Registry Duplication** (4+ locations)
   - `entry_handler.py`: 11 use cases (instances)
   - `dba_routes.py`: 11 use cases (metadata)
   - `use_case_registry.py`: Discover từ entry_handler (thiếu metadata)
   - `intent_registry.yaml`: 13 intents (không dùng cho sandbox)
   - `__init__.py`: 13 exports (2 use cases không đăng ký)
   - Playbook mapping hardcoded, thiếu mappings

6. **Dead Routing Code** (router/orchestrator.py)
   - Routing layer không được dùng cho DBA sandbox
   - Intent registry có 13 DBA intents nhưng không được route

7. **Gate Execution Duplication** (3 locations)
   - Risk simulation (risk_assessment_service.py)
   - Playbook execution re-run (dba_routes.py L431)
   - Use case execution (base_use_case.py)
   - Cùng logic gates được thực thi 2-3 lần

8. **Frontend Type Safety Violation** (DBAExecutionPlaybook.tsx)
   - Interface không đánh dấu optional fields
   - Runtime error khi NO-GO (execution_results = undefined)

### 🟢 COSMETIC - Testing & Observability

9. **Missing Integration Tests**
   - Không có test cho pipeline execution
   - Không có mock MCP client
   - Không có test gate blocking scenarios

10. **Missing Audit Trail**
    - Không log execution context đầy đủ
    - Không link frontend request với backend execution
    - Không lưu risk decision history

---

## 8. KIẾN TRÚC MỤC TIÊU

### 8.1. Use Case Management - Single Source of Truth

**Nguyên tắc:**
- TẤT CẢ use case metadata tại MỘT nơi duy nhất
- Entry handler là source of truth cho use case instances
- Metadata (description, icon, slots, playbook) được định nghĩa cùng với use case class
- Không cho phép hardcode use case list ở routes hoặc registry

**Cấu trúc mục tiêu:**

```
domain/dba/use_cases/
  __init__.py              # Export all use cases
  base_use_case.py         # Base class với metadata decorator
  analyze_slow_query.py    # Use case class + metadata
  ...

domain/dba/
  use_case_metadata.py     # NEW: Centralized metadata registry
  entry_handler.py         # Discover từ use_case_metadata
```

**Metadata Schema:**

```python
@dataclass
class UseCaseMetadata:
    id: str                      # "analyze_slow_query"
    name: str                    # "Analyze Slow Queries"
    description: str
    icon: str                    # "📊"
    intent: str                  # Same as id
    required_slots: List[str]
    optional_slots: List[str]
    source_allowed: List[str]    # ["OPERATION"]
    playbook_name: Optional[str] # "QUERY_PERFORMANCE"
    use_case_class: Type[BaseUseCase]
```

**Discovery Flow:**

```
UseCaseMetadataRegistry
  ↓ (load từ use case classes)
DBAEntryHandler
  ↓ (register instances)
UseCaseRegistry (global)
  ↓ (discover từ entry handlers)
Routes/API endpoints
```

### 8.2. Pipeline Architecture - Single Risk Assessment

**Nguyên tắc:**
- Risk assessment CHỈ chạy 1 LẦN
- Kết quả risk được cache và reuse
- Frontend request ID link với backend execution ID

**Flow mục tiêu:**

```
Frontend: /risk-assessment
  ↓
Backend: Run risk (LẦN ĐẦU)
  ↓
Return: RiskAssessmentResult + risk_id
  ↓
Frontend: Store risk_id, show to user
  ↓
User: Click Execute
  ↓
Frontend: /execute-playbook?risk_id=xxx
  ↓
Backend: Load risk từ cache/DB (KHÔNG chạy lại)
  ↓
Backend: Execute pipeline stages 2-4
```

### 8.3. Security Boundaries - Runtime Enforcement

**Nguyên tắc:**
- Read-only enforcement tại runtime (không trust metadata)
- Sandbox mode BẮT BUỘC viewer role
- Production connection registry (explicit, không heuristic)

**Enforcement Points:**

1. **SQL Validation** (db_executor.py):
   ```python
   # Validate TRƯỚC execution
   dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
   if any(kw in step.query.upper() for kw in dangerous_keywords):
       raise SecurityViolation(f"Write operation blocked: {step.type}")
   ```

2. **Sandbox Role Enforcement** (dba_routes.py):
   ```python
   if os.getenv("SANDBOX_MODE") == "true":
       user_role = "viewer"  # Bắt buộc
   ```

3. **Production Registry** (connection_registry.py):
   ```python
   # Explicit environment mapping
   connection.environment = "production" | "staging" | "development"
   # Sandbox chỉ cho phép staging/dev
   ```

### 8.4. Gate Execution - Single Source

**Nguyên tắc:**
- Gate logic tại MỘT nơi duy nhất
- Risk simulation và use case execution dùng CÙNG gate runner
- Không duplicate gate logic

**Cấu trúc mục tiêu:**

```
domain/dba/gates/
  gate_executor.py        # NEW: Single gate execution service
  production_gate.py      # Gate implementations
  scope_gate.py
  permission_gate.py
  validation_gate.py

domain/dba/
  risk_assessment_service.py  # Use gate_executor
  base_use_case.py            # Use gate_executor
```

---

## 9. KẾ HOẠCH SỬA (THỨ TỰ ƯU TIÊN)

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

#### 6. Chuẩn Hóa Use Case Registry - Single Source of Truth
**Vấn đề:** Use case metadata ở 4+ nơi, không nhất quán

**Phase 1: Tạo Use Case Metadata Registry**
**Hành động:**  
1. Tạo `domain/dba/use_case_metadata.py`:
```python
   @dataclass
   class UseCaseMetadata:
       id: str
       name: str
       description: str
       icon: str
       intent: str
       required_slots: List[str]
       optional_slots: List[str]
       source_allowed: List[str]
       playbook_name: Optional[str]
       use_case_class: Type[BaseUseCase]
   
   class DBAUseCaseMetadataRegistry:
       _metadata: Dict[str, UseCaseMetadata] = {}
       
       @classmethod
       def register(cls, metadata: UseCaseMetadata):
           cls._metadata[metadata.id] = metadata
       
       @classmethod
       def get_all(cls) -> List[UseCaseMetadata]:
           return list(cls._metadata.values())
   ```

2. Thêm metadata decorator vào base_use_case.py:
   ```python
   def use_case_metadata(
       name: str,
       description: str,
       icon: str,
       required_slots: List[str],
       optional_slots: List[str],
       playbook_name: Optional[str] = None
   ):
       def decorator(cls):
           # Register metadata
           return cls
       return decorator
   ```

**Phase 2: Migrate Use Cases**
**Hành động:**
1. Thêm metadata decorator vào mỗi use case class
2. Đăng ký metadata trong `__init__.py` hoặc auto-discover
3. Update entry_handler để load từ metadata registry

**Phase 3: Update Routes và Registry**
**Hành động:**
1. `dba_routes.py` get_dba_use_cases: Load từ metadata registry
2. `use_case_registry.py`: Load metadata từ entry_handler
3. Xóa hardcoded use case list trong routes
4. Xóa playbook_map hardcoded, dùng playbook_name từ metadata

**Phase 4: Fix Use Case Count Mismatch**
**Hành động:**
1. Quyết định: `store_query_metrics`, `get_active_alerts` có được dùng trong sandbox?
   - NẾU CÓ: Thêm vào entry_handler và metadata
   - NẾU KHÔNG: Document rằng 2 use cases này chỉ dùng cho internal/routing
2. Sync count giữa entry_handler, routes, registry, yaml

**Files:**  
- TẠO `domain/dba/use_case_metadata.py`
- SỬA `domain/dba/use_cases/base_use_case.py` (thêm decorator)
- SỬA `domain/dba/use_cases/*.py` (thêm metadata decorator)
- SỬA `domain/dba/entry_handler.py` (load từ metadata)
- SỬA `dba_routes.py` get_dba_use_cases (load từ metadata)
- SỬA `dba_routes.py` execute_playbook (dùng playbook_name từ metadata)
- SỬA `domain/use_case_registry.py` (load metadata từ entry_handler)

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
1. Tạo `domain/dba/gates/gate_executor.py`:
   ```python
   class GateExecutor:
       async def execute_gates(
           self,
           request: DomainRequest,
           connection: Any,
           simulate: bool = False
       ) -> GateExecutionResult:
           # Execute all 4 gates
           # simulate=True: không raise exception, chỉ return status
           # simulate=False: raise exception nếu block
   ```

2. Refactor:
   - `risk_assessment_service.py`: Dùng GateExecutor với simulate=True
   - `base_use_case.py`: Dùng GateExecutor với simulate=False
   - Xóa duplicate gate logic

**Files:**  
- TẠO `domain/dba/gates/gate_executor.py`
- REFACTOR `risk_assessment_service.py`
- REFACTOR `base_use_case.py`

---

## 10. QUY TẮC VẬN HÀNH

### 10.1. Use Case Management

**Quy tắc:**
1. **TẤT CẢ use case phải được định nghĩa tại MỘT nơi:**
   - Use case class: `domain/dba/use_cases/{use_case_id}.py`
   - Metadata: Sử dụng decorator `@use_case_metadata()` trong class
   - KHÔNG hardcode use case list ở routes, registry, hoặc config files

2. **Khi thêm use case mới:**
   - Tạo file `{use_case_id}.py` trong `use_cases/`
   - Thêm `@use_case_metadata()` decorator với đầy đủ metadata
   - Export trong `use_cases/__init__.py`
   - Metadata registry tự động discover (không cần đăng ký thủ công)
   - KHÔNG cần sửa `dba_routes.py`, `use_case_registry.py`, hoặc `intent_registry.yaml`

3. **Khi sửa use case metadata:**
   - Chỉ sửa tại class definition (decorator)
   - Tất cả nơi khác tự động update (entry_handler, routes, registry)

4. **Validation:**
   - CI/CD check: So sánh use case count giữa entry_handler và metadata registry
   - CI/CD check: Validate metadata đầy đủ (name, description, icon, slots, playbook)

### 10.2. Risk Assessment

**Quy tắc:**
1. Risk assessment CHỈ chạy 1 LẦN per request
2. Kết quả risk được cache với TTL (ví dụ: 5 phút)
3. `/execute-playbook` BẮT BUỘC nhận `risk_id` hoặc `force_rerun=true`
4. Nếu `force_rerun=true`: Log warning + audit trail

### 10.3. Security Enforcement

**Quy tắc:**
1. **Read-only enforcement:**
   - SQL validation TRƯỚC execution (không trust metadata)
   - Block: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE
   - Exception: SecurityViolation

2. **Sandbox mode:**
   - `SANDBOX_MODE=true`: BẮT BUỘC `role="viewer"`
   - Sandbox KHÔNG cho phép production connections
   - Production connections phải có explicit environment tag

3. **GO-WITH-CONDITIONS:**
   - BẮT BUỘC log warning với conditions
   - Frontend phải show conditions và require user acknowledgment
   - Audit trail ghi lại conditions và user decision

### 10.4. Gate Execution

**Quy tắc:**
1. Gate logic tại MỘT nơi: `gates/gate_executor.py`
2. Risk simulation và use case execution dùng CÙNG gate executor
3. KHÔNG duplicate gate logic
4. Khi thêm gate mới: Chỉ thêm vào gate_executor

### 10.5. Testing

**Quy tắc:**
1. Mỗi use case phải có unit test
2. Pipeline execution phải có integration test
3. Gate blocking scenarios phải có test
4. Security violations phải có test (SQL blocking, role enforcement)

### 10.6. Documentation

**Quy tắc:**
1. Use case metadata (description) phải rõ ràng, đủ để frontend hiển thị
2. Playbook mapping phải được document trong metadata
3. Breaking changes phải được document trong CHANGELOG
4. File này (`dba_architecture_review.md`) là single source of truth cho architecture

---

## TÓM TẮT

### Hệ Thống Có Thể Vận Hành An Toàn Cho DBA Domain Không?

**Kết luận:** ⚠️ **CÓ ĐIỀU KIỆN** với các fix P0 ngay lập tức + chuẩn hóa use case management

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
🔴 Use case registry duplication (4+ locations, không nhất quán)

**Hành động khuyến nghị:**  
1. Apply fix P0 TRƯỚC KHI deploy production  
2. Chuẩn hóa use case management (P1 Phase 1-2)  
3. Thêm integration tests để verify fixes  
4. Deploy staging với forced `SANDBOX_MODE=true`  
5. Manual QA: test production connection blocking  

**Ước tính timeline:**  
- Fix P0: 2-3 ngày  
- Use Case Standardization (P1 Phase 1-2): 1 tuần  
- Fix P1 còn lại: 1 tuần  
- Test P2: 1 tuần  
- Tổng: 3-4 tuần đến production-ready  

---

---

## 11. PHỤ LỤC: Query Templates Duplication

### Vấn đề: 2 file query_templates.py

**Files:**
1. `backend/domain/dba/query_templates.py` - ❌ DEAD CODE (không được dùng)
2. `mcp_server/query_templates.py` - ✅ Được dùng bởi MCP server
3. `execution_plan_generator.py` - ✅ Hardcode queries trong code

**Vấn đề:**
- Queries được định nghĩa ở 2 nơi (execution_plan_generator và mcp_server)
- Không có single source of truth
- `backend/domain/dba/query_templates.py` là dead code

**Giải pháp:**
- Xóa `backend/domain/dba/query_templates.py` (dead code)
- Document rõ queries ở 2 nơi
- Xem `docs/dba_query_templates_analysis.md` để biết thêm chi tiết

### Frontend View/Edit Queries

**VIEW (Read-only):** ✅ ĐƯỢC PHÉP
- Hiển thị queries trong execution plan
- User có thể review trước khi execute
- Không có security risk

**EDIT (Write):** ❌ KHÔNG ĐƯỢC PHÉP
- Security risk cao (SQL injection)
- Vi phạm design principle "predefined queries only"
- Runtime enforcement không đủ để validate user-edited queries

**ADMIN EDIT (Controlled):** ⚠️ CÓ THỂ (nếu thực sự cần)
- Chỉ admin role
- Validation và security checks
- Database storage với versioning
- Xem `docs/dba_query_templates_analysis.md` để biết thêm chi tiết

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
