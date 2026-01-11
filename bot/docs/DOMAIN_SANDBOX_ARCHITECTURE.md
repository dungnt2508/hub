# Domain-Specific Sandbox Architecture

## 🏢 High-Level Overview

```
Admin Dashboard
│
├── Test Sandbox (Routing - Existing)
│   └── Tests message → domain/intent routing only
│
└── Domain-Specific Sandboxes (NEW)
    │
    ├─── DBA Risk Simulator
    │    │
    │    ├─ Connection Safety Module
    │    │  ├─ Validate DB connection alive
    │    │  ├─ Check user has permissions
    │    │  ├─ Verify DB type matches intent
    │    │  └─ Simulate: Connection timeout
    │    │           : Permission denied
    │    │           : Wrong DB type
    │    │
    │    ├─ Query Safety Module
    │    │  ├─ Parse SQL syntax
    │    │  ├─ Detect SQL injection patterns
    │    │  ├─ Estimate query performance impact
    │    │  └─ Simulate: Injection blocked
    │    │           : Query timeout
    │    │           : Syntax error
    │    │
    │    ├─ Metrics Persistence Module
    │    │  ├─ Verify metrics stored correctly
    │    │  ├─ Check timestamp accuracy
    │    │  └─ Simulate: Storage failure
    │    │           : Data corruption
    │    │
    │    └─ Alert System Module
    │       ├─ Verify thresholds correct
    │       ├─ Check alert sent
    │       └─ Simulate: Alert not sent
    │                  : Wrong threshold used
    │
    ├─── HR Policy Simulator
    │    │
    │    ├─ Authorization Module (RBAC)
    │    │  ├─ Check user role
    │    │  ├─ Verify manager-only operations
    │    │  └─ Simulate: Non-manager approving leave
    │    │           : Unauthorized data access
    │    │
    │    ├─ Policy Engine Module
    │    │  ├─ Apply leave balance rules
    │    │  ├─ Check date overlap
    │    │  ├─ Verify quota limits
    │    │  └─ Simulate: Quota exceeded
    │    │           : Invalid date range
    │    │           : Overlapping requests
    │    │
    │    ├─ Concurrent Request Module
    │    │  ├─ Test race conditions
    │    │  └─ Simulate: Concurrent approval conflict
    │    │
    │    └─ Notification Module
    │       ├─ Verify notification sent
    │       └─ Simulate: Notification failure
    │
    └─── Catalog Quality Simulator
         │
         ├─ Search Quality Module
         │  ├─ Measure search relevance
         │  ├─ Test ranking quality
         │  └─ Simulate: Vector DB unavailable
         │           : No results found
         │
         ├─ Recommendation Module
         │  ├─ Check recommendation diversity
         │  ├─ Verify relevance scores
         │  └─ Simulate: Poor recommendation quality
         │
         └─ Fallback Module
            ├─ Test fallback to keyword search
            └─ Simulate: Fallback triggered correctly
```

---

## 📊 Request/Response Flow Comparison

### **Current: Generic Routing Test**
```
User Input: "Analyze slow queries"
        ↓
[Generic Router]
        ↓
→ Domain: dba
→ Intent: analyze_slow_query
→ Confidence: 0.92
        ↓
Response: Routing result only
(No domain-specific testing)
```

### **New: DBA Risk Simulator**
```
User Input: "Analyze slow queries on PROD_DB"
        ↓
[DBA Risk Simulator]
        ├─ Step 1: Route to DBA domain (PASS)
        │
        ├─ Step 2: Connection Safety Check
        │  ├─ Is connection string valid? ✓
        │  ├─ Is connection alive? ✓
        │  ├─ User has permissions? ✗ FAIL
        │  └─ Error: Permission denied on PROD_DB
        │
        ├─ Step 3: Query Safety Check
        │  ├─ SQL syntax valid? ✓
        │  ├─ No SQL injection? ✓
        │  ├─ Query cost acceptable? ✗ WARN
        │  └─ Performance impact: HIGH
        │
        ├─ Step 4: Failure Scenario
        │  └─ Simulate: Connection timeout
        │     → Does system fallback gracefully? ✓
        │     → Error message clear? ✓
        │     → Logged for debugging? ✓
        │
        └─ Risk Assessment: 🟡 MEDIUM RISK
           (Can execute, but permission boundaries not clear)
           
Response: Detailed risk assessment with all checks
```

---

## 🗂️ File Structure (NEW)

```
bot/frontend/src/
├── app/admin/
│   ├── test-sandbox/
│   │   ├── page.tsx                    (Existing - keep)
│   │   └── old-routing-only
│   │
│   └── domain-sandboxes/               (NEW)
│       ├── page.tsx                    (Domain selector UI)
│       │
│       ├── dba/
│       │   ├── page.tsx                (DBA Sandbox UI)
│       │   ├── components/
│       │   │   ├── ConnectionValidator.tsx
│       │   │   ├── QuerySafetyChecker.tsx
│       │   │   ├── FailureSimulator.tsx
│       │   │   └── RiskAssessment.tsx
│       │   ├── hooks/
│       │   │   ├── useConnectionTest.ts
│       │   │   ├── useQueryValidation.ts
│       │   │   └── useFailureScenarios.ts
│       │   └── utils/
│       │       ├── dba-risk-matrix.json
│       │       └── dba-scenarios.ts
│       │
│       ├── hr/
│       │   ├── page.tsx                (HR Sandbox UI)
│       │   ├── components/
│       │   │   ├── RBACTester.tsx
│       │   │   ├── PolicyValidator.tsx
│       │   │   └── ScenarioRunner.tsx
│       │   ├── hooks/
│       │   │   ├── useRBACTest.ts
│       │   │   ├── usePolicyEngine.ts
│       │   │   └── useConcurrentTest.ts
│       │   └── utils/
│       │       ├── hr-risk-matrix.json
│       │       └── hr-scenarios.ts
│       │
│       └── catalog/
│           ├── page.tsx                (Catalog Sandbox UI)
│           ├── components/
│           │   ├── SearchQualityTester.tsx
│           │   └── RecommendationTester.tsx
│           ├── hooks/
│           │   ├── useSearchQuality.ts
│           │   └── useRecommendation.ts
│           └── utils/
│               ├── catalog-risk-matrix.json
│               └── quality-metrics.ts
│
├── services/
│   ├── domain-sandbox.service.ts       (Service for all domain sandboxes)
│   ├── dba-sandbox.service.ts          (DBA-specific service)
│   ├── hr-sandbox.service.ts           (HR-specific service)
│   └── catalog-sandbox.service.ts      (Catalog-specific service)
│
└── shared/
    ├── types/
    │   ├── domain-sandbox.types.ts     (Shared types for all sandboxes)
    │   ├── risk-assessment.types.ts
    │   └── test-scenario.types.ts
    │
    └── components/
        ├── RiskMatrix.tsx              (Reusable risk matrix display)
        ├── FailureSimulator.tsx        (Reusable scenario runner)
        └── RiskBadge.tsx               (Status indicator)
```

---

## 💾 Backend Structure (NEW APIs)

```
bot/backend/
├── interface/
│   ├── admin_api.py                    (Existing)
│   │
│   └── domain_sandbox_api.py           (NEW)
│       ├── @router.post("/test-sandbox/dba/validate-connection")
│       ├── @router.post("/test-sandbox/dba/check-query-safety")
│       ├── @router.post("/test-sandbox/dba/simulate-failure")
│       │
│       ├── @router.post("/test-sandbox/hr/validate-rbac")
│       ├── @router.post("/test-sandbox/hr/validate-policy")
│       ├── @router.post("/test-sandbox/hr/simulate-scenario")
│       │
│       ├── @router.post("/test-sandbox/catalog/test-search")
│       └── @router.post("/test-sandbox/catalog/test-recommendation")
│
└── domain/
    ├── sandbox/                        (NEW - Sandbox simulators)
    │   ├── __init__.py
    │   │
    │   ├── dba_sandbox.py
    │   │   ├── ConnectionValidator
    │   │   ├── QuerySafetyChecker
    │   │   ├── FailureSimulator
    │   │   └── DBAAssessment
    │   │
    │   ├── hr_sandbox.py
    │   │   ├── RBACValidator
    │   │   ├── PolicyValidator
    │   │   └── ScenarioRunner
    │   │
    │   └── catalog_sandbox.py
    │       ├── SearchQualityAnalyzer
    │       └── RecommendationAnalyzer
    │
    ├── dba/
    │   ├── entry_handler.py            (Existing)
    │   ├── adapters/                   (Existing)
    │   └── services/                   (Existing)
    │
    └── hr/
        ├── entry_handler.py            (Existing)
        └── middleware/                 (Existing - RBAC)
```

---

## 🔄 Request Flow: DBA Sandbox Example

```
User: "I want to analyze slow queries, what could go wrong?"
                          ↓
┌─────────────────────────────────────────┐
│ Frontend: DBA Sandbox Page              │
├─────────────────────────────────────────┤
│                                          │
│ [Select Connection: PROD_DB]            │
│ [Input SQL or use default]              │
│ [Run Risk Simulation]                   │
│                                          │
└─────────────────────────────────────────┘
           ↓ POST /test-sandbox/dba/validate-connection
┌─────────────────────────────────────────┐
│ Backend: DBA Sandbox Service            │
├─────────────────────────────────────────┤
│                                          │
│ 1. ConnectionValidator.check()          │
│    → Validate connection string         │
│    → Check connection is alive          │
│    → Verify user permissions            │
│    → Identify DB type                   │
│    ↓                                     │
│    {                                    │
│      "is_alive": true,                  │
│      "has_permissions": false,          │
│      "db_type": "sql_server",           │
│      "error": "User lacks SELECT perm" │
│    }                                    │
│                                          │
│ 2. QuerySafetyChecker.check()           │
│    → Parse SQL                          │
│    → Check for SQL injection            │
│    → Estimate performance impact        │
│    ↓                                     │
│    {                                    │
│      "syntax_valid": true,              │
│      "injection_safe": true,            │
│      "estimated_rows": 5000,            │
│      "performance_impact": "HIGH"       │
│    }                                    │
│                                          │
│ 3. FailureSimulator.simulate()          │
│    → Simulate connection timeout        │
│    → Check graceful fallback            │
│    → Verify error handling              │
│    ↓                                     │
│    {                                    │
│      "scenario": "connection_timeout",  │
│      "fallback_triggered": true,        │
│      "error_message_clear": true,       │
│      "logged": true                     │
│    }                                    │
│                                          │
│ 4. Risk Assessment                      │
│    → Aggregate all checks               │
│    → Calculate risk score               │
│    → Provide recommendations            │
│    ↓                                     │
│    {                                    │
│      "risk_level": "MEDIUM",            │
│      "critical_issues": [               │
│        "User lacks permissions"         │
│      ],                                 │
│      "warnings": [                      │
│        "Query performance impact HIGH"  │
│      ],                                 │
│      "recommendations": [               │
│        "Request SELECT permission",     │
│        "Consider using LIMIT clause"    │
│      ]                                  │
│    }                                    │
│                                          │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ Frontend: Risk Assessment Display        │
├─────────────────────────────────────────┤
│                                          │
│ 🟡 MEDIUM RISK                          │
│                                          │
│ ❌ Critical Issues (1)                  │
│   • User lacks permissions on PROD_DB  │
│                                          │
│ ⚠️  Warnings (1)                        │
│   • Query performance impact HIGH       │
│                                          │
│ ✅ All failure scenarios handled        │
│   • Connection timeout → Fallback OK    │
│                                          │
│ 💡 Recommendations                      │
│   1. Request SELECT permission          │
│   2. Consider using LIMIT clause        │
│                                          │
└─────────────────────────────────────────┘
```

---

## 🎯 Domain Risk Matrix: DBA Example

```json
{
  "dba_sandbox": {
    "connection_safety": {
      "severity": "CRITICAL",
      "weight": 0.4,
      "checks": {
        "connection_alive": {
          "name": "Connection is Alive",
          "how_to_test": "Try connecting to database",
          "pass_criteria": "Connection succeeds",
          "fail_criteria": "Connection timeout or refused",
          "impact": "Cannot execute any analysis"
        },
        "user_permissions": {
          "name": "User Has Required Permissions",
          "how_to_test": "Check ACLs on database/tables",
          "pass_criteria": "User has SELECT on required tables",
          "fail_criteria": "Permission denied",
          "impact": "Query execution fails, confuses users"
        },
        "db_type_correct": {
          "name": "DB Type Matches Intent",
          "how_to_test": "Verify db_type from connection config",
          "pass_criteria": "DB type matches intent requirements",
          "fail_criteria": "DB type mismatch (e.g., expecting SQL Server, got PostgreSQL)",
          "impact": "Query logic may be wrong for DB"
        }
      }
    },
    "query_safety": {
      "severity": "HIGH",
      "weight": 0.3,
      "checks": {
        "sql_injection_safe": {
          "name": "No SQL Injection",
          "how_to_test": "Parse SQL and check for dangerous patterns",
          "pass_criteria": "No SQL injection patterns detected",
          "fail_criteria": "Dangerous SQL patterns found",
          "impact": "Database could be compromised"
        },
        "performance_acceptable": {
          "name": "Query Performance is Acceptable",
          "how_to_test": "Estimate rows returned and complexity",
          "pass_criteria": "Performance impact < threshold",
          "fail_criteria": "Query would take > X seconds",
          "impact": "Database performance degradation"
        }
      }
    },
    "metrics_persistence": {
      "severity": "MEDIUM",
      "weight": 0.2,
      "checks": {
        "metrics_stored": {
          "name": "Metrics Persisted",
          "how_to_test": "Execute and verify metrics in storage",
          "pass_criteria": "Metrics found in database",
          "fail_criteria": "Metrics not found or error on save",
          "impact": "Loss of performance history"
        },
        "data_integrity": {
          "name": "Data Integrity",
          "how_to_test": "Verify metrics math and aggregations",
          "pass_criteria": "All calculations correct",
          "fail_criteria": "Math errors or data corruption",
          "impact": "Wrong performance trending"
        }
      }
    },
    "alert_system": {
      "severity": "HIGH",
      "weight": 0.1,
      "checks": {
        "alert_triggered": {
          "name": "Alert Triggered When Needed",
          "how_to_test": "Simulate alert condition and check",
          "pass_criteria": "Alert sent with correct severity",
          "fail_criteria": "Alert not sent or wrong severity",
          "impact": "Critical issues not reported"
        }
      }
    }
  },
  "scoring": {
    "formula": "sum(check_result * weight for each check)",
    "risk_levels": {
      "0-0.2": { "name": "CRITICAL", "icon": "🔴", "action": "BLOCK" },
      "0.2-0.5": { "name": "HIGH", "icon": "🔴", "action": "REQUIRE_APPROVAL" },
      "0.5-0.8": { "name": "MEDIUM", "icon": "🟡", "action": "WARN" },
      "0.8-1.0": { "name": "LOW", "icon": "🟢", "action": "ALLOW" }
    }
  }
}
```

---

## 🔍 Comparison: Bad vs Good Sandbox Design

### ❌ Bad: Generic Sandbox
```tsx
// Tries to test everything for all domains
const GenericSandbox = () => {
  return (
    <div>
      <input placeholder="Enter message" />
      <select>
        <option>Test Input Validation</option>
        <option>Test Error Handling</option>
        <option>Test Authorization</option>
        <option>Test Database</option>
      </select>
      <button>Run Test</button>
      {result && <pre>{JSON.stringify(result)}</pre>}
    </div>
  );
};

// Problems:
// ❌ HR domain doesn't need "database test"
// ❌ DBA domain doesn't need "leave policy test"
// ❌ No domain-specific failure scenarios
// ❌ Doesn't expose actual risks
```

### ✅ Good: DBA-Specific Sandbox
```tsx
// Only tests DBA-domain risks
const DBASandbox = () => {
  return (
    <div>
      <h2>DBA Risk Simulator</h2>
      
      {/* Connection Safety Section */}
      <ConnectionValidator
        connections={availableConnections}
        onTest={validateConnection}
      />
      
      {/* Query Safety Section */}
      <QuerySafetyChecker
        sqlQuery={userQuery}
        onCheck={checkQuerySafety}
      />
      
      {/* Failure Scenario Injection */}
      <FailureSimulator
        scenarios={[
          "connection_timeout",
          "permission_denied",
          "query_too_slow",
          "metrics_storage_failed"
        ]}
        onSimulate={simulateFailure}
      />
      
      {/* Risk Assessment Result */}
      <RiskAssessment
        result={assessment}
        riskMatrix={dbaRiskMatrix}
      />
    </div>
  );
};

// Benefits:
// ✓ Every test is DBA-specific
// ✓ Exposes real failure modes
// ✓ Connects to domain entities
// ✓ Provides actionable recommendations
```

---

## 📋 Implementation Checklist

### Phase 1: DBA Sandbox Foundation
- [ ] Create DBA sandbox page structure
- [ ] Build Connection Validator component
- [ ] Implement Query Safety Checker
- [ ] Add Failure Scenario Simulator
- [ ] Create Risk Assessment display
- [ ] Design DBA risk matrix JSON
- [ ] Add backend endpoint: `/test-sandbox/dba/validate-connection`
- [ ] Add backend endpoint: `/test-sandbox/dba/check-query-safety`
- [ ] Add backend endpoint: `/test-sandbox/dba/simulate-failure`
- [ ] Document DBA-specific risks and scenarios

### Phase 2: HR Sandbox
- [ ] Create HR sandbox page structure
- [ ] Build RBAC Validator component
- [ ] Implement Policy Validator
- [ ] Add Scenario Simulator (concurrent requests, quota exceeded)
- [ ] Design HR risk matrix JSON
- [ ] Add backend endpoints for RBAC/policy tests

### Phase 3: Catalog Sandbox
- [ ] Create Catalog sandbox page structure
- [ ] Build Search Quality Tester
- [ ] Add Recommendation Analyzer
- [ ] Design quality metrics display

---

## 🚀 Domain Selector UI

```
┌─────────────────────────────────────────────┐
│ Domain-Specific Sandboxes                   │
├─────────────────────────────────────────────┤
│                                              │
│ Select a domain to simulate its risks:      │
│                                              │
│ ┌──────────────┐  ┌──────────────┐         │
│ │ 🗄️  DBA      │  │ 👥 HR        │         │
│ │ Risk Level:  │  │ Risk Level:  │         │
│ │ 🔴 HIGH      │  │ 🟡 MEDIUM    │         │
│ │              │  │              │         │
│ │ Focus:       │  │ Focus:       │         │
│ │ • Connection │  │ • RBAC       │         │
│ │ • SQL Safety │  │ • Policy     │         │
│ │ • Metrics    │  │ • Concurrent │         │
│ │              │  │              │         │
│ │ [Enter →]    │  │ [Enter →]    │         │
│ └──────────────┘  └──────────────┘         │
│                                              │
│ ┌──────────────┐  ┌──────────────┐         │
│ │ 📦 Catalog   │  │ (More...)    │         │
│ │ Risk Level:  │  │              │         │
│ │🟢 LOW        │  │ Add custom   │         │
│ │              │  │ domain here  │         │
│ │ Focus:       │  │              │         │
│ │ • Search     │  │              │         │
│ │ • Recommend  │  │ [Enter →]    │         │
│ │ • Fallback   │  │              │         │
│ │              │  │              │         │
│ │ [Enter →]    │  │              │         │
│ └──────────────┘  └──────────────┘         │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 📚 Related Documentation

- `SANDBOX_STRATEGY.md` - Philosophy and strategy
- `DOMAIN_SANDBOX_ARCHITECTURE.md` - This file - Architecture and flow
- **DBA_SANDBOX_GUIDE.md** (to be created) - DBA-specific risks and tests
- **HR_SANDBOX_GUIDE.md** (to be created) - HR-specific risks and tests
- **CATALOG_SANDBOX_GUIDE.md** (to be created) - Catalog-specific risks and tests
