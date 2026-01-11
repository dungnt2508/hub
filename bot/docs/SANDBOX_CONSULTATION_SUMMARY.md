# Sandbox Architecture Consultation Summary

## 🎯 Vấn đề Nhận Diện

**Bạn chỉ ra:**
> "Routing domain đã ổn rồi, bây h` tôi muốn build thêm sandbox test riêng cho từng domain (dba, hr, catalog,...)"

**Khác với kiến trúc generic mà tôi ban đầu propose:**

| Aspect | Bad (Generic) | Good (Domain-Specific) |
|--------|---------------|------------------------|
| **Philosophy** | Generic test suite cho mọi domain | Risk simulator riêng cho mỗi domain |
| **Focus** | Input validation, error handling, perf | Domain-specific failure modes |
| **Risk Assessment** | Áp dụng uniform checklist | Risk matrix unique per domain |
| **Architecture** | One "Test All" button | Separate sandbox per domain |
| **Result** | Demo-like, generic reports | Production-ready risk profiles |

---

## ✅ Kiến Trúc Tư Vấn - Domain-Specific Sandbox

### 1️⃣ **Philosophy**

```
PRINCIPLE 1: Risk Simulator, Not Test Suite
  - Mục đích: Expose real failure modes before execution
  - Không phải: Generic test checklist
  - Focus: Domain-specific risks

PRINCIPLE 2: Each Domain Has Own Risk Profile
  DBA:     HIGH RISK - Data + Infrastructure - External deps
  HR:      MEDIUM RISK - Authorization + Policy - Mostly logic
  Catalog: LOW RISK - Search Quality - Read-heavy

PRINCIPLE 3: Anti-Patterns to Avoid
  ❌ One generic sandbox for all domains
  ❌ Shared test cases across domains
  ❌ Generic risk scoring
  ❌ "Workflow engine" for orchestration
  ❌ Demo-like UI without real insights
```

### 2️⃣ **Architecture Pattern**

```
Admin Dashboard
│
├── [Routing Sandbox] ← Keep existing
│   └── Test message → domain/intent routing
│
└── [Domain-Specific Sandboxes] ← NEW
    │
    ├─ [DBA Sandbox] (HIGHEST PRIORITY)
    │  ├─ Connection Safety Validator
    │  │  ├─ Is connection alive?
    │  │  ├─ User has permissions?
    │  │  ├─ DB type matches intent?
    │  │  └─ Not on production?
    │  │
    │  ├─ Query Safety Checker
    │  │  ├─ SQL injection detected?
    │  │  ├─ Query performance OK?
    │  │  ├─ Sensitive columns exposed?
    │  │  └─ Syntax valid for DB?
    │  │
    │  ├─ Failure Scenario Injector
    │  │  ├─ Connection timeout
    │  │  ├─ Permission denied
    │  │  ├─ Wrong DB type
    │  │  ├─ Query too slow
    │  │  └─ Metrics storage failed
    │  │
    │  └─ Risk Assessment Report
    │     ├─ Risk score (0-1.0)
    │     ├─ Critical issues
    │     ├─ Warnings
    │     ├─ Recommendations
    │     └─ Full trace
    │
    ├─ [HR Sandbox] (SECOND PRIORITY)
    │  ├─ RBAC Enforcement Tester
    │  ├─ Policy Compliance Validator
    │  ├─ Scenario Simulator (concurrent, quota, dates)
    │  └─ Risk Assessment
    │
    └─ [Catalog Sandbox] (THIRD PRIORITY)
       ├─ Search Quality Tester
       ├─ Recommendation Validator
       └─ Risk Assessment
```

### 3️⃣ **Risk Matrix Pattern**

**DBA Risk Matrix Example:**
```json
{
  "connection_safety": {
    "severity": "CRITICAL",
    "weight": 0.35,
    "checks": {
      "connection_alive": {
        "name": "Connection is Alive",
        "method": "Try to establish connection",
        "failure_impact": "Cannot execute any query",
        "risk_if_missing": "CRITICAL"
      },
      "user_permissions": {
        "name": "User Has Permissions",
        "method": "Check system catalog",
        "failure_impact": "Query execution fails",
        "risk_if_missing": "HIGH"
      }
      // ... more checks
    }
  },
  
  "failure_scenarios": {
    "connection_timeout": {
      "name": "Connection Timeout",
      "expected_behavior": "Graceful error, clear message",
      "acceptable_outcomes": [
        "Error message is clear",
        "Logged for debugging"
      ]
    }
    // ... more scenarios
  }
}
```

**Mỗi domain có risk matrix riêng:**
- DBA: High risk, external dependencies
- HR: Medium risk, authorization critical
- Catalog: Low risk, quality metrics

### 4️⃣ **Implementation Order**

```
Phase 1: DBA Sandbox (START HERE)
├─ Why: Highest risk, most complex, most valuable
├─ What:
│  ├─ Connection validation simulator
│  ├─ SQL safety checker
│  ├─ DB unavailability simulator
│  ├─ Permission denied simulator
│  ├─ Failure scenario injector
│  └─ Risk assessment report
└─ Time: ~1-2 weeks

Phase 2: HR Sandbox
├─ Why: Authorization is critical, easy to test with mocks
├─ What:
│  ├─ RBAC enforcement tester
│  ├─ Policy violation detector
│  ├─ Concurrent request simulator
│  └─ Notification delivery tracker
└─ Time: ~1 week

Phase 3: Catalog Sandbox
├─ Why: Read-only, lower business impact
├─ What:
│  ├─ Search quality tester
│  ├─ Recommendation analyzer
│  └─ Vector DB fallback tester
└─ Time: ~1 week
```

---

## 📊 DBA Sandbox Deep-Dive

### Risk Profile

```
DBA Domain Risks (by severity):

🔴 CRITICAL (Block execution):
   • Wrong database selected
   • SQL injection detected
   • User lacks permissions
   • Query on production without warning

🔴 HIGH (Require approval):
   • Query performance too high (DoS risk)
   • Alert thresholds incorrect

🟡 MEDIUM (Warn user):
   • Metrics storage might fail
   • DB type mismatch
   • Sensitive columns exposed
```

### Key Components

**1. Connection Validator**
```
Input: Connection ID
Process:
  - Check connection is alive
  - Verify user permissions
  - Identify DB type
  - Check if production
Output:
  - Connection status
  - Permission matrix
  - DB type
  - Production warning
```

**2. Query Safety Checker**
```
Input: SQL query
Process:
  - Parse SQL syntax
  - Scan for injection patterns
  - Estimate rows/complexity
  - Check sensitive columns
Output:
  - Safety assessment
  - Performance impact
  - Column exposure report
```

**3. Failure Injector**
```
Input: Failure scenario
Process:
  - Simulate specified failure
  - Check error handling
  - Verify fallback works
Output:
  - Was failure handled gracefully?
  - Error message quality
  - Logging completeness
```

**4. Risk Assessment**
```
Input: All check results
Process:
  - Apply DBA risk matrix
  - Calculate risk score
  - Generate recommendations
Output:
  - Risk level (CRITICAL/HIGH/MEDIUM/LOW)
  - Critical issues list
  - Warnings list
  - Actionable recommendations
  - Full trace for debugging
```

---

## 🎨 UI Pattern

### DBA Sandbox UI Flow

```
┌─────────────────────────────────────────────┐
│ DBA Risk Simulator                          │
├─────────────────────────────────────────────┤
│                                              │
│ STEP 1: Select Connection                  │
│ [PROD_DB ▼] - 🔴 Production (Be careful!)  │
│              - Type: SQL Server             │
│              - Status: 🟢 Alive            │
│                                              │
│ STEP 2: Input Query or Select Scenario     │
│ [Analyze Slow Queries ▼]                   │
│ or paste custom SQL...                     │
│                                              │
│ STEP 3: Simulate Failure? (Optional)       │
│ □ Connection Timeout                       │
│ □ Permission Denied                        │
│ □ Query Too Slow                           │
│                                              │
│ [RUN RISK ASSESSMENT]                      │
│                                              │
├─────────────────────────────────────────────┤
│ ✅ ASSESSMENT RESULT                        │
├─────────────────────────────────────────────┤
│                                              │
│ Risk Level: 🟡 MEDIUM (Score: 0.42)        │
│                                              │
│ 🔴 Critical Issues (0)                     │
│    None ✓                                   │
│                                              │
│ 🟡 Warnings (2)                            │
│    • Query performance: HIGH impact         │
│    • Missing WHERE clause (table scan)      │
│                                              │
│ 🟢 Checks Passed (5)                       │
│    ✓ Connection alive                      │
│    ✓ User has SELECT permission            │
│    ✓ SQL injection safe                    │
│    ✓ DB type correct (SQL Server)          │
│    ✓ Not on production without warning     │
│                                              │
│ 💡 Recommendations:                        │
│    1. Add WHERE clause to limit rows       │
│    2. Use specific column list              │
│    3. Test on DEV_DB first                 │
│                                              │
│ [View Full Trace] [Export Report]          │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 📋 File Structure (Frontend)

```
bot/frontend/src/app/admin/domain-sandboxes/
│
├─ page.tsx                             (Domain selector)
│
├─ dba/
│  ├─ page.tsx                          (DBA Sandbox main)
│  ├─ components/
│  │  ├─ ConnectionValidator.tsx
│  │  ├─ QuerySafetyChecker.tsx
│  │  ├─ FailureSimulator.tsx
│  │  └─ RiskAssessmentReport.tsx
│  ├─ hooks/
│  │  ├─ useConnectionTest.ts
│  │  ├─ useQueryValidation.ts
│  │  └─ useRiskAssessment.ts
│  └─ utils/
│     ├─ dba-risk-matrix.json
│     └─ dba-scenarios.ts
│
├─ hr/
│  ├─ page.tsx
│  ├─ components/
│  │  ├─ RBACTester.tsx
│  │  ├─ PolicyValidator.tsx
│  │  └─ RiskAssessmentReport.tsx
│  ├─ hooks/
│  └─ utils/
│     └─ hr-risk-matrix.json
│
└─ catalog/
   ├─ page.tsx
   ├─ components/
   ├─ hooks/
   └─ utils/

bot/frontend/src/services/
├─ domain-sandbox.service.ts            (Base service)
├─ dba-sandbox.service.ts               (DBA-specific)
├─ hr-sandbox.service.ts                (HR-specific)
└─ catalog-sandbox.service.ts           (Catalog-specific)
```

---

## 📚 Backend APIs (New)

```
POST /api/admin/v1/test-sandbox/dba/validate-connection
├─ Input: connection_id
└─ Output: ConnectionValidationResult

POST /api/admin/v1/test-sandbox/dba/check-query-safety
├─ Input: connection_id, sql_query
└─ Output: QuerySafetyResult

POST /api/admin/v1/test-sandbox/dba/simulate-failure
├─ Input: connection_id, scenario
└─ Output: FailureSimulationResult

POST /api/admin/v1/test-sandbox/hr/validate-rbac
├─ Input: user_id, action
└─ Output: RBACValidationResult

POST /api/admin/v1/test-sandbox/hr/validate-policy
├─ Input: policy_type, parameters
└─ Output: PolicyValidationResult

POST /api/admin/v1/test-sandbox/catalog/test-search
├─ Input: query, criteria
└─ Output: SearchQualityResult
```

---

## ✅ Success Criteria

### DBA Sandbox
- ✓ No false negatives (real risks detected)
- ✓ No false positives (safe operations pass)
- ✓ All failure modes covered
- ✓ < 5 seconds to run assessment
- ✓ Risk score is meaningful
- ✓ Error messages are clear and actionable

### HR Sandbox
- ✓ RBAC cannot be bypassed
- ✓ All policy rules tested
- ✓ Concurrent conflicts handled
- ✓ Audit trail complete
- ✓ Notifications working

### Catalog Sandbox
- ✓ Search quality measurable
- ✓ Vector DB fallbacks work
- ✓ No false recommendations

---

## 🚫 Anti-Patterns to Avoid

❌ **One generic test runner** for all domains
  → Each domain needs custom logic

❌ **Shared test cases** across domains
  → DBA tests ≠ HR tests ≠ Catalog tests

❌ **Generic risk scoring**
  → DBA risks ≠ HR risks; different weights

❌ **"Workflow engine"** for orchestration
  → Just simulate risks; don't chain operations

❌ **Demo-like UI** without real insights
  → Must expose actual failure modes

---

## 📖 Documentation Structure

We've created:

1. **SANDBOX_STRATEGY.md**
   - Philosophy: Sandbox = Risk Simulator
   - Each domain's risk profile
   - Anti-patterns to avoid

2. **DOMAIN_SANDBOX_ARCHITECTURE.md**
   - High-level system design
   - File structure (frontend + backend)
   - Request/response flow
   - Comparison: bad vs good design

3. **DBA_SANDBOX_IMPLEMENTATION.md** ← START HERE
   - DBA-specific risk profile
   - Complete risk matrix (JSON)
   - Component breakdown
   - Implementation steps
   - UI layout with examples

4. **This file (SANDBOX_CONSULTATION_SUMMARY.md)**
   - Overview of consultation
   - Key decisions
   - Why this architecture

Next to create (when implementing):
- **HR_SANDBOX_IMPLEMENTATION.md**
- **CATALOG_SANDBOX_IMPLEMENTATION.md**

---

## 🎯 Next Steps

### For You:
1. Review **DBA_SANDBOX_IMPLEMENTATION.md** thoroughly
2. Decide if risk matrix aligns with your understanding
3. Identify any additional DBA-specific risks we missed
4. Confirm DBA domain is the right starting point

### For Implementation:
1. Create DBA sandbox page structure
2. Build Connection Validator component
3. Build Query Safety Checker component
4. Build Failure Simulator
5. Build Risk Assessment display
6. Create backend endpoints
7. Test end-to-end

### Timeline:
- DBA Sandbox: ~1-2 weeks
- HR Sandbox: ~1 week
- Catalog Sandbox: ~1 week
- Total: ~3-4 weeks

---

## ❓ Questions for You

1. **DBA Risk Matrix**: Does the risk matrix capture your top concerns?
2. **Risk Severity**: Are the severity levels (CRITICAL/HIGH/MEDIUM/LOW) correct?
3. **Failure Scenarios**: Are there failure modes we missed?
4. **Starting Point**: Confirm DBA sandbox first, then HR, then Catalog?
5. **Integration**: Should DBA sandbox integrate with existing connections registry?

---

## 💬 Key Takeaway

> **Sandbox là risk simulator riêng cho từng domain, không phải generic test suite.**

Mỗi domain:
- Có risk profile khác nhau
- Có dependency khác nhau
- Có failure modes khác nhau
- Cần risk matrix riêng

Kết quả:
- Production-ready, không demo-like
- Actionable recommendations
- Real safety verification
- Domain experts approve the logic
