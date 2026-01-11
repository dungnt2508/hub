# Sandbox Architecture - Visual Guide

## 🎯 System Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Admin Dashboard                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Navigation Menu:                                                 │
│  [Dashboard] [Routing] [Patterns] [Keywords] ... [Sandboxes]     │
│                                                           ▲        │
│                                              Click here ──┘        │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │ Sandboxes - Domain Selector Page        │
        ├─────────────────────────────────────────┤
        │                                          │
        │ Select a domain to test risks:          │
        │                                          │
        │  ┌──────────┐  ┌──────────┐            │
        │  │ 🗄️ DBA   │  │ 👥 HR    │            │
        │  │ Risk: 🔴 │  │ Risk: 🟡 │            │
        │  │ [ENTER]  │  │ [ENTER]  │            │
        │  └──────────┘  └──────────┘            │
        │                                          │
        │  ┌──────────┐  ┌──────────┐            │
        │  │ 📦 Cat   │  │ + Add     │            │
        │  │ Risk: 🟢 │  │ Custom   │            │
        │  │ [ENTER]  │  │          │            │
        │  └──────────┘  └──────────┘            │
        │                                          │
        └─────────────────────────────────────────┘
         ▲          ▲          ▲
         │          │          │
         │          │          └─ Catalog Sandbox
         │          └────────────── HR Sandbox
         │
         └─────────────────────── DBA Sandbox
                                  (DETAILED BELOW)
```

---

## 🔍 DBA Sandbox - Detailed UI Flow

### Page 1: Input Configuration

```
┌─────────────────────────────────────────────────────────┐
│ DBA Risk Simulator - Test your database operations      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ STEP 1: SELECT DATABASE CONNECTION                     │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 🔓 Available Connections:                       │   │
│ │                                                  │   │
│ │ ☐ PROD_MAIN                                     │   │
│ │   🔴 Production | SQL Server | Available      │   │
│ │   User: db_analyst | Permissions: SELECT      │   │
│ │                                                  │   │
│ │ ☐ PROD_ANALYTICS                                │   │
│ │   🔴 Production | MySQL | Available            │   │
│ │   User: db_analyst | Permissions: SELECT      │   │
│ │                                                  │   │
│ │ ✓ DEV_DB                                        │   │
│ │   🟢 Development | SQL Server | Available      │   │
│ │   User: db_analyst | Permissions: All         │   │
│ │   ← Selected                                    │   │
│ │                                                  │   │
│ │ ☐ TEST_LOCAL                                    │   │
│ │   🟢 Local | PostgreSQL | Available            │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ STEP 2: SELECT QUERY OR SCENARIO                       │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Pre-configured Scenarios:                       │   │
│ │ ✓ Analyze Slow Queries                          │   │
│ │ ☐ Detect Deadlocks                              │   │
│ │ ☐ Check Index Health                            │   │
│ │ ☐ Validate Custom SQL                           │   │
│ │                                                  │   │
│ │ OR paste your own SQL:                          │   │
│ │ ┌─────────────────────────────────────────────┐ │   │
│ │ │ SELECT                                        │ │   │
│ │ │   session_id,                                │ │   │
│ │ │   wait_duration_ms,                          │ │   │
│ │ │   wait_type                                  │ │   │
│ │ │ FROM sys.dm_exec_requests                    │ │   │
│ │ │ WHERE session_id > 50                        │ │   │
│ │ └─────────────────────────────────────────────┘ │   │
│ │ (Syntax hints: SQL Server, parameterized)      │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ STEP 3: FAILURE SIMULATION (Optional)                  │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Simulate what happens when things go wrong:    │   │
│ │                                                  │   │
│ │ ☐ Connection Timeout (30s no response)         │   │
│ │ ☐ Permission Denied (user lacks SELECT)        │   │
│ │ ☐ Query Too Slow (> 30s estimated time)        │   │
│ │ ☐ Wrong DB Type (syntax incompatible)          │   │
│ │ ☐ Metrics Storage Failed                       │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ [← BACK]              [RUN RISK ASSESSMENT →]         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Page 2: Risk Assessment Results

```
┌─────────────────────────────────────────────────────────┐
│ DBA Risk Assessment - RESULTS                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 📊 RISK SUMMARY                                        │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Risk Level: 🟡 MEDIUM (0.42)                   │   │
│ │ Connection: DEV_DB (SQL Server)                  │   │
│ │ Scenario: Analyze Slow Queries                  │   │
│ │ Assessment Time: 1.2s                           │   │
│ │ Timestamp: 2026-01-11 10:30:45 UTC             │   │
│ │                                                  │   │
│ │ ┌─────────────────────────────────────────┐   │   │
│ │ │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │   │
│ │ │ 0.0 ─────────────── 0.5 ───────────── 1.0 │   │   │
│ │ │ LOW    MEDIUM (HERE)   HIGH    CRITICAL │   │   │
│ │ └─────────────────────────────────────────┘   │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ 🔴 CRITICAL ISSUES (0)                                │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✓ All critical checks passed                    │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ 🟡 WARNINGS (2)                                       │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ⚠ Query Performance Impact: HIGH                │   │
│ │   └─ Estimated time: 15-30 seconds             │   │
│ │   └─ Estimated rows: 150,000                   │   │
│ │   └─ Recommendation: Add LIMIT clause or       │   │
│ │                      increase timeout          │   │
│ │                                                  │   │
│ │ ⚠ Missing WHERE Clause                          │   │
│ │   └─ Query scans entire table                  │   │
│ │   └─ Recommendation: Add WHERE to filter data  │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ 🟢 CHECKS PASSED (5)                                  │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✓ Connection is Alive                           │   │
│ │ ✓ User has SELECT Permissions                   │   │
│ │ ✓ No SQL Injection Detected                     │   │
│ │ ✓ Database Type is Correct (SQL Server)        │   │
│ │ ✓ Not on Production (Safe)                      │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ 💡 RECOMMENDATIONS                                    │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 1. Add WHERE clause to limit rows              │   │
│ │    Example: WHERE wait_duration_ms > 1000      │   │
│ │                                                  │   │
│ │ 2. Consider using specific columns             │   │
│ │    Replace: SELECT * → SELECT session_id, ... │   │
│ │                                                  │   │
│ │ 3. Test on DEV_DB first                         │   │
│ │    Current connection is safe (dev), good!     │   │
│ │                                                  │   │
│ │ 4. Monitor execution time                       │   │
│ │    Set timeout to 45 seconds for safety        │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ 📋 EXECUTION TRACE (Advanced)                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [+ Expand Full Trace]                           │   │
│ │                                                  │   │
│ │ Check Results:                                  │   │
│ │ 1. connection_alive ........... [✓] (50ms)    │   │
│ │ 2. user_permissions ........... [✓] (120ms)   │   │
│ │ 3. db_type_correct ............ [✓] (10ms)    │   │
│ │ 4. not_production ............. [✓] (5ms)     │   │
│ │ 5. sql_injection_safe ......... [✓] (200ms)   │   │
│ │ 6. performance_acceptable ..... [⚠] (300ms)   │   │
│ │ 7. no_sensitive_columns ....... [✓] (50ms)    │   │
│ │                                                  │   │
│ │ Total Assessment Time: 735ms                    │   │
│ │                                                  │   │
│ │ JSON Response:                                  │   │
│ │ {                                               │   │
│ │   "risk_level": "MEDIUM",                      │   │
│ │   "risk_score": 0.42,                          │   │
│ │   "checks_passed": 5,                          │   │
│ │   "checks_failed": 0,                          │   │
│ │   "checks_warned": 2,                          │   │
│ │   ...                                           │   │
│ │ }                                               │   │
│ │                                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ [← BACK TO TESTS]  [EXPORT REPORT]  [VIEW JSON]      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Risk Matrix Visualization

### DBA Risk Categories (Weighted)

```
┌─────────────────────────────────────────────────────────┐
│ RISK MATRIX - DBA Domain                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Category                Weight    Status   Impact       │
│ ────────────────────────────────────────────────────   │
│ Connection Safety       35%       ✓ PASS   CRITICAL   │
│ ├─ Alive               (17.5%)    ✓        CRITICAL   │
│ ├─ Permissions         (10%)      ✓        HIGH       │
│ ├─ DB Type             (5%)       ✓        MEDIUM     │
│ └─ Not Prod            (2.5%)     ✓        CRITICAL   │
│                                                          │
│ Query Safety            30%       ⚠ WARN   HIGH       │
│ ├─ SQL Injection        (12%)     ✓        CRITICAL   │
│ ├─ Performance          (12%)     ⚠        HIGH       │
│ ├─ Syntax Valid         (3%)      ✓        MEDIUM     │
│ └─ Sensitive Columns    (3%)      ✓        CRITICAL   │
│                                                          │
│ Metrics & Alerts        20%       ✓ PASS   MEDIUM     │
│ ├─ Persist              (10%)     ✓        MEDIUM     │
│ └─ Alert Threshold      (10%)     ✓        HIGH       │
│                                                          │
│ Data Protection         15%       ✓ PASS   HIGH       │
│ └─ Sensitive Cols       (15%)     ✓        CRITICAL   │
│                                                          │
│ ────────────────────────────────────────────────────   │
│ WEIGHTED SCORE:         100%                 0.42      │
│ ────────────────────────────────────────────────────   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram (DBA Sandbox)

```
┌────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION (Frontend)                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  User selects:                                         │
│  • Connection: DEV_DB                                  │
│  • Scenario: Analyze Slow Queries                      │
│  • Failure simulation: None                            │
│                                                         │
│  [Click: RUN RISK ASSESSMENT]                          │
│                                                         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 2. BUILD REQUEST (Frontend)                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│  const request = {                                     │
│    connection_id: "uuid-001",                          │
│    scenario: "analyze_slow_query",                     │
│    sql_query: "[auto-generated or user input]",        │
│    simulate_failure: null,                             │
│    risk_matrix_version: "1.0"                          │
│  }                                                      │
│                                                         │
│  [Validate locally before sending]                     │
│                                                         │
└────────────────────────────────────────────────────────┘
                          ↓
      POST /test-sandbox/dba/validate-connection
      POST /test-sandbox/dba/check-query-safety
                          ↓
┌────────────────────────────────────────────────────────┐
│ 3. BACKEND VALIDATION (Backend)                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Step 3A: ConnectionValidator                         │
│  ├─ Lookup connection in registry                     │
│  ├─ Get { host, port, credentials, db_type }         │
│  ├─ Try to establish connection                       │
│  ├─ Run: SELECT 1  → Success?                         │
│  ├─ Check system_views for permissions                │
│  └─ Result: { is_alive: ✓, permissions: [...] }      │
│                                                         │
│  Step 3B: QuerySafetyChecker                          │
│  ├─ Parse SQL syntax                                  │
│  ├─ Check for injection patterns                      │
│  │  ├─ Look for: UNION, EXEC, DROP, DELETE...        │
│  │  └─ Result: sql_injection_safe: ✓                 │
│  ├─ Estimate query cost                               │
│  │  ├─ Parse table access                            │
│  │  ├─ Count JOINs                                    │
│  │  ├─ Estimate rows (from stats)                    │
│  │  └─ Result: performance_acceptable: ⚠ (15s est)  │
│  ├─ Scan for sensitive columns                        │
│  │  ├─ Look for: password, ssn, credit_card...      │
│  │  └─ Result: no_sensitive_columns: ✓              │
│  └─ Result: { syntax: ✓, injection: ✓, perf: ⚠ }    │
│                                                         │
│  Step 3C: RiskAssessment                              │
│  ├─ Load DBA risk matrix                              │
│  ├─ Apply check results to matrix                     │
│  ├─ Calculate weighted score                          │
│  │  └─ score = 1.0 - Σ(weight × result)              │
│  ├─ Map to risk level                                 │
│  │  └─ 0.42 → MEDIUM (0.2-0.5 range)                │
│  └─ Generate recommendations                          │
│     ├─ For each warning: suggest fix                 │
│     └─ List all passed checks                         │
│                                                         │
└────────────────────────────────────────────────────────┘
                          ↓
        return RiskAssessmentResponse
                          ↓
┌────────────────────────────────────────────────────────┐
│ 4. DISPLAY RESULTS (Frontend)                          │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Received response:                                    │
│  {                                                     │
│    "risk_level": "MEDIUM",                           │
│    "risk_score": 0.42,                               │
│    "issues": [...],                                   │
│    "recommendations": [...],                          │
│    "checks_passed": 5,                               │
│    "checks_failed": 0,                               │
│    "checks_warned": 2,                               │
│    "trace": {...}                                     │
│  }                                                     │
│                                                         │
│  Render:                                              │
│  1. Risk level badge (🟡 MEDIUM)                      │
│  2. Risk progress bar (0.42 on 0-1.0 scale)          │
│  3. Issues list (critical/warning/pass)              │
│  4. Recommendations (5 items)                         │
│  5. Full trace (collapsible)                          │
│                                                         │
│  [✓] Display to user                                  │
│  [→] User can now make decision                       │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 Risk Level Interpretation

### Visual Risk Score Scale

```
┌─ CRITICAL (🔴) ─────────────────────────────────────┐
│ Score: 0.80 - 1.00                                  │
│ Action: BLOCK EXECUTION                             │
│ Example: SQL injection detected                     │
│          User lacks permissions                     │
│          Wrong database selected                    │
│ ███████████████████████████████████████████████    │
└─────────────────────────────────────────────────────┘

┌─ HIGH (🔴) ────────────────────────────────────────┐
│ Score: 0.50 - 0.80                                  │
│ Action: REQUIRE APPROVAL                            │
│ Example: Query too slow (30-60s)                    │
│          Alert thresholds wrong                     │
│ ███████████████████████░░░░░░░░░░░░░░░░░░░░░░░    │
└─────────────────────────────────────────────────────┘

┌─ MEDIUM (🟡) ──────────────────────────────────────┐
│ Score: 0.20 - 0.50                                  │
│ Action: WARN USER                                  │
│ Example: Query might be slow                        │
│          Missing WHERE clause                       │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
└─────────────────────────────────────────────────────┘

┌─ LOW (🟢) ─────────────────────────────────────────┐
│ Score: 0.00 - 0.20                                  │
│ Action: ALLOW                                       │
│ Example: All checks passed                          │
│          Safe to execute                            │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Component Hierarchy (Detailed)

```
DBASandbox (Page)
│
├─ ConnectionValidator
│  ├─ ConnectionList
│  │  ├─ ConnectionCard (✓ DEV_DB)
│  │  ├─ ConnectionCard (☐ PROD_MAIN)
│  │  └─ ConnectionCard (☐ TEST)
│  │
│  ├─ SelectedConnectionDetails
│  │  ├─ Name: DEV_DB
│  │  ├─ Type: SQL Server
│  │  ├─ Status: 🟢 Available
│  │  ├─ UserPermissions table
│  │  └─ IsProduction: No (safe)
│  │
│  └─ ConnectionValidator.test()
│     └─ → { is_alive, permissions, db_type }
│
├─ QuerySafetyChecker
│  ├─ ScenarioSelector
│  │  ├─ Option: Analyze Slow Queries (✓)
│  │  ├─ Option: Detect Deadlocks
│  │  └─ Option: Validate Custom SQL
│  │
│  ├─ QueryInput (if custom)
│  │  └─ SQLEditor with syntax highlighting
│  │
│  └─ QuerySafetyChecker.test()
│     → { injection_safe, perf_ok, sensitive_cols, syntax_valid }
│
├─ FailureSimulator
│  ├─ Checkbox: Connection Timeout
│  ├─ Checkbox: Permission Denied
│  ├─ Checkbox: Query Too Slow
│  ├─ Checkbox: Wrong DB Type
│  └─ Checkbox: Metrics Storage Failed
│
├─ [RUN ASSESSMENT BUTTON]
│
└─ RiskAssessmentReport (rendered after results)
   ├─ RiskSummary
   │  ├─ RiskLevelBadge: 🟡 MEDIUM
   │  ├─ RiskProgressBar: ████░░░░░ (0.42)
   │  └─ Metadata: timestamp, duration
   │
   ├─ CriticalIssuesList (0)
   │  └─ "✓ All critical checks passed"
   │
   ├─ WarningsList (2)
   │  ├─ Warning: Query Performance HIGH
   │  │  └─ Details + Recommendation
   │  └─ Warning: Missing WHERE clause
   │     └─ Details + Recommendation
   │
   ├─ PassedChecksList (5)
   │  ├─ ✓ Connection Alive
   │  ├─ ✓ User Permissions OK
   │  ├─ ✓ SQL Injection Safe
   │  ├─ ✓ DB Type Correct
   │  └─ ✓ Not on Production
   │
   ├─ RecommendationsList (4)
   │  ├─ "Add WHERE clause..."
   │  ├─ "Use specific columns..."
   │  ├─ "Test on DEV first..."
   │  └─ "Monitor execution time..."
   │
   └─ FullTraceExpander
      └─ JSON or detailed step-by-step log
```

---

## 📈 Risk Score Calculation Example

```
Input:
  connection_alive:     ✓ pass    weight: 0.175
  user_permissions:     ✓ pass    weight: 0.10
  db_type_correct:      ✓ pass    weight: 0.05
  not_production:       ✓ pass    weight: 0.025
  sql_injection:        ✓ pass    weight: 0.12
  query_performance:    ⚠ warn    weight: 0.12    (result: 0.5)
  syntax_valid:         ✓ pass    weight: 0.03
  no_sensitive_cols:    ✓ pass    weight: 0.03

Calculation:
  passed_sum = 0.175 + 0.10 + 0.05 + 0.025 + 0.12 + 0.03 + 0.03
             = 0.53 × 1.0 (all pass = 1.0)
  warned_sum = 0.12 × 0.5 = 0.06
  total_check_value = 0.53 + 0.06 = 0.59
  
  risk_score = 1.0 - 0.59 = 0.41

Result:
  risk_score: 0.41
  risk_level: "MEDIUM" (0.41 is in 0.20-0.50 range)
  action: "WARN USER"
  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  0.0                                      1.0
      ↑ (0.41)
      └─ Score is here = MEDIUM RISK
```

---

## 🎓 HR Sandbox - Similar Structure

```
HR Risk Simulator
├─ User Selector
│  └─ Select employee or use current context
│
├─ Action Selector
│  ├─ Create Leave Request
│  ├─ Approve Leave
│  └─ Query Leave Balance
│
├─ Parameters Input
│  ├─ Leave days
│  ├─ Date range
│  └─ Reason/comment
│
├─ RBAC Check
│  └─ Does user have permission for this action?
│
├─ Policy Check
│  └─ Does request comply with leave policy?
│
└─ Risk Assessment
   ├─ Authorization: ✓ Pass
   ├─ Policy Compliance: ✓ Pass
   ├─ Quota Available: ⚠ Low (only 2 days left)
   ├─ No Conflicts: ✓ Pass
   └─ Risk Level: 🟡 MEDIUM
```

---

## 📊 Catalog Sandbox - Similar Structure

```
Catalog Quality Simulator
├─ Query Input
│  └─ Enter search query
│
├─ Search Quality Test
│  └─ Show search results + quality metrics
│
├─ Recommendation Test
│  └─ Show recommendations + diversity score
│
└─ Risk Assessment
   ├─ Relevance: ✓ Good (0.85)
   ├─ Diversity: ✓ Good (5+ different categories)
   ├─ Vector DB: ✓ Available
   ├─ Fallback: ✓ Works
   └─ Risk Level: 🟢 LOW
```

---

## 🔗 Navigation Between Sandboxes

```
┌──────────────────────────────────────────┐
│ Domain Selector Page                     │
├──────────────────────────────────────────┤
│ [DBA] [HR] [Catalog]                     │
└──────────────────────────────────────────┘
     ↓       ↓        ↓
   DBA    HR      Catalog
   Page   Page    Page
    ↓      ↓       ↓
[Assessment] [Assessment] [Assessment]
    ↑      ↑       ↑
[← BACK TO SELECTOR] (on each sandbox page)
```

---

## 🎨 Color Coding

```
🔴 RED / CRITICAL
   - Severity: CRITICAL / HIGH
   - Risk score: 0.5 - 1.0
   - Action: BLOCK or REQUIRE APPROVAL

🟡 YELLOW / MEDIUM
   - Severity: MEDIUM
   - Risk score: 0.2 - 0.5
   - Action: WARN USER

🟢 GREEN / LOW
   - Severity: LOW
   - Risk score: 0.0 - 0.2
   - Action: ALLOW

⚪ GRAY / NEUTRAL
   - Status: Pending, Unknown
   - Not assessed yet
```

This visual guide makes it clear how the sandbox translates domain-specific risks into a clear, actionable UI.
