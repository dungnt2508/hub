# Sandbox Architecture - Quick Reference Guide

## 🎯 One-Line Summary

**Sandbox = Domain-Specific Risk Simulator** (not generic test suite)

---

## 📊 Domain Comparison Matrix

| Aspect | DBA | HR | Catalog |
|--------|-----|----|----|
| **Risk Level** | 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW |
| **Priority** | 1️⃣ First | 2️⃣ Second | 3️⃣ Third |
| **Risk Type** | Data + Infrastructure | Authorization + Policy | Search Quality |
| **External Deps** | ✓ Real DB connection | ✗ Logic only | ✗ Read-only |
| **Reversibility** | Hard to undo | Easy to undo | Read-only |
| **Critical Risks** | Connection, SQL injection, permissions | RBAC bypass, policy violation | Poor search quality |
| **Failure Modes** | Connection timeout, query fail, metrics loss | Permission denied, quota exceeded | Vector DB fail, bad results |

---

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────┐
│ Admin Dashboard                         │
├─────────────────────────────────────────┤
│ [Routing Sandbox]  [DBA]  [HR]  [Cat]  │
│      ▲              ▲      ▲     ▲     │
│ (Keep)         (New Sandboxes)         │
└─────────────────────────────────────────┘

Each Sandbox = Specific Risk Simulator
  ├─ Own UI layout
  ├─ Own data validation
  ├─ Own risk matrix
  ├─ Own failure scenarios
  └─ Own recommendations
```

---

## 📋 DBA Sandbox Checklist

```
Browser visits: /admin/domain-sandboxes/dba

┌─ Connection Validation
│  ├─ Is connection alive? ✓/✗
│  ├─ User has permissions? ✓/✗
│  ├─ DB type correct? ✓/✗
│  └─ Is production? ⚠/✓
│
├─ Query Safety Check
│  ├─ SQL injection? ✓/✗
│  ├─ Performance OK? ✓/✗
│  ├─ Sensitive columns? ✓/✗
│  └─ Syntax valid? ✓/✗
│
├─ Failure Simulation (Optional)
│  ├─ Connection timeout → handled?
│  ├─ Permission denied → handled?
│  ├─ Query slow → handled?
│  └─ Metrics failed → handled?
│
└─ Risk Score
   └─ CRITICAL / HIGH / MEDIUM / LOW

Result: ✓ Safe to execute / ✗ Issues found
```

---

## 🔴 DBA Critical Risks (Red Flags)

**BLOCK immediately:**
- [ ] Wrong database selected
- [ ] SQL injection detected
- [ ] User lacks permissions
- [ ] On production without confirmation

**REQUIRE APPROVAL:**
- [ ] Query too slow (> 30s)
- [ ] Alert thresholds wrong

**WARN USER:**
- [ ] Sensitive column exposure
- [ ] Table scan (missing WHERE)
- [ ] DB type mismatch

---

## 🟡 HR Critical Risks (Red Flags)

**BLOCK immediately:**
- [ ] Non-manager approving leave
- [ ] Quota exceeded
- [ ] Invalid date range
- [ ] Policy violation

**WARN USER:**
- [ ] Notification might fail
- [ ] Concurrent requests possible

---

## 🟢 Catalog Critical Risks (Red Flags)

**WARN USER:**
- [ ] Search relevance low
- [ ] Vector DB unavailable
- [ ] Results are empty

---

## 💾 API Endpoints (Backend)

### DBA Sandbox APIs
```bash
POST /api/admin/v1/test-sandbox/dba/validate-connection
  body: { connection_id }
  response: { is_alive, permissions, db_type, is_prod }

POST /api/admin/v1/test-sandbox/dba/check-query-safety
  body: { connection_id, sql_query }
  response: { injection_safe, perf_ok, sensitive_cols, syntax_valid }

POST /api/admin/v1/test-sandbox/dba/simulate-failure
  body: { connection_id, scenario }
  response: { handled_gracefully, error_msg_clear, logged }
```

### HR Sandbox APIs
```bash
POST /api/admin/v1/test-sandbox/hr/validate-rbac
  body: { user_id, action }
  response: { allowed, required_role, actual_role }

POST /api/admin/v1/test-sandbox/hr/validate-policy
  body: { employee_id, leave_days }
  response: { quota_ok, no_overlap, policy_compliant }
```

### Catalog Sandbox APIs
```bash
POST /api/admin/v1/test-sandbox/catalog/test-search
  body: { query }
  response: { results, relevance_score, fallback_used }
```

---

## 🎨 UI Component Tree

```
DBA Sandbox
├─ ConnectionValidator
│  └─ displays connection status + permissions
├─ QuerySafetyChecker
│  └─ displays query analysis
├─ FailureSimulator
│  └─ allows selecting failure scenario
└─ RiskAssessmentReport
   ├─ risk level badge
   ├─ critical issues list
   ├─ warnings list
   ├─ passed checks list
   ├─ recommendations
   └─ full trace

Similar tree for HR and Catalog sandboxes...
```

---

## 📊 Risk Scoring Formula

```
risk_score = 1.0 - Σ(check_weight × check_result)

where:
  check_result ∈ [0, 1]  (0 = fail, 1 = pass)
  check_weight = importance of this check

Example (DBA):
  connection_alive:    weight=0.4, result=1.0 → 0.4 points
  user_permissions:    weight=0.3, result=0.0 → 0.0 points (FAIL)
  sql_injection_safe:  weight=0.2, result=1.0 → 0.2 points
  query_performance:   weight=0.1, result=0.5 → 0.05 points
  
  risk_score = 1.0 - (0.4 + 0.0 + 0.2 + 0.05) = 0.35
  risk_level = "MEDIUM" (0.2 < 0.35 < 0.5)
```

---

## ✅ Risk Levels

```
Risk Score    Level      Icon    Action
────────────────────────────────────────
0.0 - 0.2     LOW        🟢      ALLOW
0.2 - 0.5     MEDIUM     🟡      WARN
0.5 - 0.8     HIGH       🔴      REQUIRE_APPROVAL
0.8 - 1.0     CRITICAL   🔴      BLOCK
```

---

## 🎯 Implementation Roadmap

```
Week 1: DBA Sandbox MVP
├─ Connection Validator component
├─ Query Safety Checker component
├─ Backend endpoints
└─ Risk Assessment display

Week 2: DBA Sandbox Polish
├─ Failure Simulator
├─ Edge cases handling
└─ Documentation

Week 3: HR Sandbox
├─ RBAC Validator
├─ Policy Engine
└─ Risk Assessment

Week 4: Catalog Sandbox
├─ Search Quality Tester
└─ Recommendation Analyzer
```

---

## 📁 File Locations

**Frontend:**
```
src/app/admin/domain-sandboxes/
├── page.tsx                    (domain selector)
├── dba/page.tsx                (DBA sandbox)
├── dba/components/...          (DBA components)
├── dba/utils/dba-risk-matrix.json
├── hr/page.tsx                 (HR sandbox)
├── hr/components/...
├── hr/utils/hr-risk-matrix.json
└── catalog/page.tsx            (Catalog sandbox)

src/services/
├── dba-sandbox.service.ts
├── hr-sandbox.service.ts
└── catalog-sandbox.service.ts
```

**Backend:**
```
backend/interface/
└── domain_sandbox_api.py       (all sandbox endpoints)

backend/domain/sandbox/
├── dba_sandbox.py              (DBA logic)
├── hr_sandbox.py               (HR logic)
└── catalog_sandbox.py          (Catalog logic)
```

---

## 🚫 Anti-Patterns (DON'T DO)

```
❌ Generic "Test Everything" button
   → Use domain-specific sandboxes

❌ Shared checklist across domains
   → Each domain has own risk matrix

❌ One "workflow engine"
   → Simulate risks, don't orchestrate

❌ Demo-like UI
   → Expose real failure modes

❌ Copy-paste test cases
   → Each domain tests different things
```

---

## ✨ Key Principles

```
1️⃣ SPECIFICITY
   Each sandbox tests ONLY that domain's risks

2️⃣ REALISTIC
   Test real failure modes, not hypothetical

3️⃣ ACTIONABLE
   Recommendations should be specific and doable

4️⃣ PRODUCTION-READY
   Should work as safety checker in production

5️⃣ MEASURABLE
   Risk score should be meaningful, not arbitrary

6️⃣ FAST
   Assessment should complete in < 5 seconds
```

---

## 📚 Full Documentation Files

- `SANDBOX_STRATEGY.md` - Philosophy + strategies
- `DOMAIN_SANDBOX_ARCHITECTURE.md` - System design
- `DBA_SANDBOX_IMPLEMENTATION.md` - DBA details (START HERE)
- `SANDBOX_CONSULTATION_SUMMARY.md` - This consultation overview

---

## 💡 Example: DBA Flow

```
User: "Check if it's safe to analyze slow queries on PROD_DB"

Step 1: Frontend loads DBA Sandbox
Step 2: User selects connection: PROD_DB
Step 3: User selects scenario: "Analyze Slow Queries"
Step 4: Frontend validates locally (basic checks)
Step 5: Frontend calls: POST /test-sandbox/dba/validate-connection
Step 6: Backend checks connection status + permissions
Step 7: Frontend calls: POST /test-sandbox/dba/check-query-safety
Step 8: Backend validates SQL syntax + injection patterns
Step 9: Frontend shows Risk Assessment:
        - Risk Level: 🟡 MEDIUM
        - Issues: 1 warning (query might be slow)
        - Recommendations: Add WHERE clause
        - Status: ✅ Safe to execute

Result: User can proceed with confidence + knows risks
```

---

## 🔍 Debugging Tips

If risk assessment doesn't match expectations:

1. **Check risk matrix JSON**
   - Verify weights sum to appropriate values
   - Verify severity levels correct

2. **Check formula**
   - Is risk_score = 1.0 - Σ(weight × result)?
   - Are thresholds applied correctly?

3. **Check check logic**
   - Is each check detecting what it should?
   - Are edge cases handled?

4. **Check failure injection**
   - Does simulated failure produce expected error?
   - Is error handling graceful?

5. **Add logging**
   - Log each check result
   - Log final risk_score calculation
   - Log which checks failed/passed

---

## 🎓 Learning Path

1. Read: `SANDBOX_STRATEGY.md` (5 min)
2. Read: `DOMAIN_SANDBOX_ARCHITECTURE.md` (10 min)
3. Read: `DBA_SANDBOX_IMPLEMENTATION.md` (20 min)
4. Review: DBA Risk Matrix JSON
5. Start building: DBA Connection Validator component
6. Reference: This quick guide during implementation
