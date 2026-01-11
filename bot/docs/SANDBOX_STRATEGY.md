# Domain-Specific Sandbox Strategy

## 🎯 Philosophy
Sandbox **không phải generic test suite**. Mỗi domain có **risk profile riêng**, **dependencies riêng**, **failure modes riêng**. Sandbox là **risk simulator**, không phải workflow engine.

---

## 📊 Domain Risk Profiles

### 1. **DBA Domain** - HIGH RISK / EXTERNAL DEPENDENCY
```
Risk Category: DATA + INFRASTRUCTURE
┌─────────────────────────────────────────────┐
│ Critical Risks:                              │
│ ❌ Wrong database selected                  │
│ ❌ SQL injection in custom queries          │
│ ❌ Connection failure/timeout               │
│ ❌ Insufficient permissions on DB           │
│ ❌ Performance regression detection wrong   │
│ ❌ False positive deadlock detection        │
│ ❌ Query analysis on wrong DB type          │
│ ❌ Metrics stored to wrong connection       │
└─────────────────────────────────────────────┘

Dependencies:
  - Real database connection (MCP client)
  - Connection registry
  - Metrics history storage
  - Alert system
  
Failure Points:
  - Connection validation failed
  - Query execution permission denied
  - Database type mismatch
  - Metrics storage failed
  - Alert not triggered
  
Sandbox Purpose:
  ✓ Test connection selection logic
  ✓ Verify SQL is safe before execution
  ✓ Simulate DB unavailability
  ✓ Test fallback when analysis fails
  ✓ Verify metrics are persisted correctly
  ✓ Test alert triggering conditions
```

### 2. **HR Domain** - MEDIUM RISK / POLICY VALIDATION
```
Risk Category: AUTHORIZATION + BUSINESS LOGIC
┌─────────────────────────────────────────────┐
│ Critical Risks:                              │
│ ❌ Non-manager approving leave              │
│ ❌ Employee exceeding leave quota           │
│ ❌ Policy not applied correctly             │
│ ❌ Unauthorized data access                 │
│ ❌ Invalid date ranges                      │
│ ❌ Concurrent request conflicts             │
│ ❌ Notification not sent                    │
└─────────────────────────────────────────────┘

Dependencies:
  - Employee repository
  - RBAC middleware
  - Policy engine
  - Notification service
  - Leave balance cache

Failure Points:
  - User not found
  - Insufficient permissions
  - Leave balance < requested days
  - Overlapping leave requests
  - Notification delivery failed
  - Policy mismatch

Sandbox Purpose:
  ✓ Test RBAC enforcement
  ✓ Verify policy application
  ✓ Simulate permission denial
  ✓ Test leave balance calculation
  ✓ Test concurrent request handling
  ✓ Test notification delivery
  ✓ Verify audit trail
```

### 3. **Catalog Domain** - LOW RISK / READ-HEAVY
```
Risk Category: SEARCH QUALITY + RECOMMENDATIONS
┌─────────────────────────────────────────────┐
│ Critical Risks:                              │
│ ❌ Search returns wrong products            │
│ ❌ Recommendation is irrelevant             │
│ ❌ Vector search fails silently             │
│ ❌ Fallback not triggered                   │
│ ❌ Pagination broken                        │
│ ❌ Ranking is poor quality                  │
└─────────────────────────────────────────────┘

Dependencies:
  - Vector database (embeddings)
  - Product catalog
  - Search index
  - RAG retriever
  
Failure Points:
  - Embedding generation failed
  - Vector search timeout
  - No results returned
  - Irrelevant results
  - Ranking mismatch
  
Sandbox Purpose:
  ✓ Test search quality metrics
  ✓ Verify ranking algorithms
  ✓ Test fallback to keyword search
  ✓ Simulate vector DB unavailable
  ✓ Test pagination edge cases
  ✓ Verify recommendation diversity
```

---

## 🏗️ Sandbox Architecture Pattern

```
TestSandbox/
├── domain-specific sandboxes/
│
├── DBA Sandbox
│   ├── fixtures/
│   │   ├── mock_connections.ts       # Pre-configured DB connections
│   │   ├── mock_queries.ts           # Sample slow/problematic queries
│   │   ├── mock_metrics.ts           # Historical metrics data
│   │   └── mock_alerts.ts            # Alert scenarios
│   │
│   ├── scenarios/
│   │   ├── connection_failures/      # Test connection issues
│   │   ├── permission_denied/        # Test auth failures
│   │   ├── wrong_db_type/            # Test DB mismatch detection
│   │   ├── query_performance/        # Test analysis accuracy
│   │   ├── metrics_persistence/      # Test metrics storage
│   │   └── alert_triggering/         # Test alert conditions
│   │
│   ├── risk_matrix/                  # Risk severity mapping
│   │   └── dba_risks.json
│   │
│   └── dba-sandbox.tsx               # DBA-specific UI
│
├── HR Sandbox
│   ├── fixtures/
│   │   ├── mock_employees.ts
│   │   ├── mock_policies.ts
│   │   ├── mock_permissions.ts
│   │   └── mock_leave_data.ts
│   │
│   ├── scenarios/
│   │   ├── rbac_violations/          # Permission tests
│   │   ├── policy_breaches/          # Policy tests
│   │   ├── quota_exceeded/           # Balance tests
│   │   ├── concurrent_requests/      # Race condition tests
│   │   └── notification_failures/    # Notification tests
│   │
│   ├── policy_engine/                # Policy validation
│   │   └── policy_rules.json
│   │
│   └── hr-sandbox.tsx                # HR-specific UI
│
├── Catalog Sandbox
│   ├── fixtures/
│   │   ├── mock_products.ts
│   │   ├── mock_embeddings.ts
│   │   └── mock_search_index.ts
│   │
│   ├── scenarios/
│   │   ├── search_quality/           # Relevance tests
│   │   ├── vector_failures/          # VectorDB tests
│   │   ├── ranking_issues/           # Ranking tests
│   │   └── fallback_behavior/        # Fallback tests
│   │
│   └── catalog-sandbox.tsx           # Catalog-specific UI
│
└── shared/
    ├── sandbox-base.tsx              # Base component
    ├── scenario-runner.ts            # Scenario execution engine
    └── risk-formatter.ts             # Risk display utilities
```

---

## 🚀 Implementation Order

### **Phase 1: DBA Sandbox** (Critical)
**Why first?**
- Highest risk (external DB access)
- Most complex failure modes
- Most valuable for safety
- Many dependencies to test

**What to build:**
1. Connection validation simulator
2. SQL safety checker
3. DB unavailability simulator
4. Permission denied simulator
5. Metrics persistence verifier
6. Alert trigger validator

### **Phase 2: HR Sandbox** (Important)
**Why second?**
- Authorization is critical
- Policy violations are hard to catch
- Concurrent request issues
- Easy to test with mocks

**What to build:**
1. RBAC enforcement tester
2. Policy violation detector
3. Leave balance calculator
4. Concurrent request simulator
5. Notification delivery tracker

### **Phase 3: Catalog Sandbox** (Nice-to-have)
**Why last?**
- Read-only operations (less risky)
- Can be tested without mocks
- Quality metrics are subjective
- Lower business impact

---

## 📋 Domain-Specific Checklist Pattern

### ❌ **Anti-Pattern: Generic Checklist**
```tsx
// BAD - Generic checklist reused everywhere
const GeneralTestChecklist = [
  "Input validation",
  "Error handling",
  "Performance",
  "Authorization"
];
// ❌ Doesn't capture domain-specific risks!
```

### ✅ **Good Pattern: Domain-Specific Risk Matrix**

**DBA Sandbox Risk Matrix:**
```json
{
  "connection_selection": {
    "severity": "CRITICAL",
    "tests": ["right_db_selected", "permission_check", "connection_alive"],
    "acceptance": "100% pass required"
  },
  "query_analysis": {
    "severity": "HIGH",
    "tests": ["sql_injection_safe", "performance_acceptable", "permissions_ok"],
    "acceptance": "100% pass required"
  },
  "metrics_storage": {
    "severity": "MEDIUM",
    "tests": ["metrics_persisted", "timestamps_correct", "aggregations_accurate"],
    "acceptance": "100% pass required"
  },
  "alert_triggering": {
    "severity": "HIGH",
    "tests": ["correct_threshold_used", "alert_sent", "alert_content_accurate"],
    "acceptance": "100% pass required"
  }
}
```

**HR Sandbox Risk Matrix:**
```json
{
  "authorization_enforcement": {
    "severity": "CRITICAL",
    "tests": ["manager_role_required", "no_bypass_possible", "audit_logged"],
    "acceptance": "100% pass required"
  },
  "policy_compliance": {
    "severity": "CRITICAL",
    "tests": ["leave_balance_enforced", "date_overlap_prevented", "quota_respected"],
    "acceptance": "100% pass required"
  },
  "notification_delivery": {
    "severity": "MEDIUM",
    "tests": ["notification_sent", "correct_recipient", "timestamp_recorded"],
    "acceptance": "100% pass required"
  }
}
```

---

## 🔧 Frontend Implementation Example (DBA Sandbox)

```tsx
// What DBA Sandbox should show:

┌─────────────────────────────────────────────────┐
│ DBA Risk Simulator                              │
├─────────────────────────────────────────────────┤
│                                                  │
│ 📊 Risk Matrix                                  │
│ ┌─────────────────────────────────────────┐    │
│ │ Connection Selection  [🔴 CRITICAL]     │    │
│ │ ├─ Right DB selected  [✓ PASS]         │    │
│ │ ├─ Permission check   [✗ FAIL]         │    │
│ │ └─ Connection alive   [✓ PASS]         │    │
│ │                                          │    │
│ │ Query Analysis        [🟡 HIGH]         │    │
│ │ ├─ SQL injection safe [✓ PASS]         │    │
│ │ ├─ Performance ok     [⚠ WARN]         │    │
│ │ └─ Permissions ok     [✓ PASS]         │    │
│ │                                          │    │
│ │ Metrics Storage       [🟢 MEDIUM]       │    │
│ │ ├─ Metrics persisted  [✓ PASS]         │    │
│ │ ├─ Timestamps correct [✓ PASS]         │    │
│ │ └─ Aggregations ok    [✓ PASS]         │    │
│ └─────────────────────────────────────────┘    │
│                                                  │
│ 🎯 Failure Scenario Simulator                  │
│ Select scenario: [Connection Failure ▼]         │
│                                                  │
│ Input: "Show slow queries on PROD_DB"          │
│                                                  │
│ [Simulate Failure] → Result:                   │
│ ❌ Connection failed (simulated)                │
│ → Fallback triggered?                          │
│ → Proper error message? [✓ PASS]               │
│ → Logged for debugging? [✓ PASS]               │
│                                                  │
│ Risk Assessment: 🟢 SAFE                        │
│ (All failure scenarios handled correctly)       │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 🛡️ Risk Simulator Features by Domain

### **DBA Sandbox Features:**
```
1️⃣ Connection Selector
   - List available connections
   - Validate connection alive
   - Check permissions
   - Verify DB type

2️⃣ SQL Query Validator
   - Parse SQL syntax
   - Detect SQL injection patterns
   - Estimate query cost
   - Check table access permissions

3️⃣ Failure Injector
   - Connection timeout
   - Permission denied
   - Wrong DB type
   - Query execution failure
   - Metrics storage failure
   
4️⃣ Risk Assessment
   - Severity scoring
   - Failure impact analysis
   - Mitigation suggestions
```

### **HR Sandbox Features:**
```
1️⃣ Authorization Checker
   - Current user role
   - Required permission
   - Full RBAC trace

2️⃣ Policy Engine
   - Leave policy rules
   - Quota calculation
   - Date validation
   - Policy conflicts

3️⃣ Scenario Simulator
   - Non-manager approval attempt
   - Quota exceeded scenario
   - Concurrent requests
   - Invalid date ranges
   
4️⃣ Audit Trail
   - Who requested what
   - Who approved/rejected
   - Policy applied
   - Timestamps
```

### **Catalog Sandbox Features:**
```
1️⃣ Search Quality Tester
   - Query input
   - Vector search results
   - Keyword fallback results
   - Ranking scores

2️⃣ Recommendation Tester
   - Input query
   - Generated recommendations
   - Diversity metrics
   - Relevance scores

3️⃣ Vector DB Simulator
   - Vector DB unavailable
   - Slow search (timeout)
   - Empty results
   - Fallback triggered

4️⃣ Quality Metrics
   - Precision@5
   - nDCG scores
   - Recommendation diversity
```

---

## ✅ Success Criteria

### **DBA Sandbox Success:**
- ✓ No false negatives (real risks detected)
- ✓ No false positives (safe operations pass)
- ✓ All failure modes covered
- ✓ Connection safety verified
- ✓ SQL injection prevention validated
- ✓ Permission boundaries clear

### **HR Sandbox Success:**
- ✓ RBAC cannot be bypassed
- ✓ All policy rules tested
- ✓ Concurrent conflicts handled
- ✓ Audit trail complete
- ✓ Notifications working
- ✓ Leave balance accurate

### **Catalog Sandbox Success:**
- ✓ Search quality measurable
- ✓ Vector DB fallbacks work
- ✓ Ranking consistent
- ✓ Recommendations diverse
- ✓ No data leaks

---

## 🚫 Anti-Patterns to Avoid

❌ **One generic test runner** - Each domain needs custom logic
❌ **Shared test cases** - HR tests don't apply to DBA
❌ **Generic risk scoring** - DBA risks ≠ HR risks
❌ **Single "Test All" button** - Each domain tested independently
❌ **Workflow engine** - Not orchestrating; just simulating risks
❌ **Demo mode** - Risk simulators, not tutorials

---

## 🎯 Next Steps

1. **Identify DBA-specific risk matrix** (start here)
   - What are top 3 failure modes?
   - What's the severity?
   - How to detect?
   - How to fix?

2. **Build DBA Sandbox MVP**
   - Connection validation only
   - SQL safety check only
   - Basic error scenarios

3. **Expand to HR Sandbox**
   - RBAC tester
   - Policy validator

4. **Add Catalog Sandbox**
   - Search quality metrics
   - Recommendation tester
