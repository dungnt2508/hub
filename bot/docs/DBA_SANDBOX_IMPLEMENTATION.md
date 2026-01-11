# DBA Domain Sandbox - Implementation Guide

## 🎯 Objective
Build a **risk simulator specific to DBA domain**. Not a generic test tool, but a **safety checker** that exposes real failure modes before execution.

---

## 📊 DBA Risk Profile

```
DBA Domain Characteristics:
├─ Operation Type: DESTRUCTIVE POTENTIAL (read/write to production DB)
├─ External Dependencies: ✓ Real database connection required
├─ Business Impact: ✓ CRITICAL (data corruption, downtime)
├─ Authorization: ✓ Role-based (DBA only)
├─ Reversibility: ✗ Hard to undo (depends on query)
└─ Frequency: Low (specialized domain)
```

### 🔴 Top Risks (by severity)

| Risk | Impact | How to Detect | Severity |
|------|--------|--------------|----------|
| **Wrong database selected** | Query runs on prod instead of dev | Verify connection name & type | CRITICAL |
| **SQL injection in custom queries** | Database compromised | Scan for dangerous SQL patterns | CRITICAL |
| **User lacks permissions** | Query fails, confuses user | Check ACLs before execution | HIGH |
| **Query too slow (DoS)** | Database performance degradation | Estimate query cost | HIGH |
| **Metrics stored incorrectly** | Wrong trending data | Verify schema and calculation | MEDIUM |
| **Alert not triggered** | Critical issue goes unnoticed | Test alert conditions | HIGH |
| **Wrong DB type assumptions** | Query logic fails on different DB | Verify query compatibility | MEDIUM |

---

## 🏗️ DBA Sandbox Architecture

### Components

```
DBA Sandbox (dba-sandbox.tsx)
│
├── 1️⃣ Connection Validator
│   ├─ Select from available connections
│   ├─ Verify connection is alive
│   ├─ Check user permissions
│   ├─ Identify DB type (SQL Server, PostgreSQL, MySQL)
│   └─ Display connection details
│
├── 2️⃣ Query Safety Checker
│   ├─ Input: SQL query or pre-defined scenario
│   ├─ Parse SQL syntax
│   ├─ Detect SQL injection patterns
│   ├─ Estimate performance impact (rows, complexity)
│   └─ Display safety assessment
│
├── 3️⃣ Failure Scenario Injector
│   ├─ Simulate: Connection timeout
│   ├─ Simulate: Permission denied
│   ├─ Simulate: Wrong DB type
│   ├─ Simulate: Query execution failure
│   ├─ Simulate: Metrics storage failure
│   └─ Verify graceful error handling
│
└── 4️⃣ Risk Assessment Report
    ├─ Aggregate all checks
    ├─ Calculate risk score (0-1.0)
    ├─ Map to risk level: CRITICAL/HIGH/MEDIUM/LOW
    ├─ List all issues found
    ├─ Provide recommendations
    └─ Show full trace
```

---

## 📋 DBA Risk Matrix (Implementation Reference)

```json
{
  "dba_sandbox": {
    "version": "1.0",
    "domain": "dba",
    
    "risk_categories": {
      "connection_safety": {
        "severity": "CRITICAL",
        "weight": 0.35,
        "description": "Ensures safe database selection and permissions",
        
        "checks": {
          "connection_alive": {
            "id": "conn_alive",
            "name": "Connection is Alive",
            "description": "Database is reachable and responding",
            "method": "Try to establish connection",
            "success_criteria": "Connection succeeds within timeout",
            "failure_impact": "Cannot execute any query",
            "risk_if_missing": "CRITICAL"
          },
          
          "user_permissions": {
            "id": "user_perms",
            "name": "User Has Permissions",
            "description": "User has SELECT permission on required tables",
            "method": "Check system catalog (sys.tables, information_schema)",
            "success_criteria": "All required tables have SELECT grant",
            "failure_impact": "Query execution fails, confuses user",
            "risk_if_missing": "HIGH",
            "requires_connection": true
          },
          
          "db_type_correct": {
            "id": "db_type",
            "name": "Database Type Matches",
            "description": "Selected DB type matches intent requirements",
            "method": "Compare connection.db_type vs intent.required_db_types",
            "success_criteria": "DB type is in allowed list",
            "failure_impact": "Query syntax/logic may be wrong",
            "risk_if_missing": "MEDIUM"
          },
          
          "not_production": {
            "id": "not_prod",
            "name": "Connection is Safe",
            "description": "Prevent accidental execution on production without warning",
            "method": "Check connection.is_production flag",
            "success_criteria": "Is prod flag = false OR user confirmed prod intent",
            "failure_impact": "Accidental production modification",
            "risk_if_missing": "CRITICAL"
          }
        }
      },
      
      "query_safety": {
        "severity": "HIGH",
        "weight": 0.30,
        "description": "Prevents SQL injection and resource exhaustion",
        
        "checks": {
          "sql_injection_safe": {
            "id": "sql_injection",
            "name": "No SQL Injection Detected",
            "description": "Query is free from SQL injection patterns",
            "method": "Parse SQL and check for dangerous patterns (union, exec, drop, etc.)",
            "success_criteria": "No dangerous patterns found",
            "failure_impact": "Database could be compromised",
            "risk_if_missing": "CRITICAL",
            "patterns_to_block": [
              "UNION SELECT",
              "EXEC\\s*\\(",
              "EXECUTE\\s*\\(",
              "DROP\\s+(TABLE|DATABASE)",
              "DELETE.*WHERE.*=.*'",
              "INSERT.*INTO.*VALUES",
              "UPDATE.*SET.*WHERE.*=.*'"
            ]
          },
          
          "performance_acceptable": {
            "id": "query_perf",
            "name": "Query Performance Acceptable",
            "description": "Query won't cause database performance issues",
            "method": "Estimate cost (rows returned, complexity, estimated duration)",
            "success_criteria": "Estimated execution time < 30s AND rows < 1M",
            "failure_impact": "Database DoS, performance degradation",
            "risk_if_missing": "HIGH",
            "thresholds": {
              "max_estimated_rows": 1000000,
              "max_execution_time_ms": 30000,
              "max_joins": 5,
              "max_table_size_gb": 100
            }
          },
          
          "syntax_valid": {
            "id": "sql_syntax",
            "name": "SQL Syntax Valid",
            "description": "Query has valid SQL syntax for target DB",
            "method": "Try to parse/validate SQL",
            "success_criteria": "Parse succeeds without errors",
            "failure_impact": "Query execution fails, confuses user",
            "risk_if_missing": "MEDIUM"
          }
        }
      },
      
      "metrics_and_alerts": {
        "severity": "MEDIUM",
        "weight": 0.20,
        "description": "Ensures performance data is captured and alerted correctly",
        
        "checks": {
          "metrics_persisted": {
            "id": "metrics_persist",
            "name": "Metrics Will Be Persisted",
            "description": "Query metrics are saved to history for trending",
            "method": "Verify metrics table exists and is writable",
            "success_criteria": "Can insert to metrics table",
            "failure_impact": "Loss of performance history",
            "risk_if_missing": "MEDIUM"
          },
          
          "alert_threshold_correct": {
            "id": "alert_threshold",
            "name": "Alert Thresholds Are Correct",
            "description": "Alert will trigger at appropriate threshold",
            "method": "Check alert configuration for this intent",
            "success_criteria": "Thresholds are within reasonable range",
            "failure_impact": "Critical issues not alerted",
            "risk_if_missing": "HIGH"
          }
        }
      },
      
      "data_protection": {
        "severity": "HIGH",
        "weight": 0.15,
        "description": "Prevents unauthorized data access",
        
        "checks": {
          "no_sensitive_columns": {
            "id": "sensitive_cols",
            "name": "No Sensitive Columns Exposed",
            "description": "Query doesn't expose PII or sensitive data",
            "method": "Scan query for SELECT * or known sensitive columns",
            "success_criteria": "No sensitive columns in SELECT",
            "failure_impact": "Data breach, privacy violation",
            "risk_if_missing": "CRITICAL",
            "sensitive_columns": [
              "password",
              "ssn",
              "credit_card",
              "salary",
              "social_security",
              "email",
              "phone"
            ]
          }
        }
      }
    },
    
    "failure_scenarios": {
      "connection_timeout": {
        "id": "fail_conn_timeout",
        "name": "Connection Timeout",
        "description": "Database doesn't respond within timeout period",
        "how_to_trigger": "Simulate network latency > 30s",
        "expected_behavior": "Graceful error, fallback suggestion",
        "acceptable_outcomes": [
          "Error message is clear and actionable",
          "Suggestion to check connection",
          "Logged for debugging"
        ]
      },
      
      "permission_denied": {
        "id": "fail_permission",
        "name": "Permission Denied",
        "description": "User lacks required permissions on database",
        "how_to_trigger": "User doesn't have SELECT on table",
        "expected_behavior": "Error message shows missing permission",
        "acceptable_outcomes": [
          "Error message specifies missing permission",
          "Suggestions for granting permission",
          "Logged with user context"
        ]
      },
      
      "wrong_db_type": {
        "id": "fail_db_type",
        "name": "Wrong Database Type",
        "description": "Connection type doesn't match query requirements",
        "how_to_trigger": "SQL Server syntax on PostgreSQL",
        "expected_behavior": "Validation error before execution",
        "acceptable_outcomes": [
          "Error specifies DB type mismatch",
          "Shows compatible DB types",
          "Suggests alternative syntax"
        ]
      },
      
      "query_too_slow": {
        "id": "fail_slow_query",
        "name": "Query Performance Too High",
        "description": "Query would take too long to execute",
        "how_to_trigger": "Query scans entire table without WHERE clause",
        "expected_behavior": "Warning with cost estimate",
        "acceptable_outcomes": [
          "Shows estimated cost",
          "Suggests optimization",
          "Allows override with confirmation"
        ]
      },
      
      "metrics_storage_failed": {
        "id": "fail_metrics",
        "name": "Metrics Storage Failed",
        "description": "Unable to persist metrics after execution",
        "how_to_trigger": "Metrics table is full or unreachable",
        "expected_behavior": "Query executes but warning issued",
        "acceptable_outcomes": [
          "Query still completes",
          "Warning about metrics storage",
          "Fallback to memory storage"
        ]
      }
    },
    
    "scoring": {
      "formula": "1.0 - sum(check_weight * check_pass_fraction)",
      "risk_thresholds": {
        "critical": { "min": 0.8, "max": 1.0, "icon": "🔴", "action": "BLOCK" },
        "high": { "min": 0.5, "max": 0.8, "icon": "🔴", "action": "REQUIRE_APPROVAL" },
        "medium": { "min": 0.2, "max": 0.5, "icon": "🟡", "action": "WARN_USER" },
        "low": { "min": 0.0, "max": 0.2, "icon": "🟢", "action": "ALLOW" }
      }
    }
  }
}
```

---

## 🛠️ Implementation Steps

### Step 1: Create DBA Sandbox Page Structure

Create `bot/frontend/src/app/admin/domain-sandboxes/dba/page.tsx`:

```typescript
// High-level structure
export default function DBASandboxPage() {
  // State
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Main flow:
  // 1. User selects connection
  // 2. User enters query or scenario
  // 3. Frontend validates connection
  // 4. Frontend validates query safety
  // 5. Frontend optionally simulates failure
  // 6. Display risk assessment
  
  return (
    <AdminLayout>
      {/* Title & Description */}
      {/* Connection Selector Component */}
      {/* Query Input Component */}
      {/* Scenario Selector Component */}
      {/* Risk Matrix Display */}
      {/* Failure Simulation Controls */}
      {/* Risk Assessment Results */}
    </AdminLayout>
  );
}
```

### Step 2: Create DBA-Specific Service

Create `bot/frontend/src/services/dba-sandbox.service.ts`:

```typescript
class DBASandboxService {
  // API calls specific to DBA domain
  
  async validateConnection(connectionId: string): Promise<ConnectionValidationResult> {
    // POST /api/admin/v1/test-sandbox/dba/validate-connection
  }
  
  async checkQuerySafety(connectionId: string, sqlQuery: string): Promise<QuerySafetyResult> {
    // POST /api/admin/v1/test-sandbox/dba/check-query-safety
  }
  
  async simulateFailure(
    connectionId: string,
    sqlQuery: string,
    scenario: FailureScenario
  ): Promise<FailureSimulationResult> {
    // POST /api/admin/v1/test-sandbox/dba/simulate-failure
  }
  
  async assessRisk(result: RiskAssessment): Promise<RecommendationList> {
    // POST /api/admin/v1/test-sandbox/dba/assess-risk
  }
}
```

### Step 3: Create Components

**ConnectionValidator.tsx**
```typescript
// Show connection status:
// - Connection name
// - Database type
// - Host/port
// - Connection status (alive/dead)
// - User permissions (table by table)
// - Is production? (warning)
```

**QuerySafetyChecker.tsx**
```typescript
// Show query analysis:
// - SQL syntax valid?
// - SQL injection detected?
// - Estimated rows/complexity
// - Performance impact
// - Sensitive columns check
```

**FailureSimulator.tsx**
```typescript
// Allow selecting failure scenario:
// - Connection timeout
// - Permission denied
// - Wrong DB type
// - Query too slow
// - Metrics storage failed
// - Run simulation → see expected behavior
```

**RiskAssessmentReport.tsx**
```typescript
// Display final assessment:
// - Risk level (CRITICAL/HIGH/MEDIUM/LOW)
// - Critical issues list
// - Warnings list
// - All passed checks (show successes)
// - Recommendations
// - Full execution trace
```

### Step 4: Create Backend Endpoints

Add to `bot/backend/interface/domain_sandbox_api.py`:

```python
@router.post("/test-sandbox/dba/validate-connection")
async def dba_validate_connection(
    connection_id: str,
    current_user: dict = Depends(require_admin_or_operator)
) -> ConnectionValidationResult:
    """Validate DBA connection safety"""
    # 1. Get connection from registry
    # 2. Check connection is alive
    # 3. Verify user permissions
    # 4. Return detailed result

@router.post("/test-sandbox/dba/check-query-safety")
async def dba_check_query_safety(
    connection_id: str,
    sql_query: str,
    current_user: dict = Depends(require_admin_or_operator)
) -> QuerySafetyResult:
    """Check if SQL query is safe"""
    # 1. Validate connection exists
    # 2. Parse SQL syntax
    # 3. Check for SQL injection
    # 4. Estimate performance
    # 5. Return safety assessment

@router.post("/test-sandbox/dba/simulate-failure")
async def dba_simulate_failure(
    connection_id: str,
    sql_query: str,
    scenario: str,
    current_user: dict = Depends(require_admin_or_operator)
) -> FailureSimulationResult:
    """Simulate failure scenario"""
    # 1. Validate inputs
    # 2. Simulate specified failure
    # 3. Check system handles gracefully
    # 4. Return simulation result
```

### Step 5: Create Risk Matrix JSON

Create `bot/frontend/src/app/admin/domain-sandboxes/dba/utils/dba-risk-matrix.json`:
- Copy the risk matrix from above
- Use it to render checkboxes/progress bars in UI

### Step 6: Create Test Scenarios

Create `bot/frontend/src/app/admin/domain-sandboxes/dba/utils/dba-scenarios.ts`:

```typescript
export const DBA_SCENARIOS = {
  // Pre-configured test scenarios
  
  slow_query_analysis: {
    title: "Analyze Slow Queries",
    description: "Find slow running queries on database",
    expectedRisks: ["wrong_db_selected", "permission_denied", "slow_query"],
    intent: "analyze_slow_query"
  },
  
  check_deadlocks: {
    title: "Detect Deadlocks",
    description: "Check for blocking and deadlock patterns",
    expectedRisks: ["connection_failure", "permission_denied"],
    intent: "detect_deadlock_pattern"
  },
  
  validate_custom_sql: {
    title: "Validate Custom SQL",
    description: "Check custom SQL before execution",
    expectedRisks: ["sql_injection", "slow_query", "permission_denied"],
    intent: "validate_custom_sql"
  }
};
```

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ DBA Risk Simulator                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 📊 Step 1: Select Connection                           │
│ ┌──────────────────────────────────────────────────┐   │
│ │ [Production Servers ▼]                           │   │
│ │ • PROD_MAIN_DB      🔴 Critical                  │   │
│ │ • PROD_ANALYTICS    🔴 Critical                  │   │
│ │ • DEV_DB            🟢 Safe                      │   │
│ │ • LOCAL_TEST        🟢 Safe                      │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ 📝 Step 2: Input Query or Select Scenario              │
│ ┌──────────────────────────────────────────────────┐   │
│ │ [Pre-configured Scenarios ▼]                     │   │
│ │ ┌─ Analyze Slow Queries                          │   │
│ │ ┌─ Detect Deadlocks                              │   │
│ │ ┌─ Validate Custom SQL                           │   │
│ │                                                   │   │
│ │ OR paste custom SQL:                             │   │
│ │ [                                             ]   │   │
│ │ SELECT * FROM table_name WHERE condition        │   │
│ │                                                  │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ 🚨 Step 3: Failure Scenario (Optional)                 │
│ ┌──────────────────────────────────────────────────┐   │
│ │ □ Simulate Connection Timeout                    │   │
│ │ □ Simulate Permission Denied                     │   │
│ │ □ Simulate Query Too Slow                        │   │
│ │ □ Simulate Metrics Storage Failed                │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ [Run Risk Assessment]                                  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ ✅ RISK ASSESSMENT RESULT                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Risk Level: 🟡 MEDIUM (0.45)                           │
│                                                          │
│ 🔴 Critical Issues (0):                                │
│    None                                                │
│                                                          │
│ 🟡 Warnings (2):                                       │
│    • Query performance impact: HIGH                     │
│    • Table scan detected, consider WHERE clause         │
│                                                          │
│ 🟢 Passed Checks (5):                                  │
│    ✓ Connection is alive                              │
│    ✓ User has SELECT permissions                      │
│    ✓ SQL injection safe                               │
│    ✓ Database type correct                            │
│    ✓ Not on production (safe)                         │
│                                                          │
│ 💡 Recommendations:                                    │
│    1. Add WHERE clause to limit rows                   │
│    2. Consider using column list instead of SELECT *   │
│    3. Test on smaller dataset first                    │
│                                                          │
│ [View Full Trace ▼]                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Data Flow Diagram

```
User Input:
  - Select Connection: PROD_DB
  - Query: "SELECT * FROM table_name"
  - Scenario: None (or "connection_timeout")
        ↓
┌──────────────────────────────────────────┐
│ DBA Sandbox Validator (Frontend)         │
├──────────────────────────────────────────┤
│                                           │
│ 1. Load risk matrix from JSON             │
│ 2. Build request object                   │
│ 3. Call backend API                       │
│                                           │
└──────────────────────────────────────────┘
        ↓
    HTTP POST to Backend
        ↓
┌──────────────────────────────────────────┐
│ DBA Sandbox API (Backend)                │
├──────────────────────────────────────────┤
│                                           │
│ DBAConnectionValidator:                  │
│  - Check connection registry              │
│  - Verify connection alive                │
│  - Get user permissions                   │
│  - Identify DB type                       │
│  → CheckResult: pass/fail per check       │
│                                           │
│ DBAQuerySafetyChecker:                   │
│  - Parse SQL                              │
│  - Scan for injection patterns            │
│  - Estimate query cost                    │
│  - Check sensitive columns                │
│  → CheckResult: pass/fail per check       │
│                                           │
│ DBAFailureSimulator (if scenario):        │
│  - Simulate specified failure             │
│  - Verify error handling                  │
│  - Check fallback works                   │
│  → ScenarioResult: pass/fail              │
│                                           │
│ RiskAssessment:                           │
│  - Aggregate all check results            │
│  - Apply risk matrix weights              │
│  - Calculate risk score (0-1.0)           │
│  - Generate recommendations               │
│  → RiskAssessmentResponse                 │
│                                           │
└──────────────────────────────────────────┘
        ↓
    HTTP Response with RiskAssessmentResponse
        ↓
┌──────────────────────────────────────────┐
│ Risk Assessment Display (Frontend)       │
├──────────────────────────────────────────┤
│                                           │
│ - Risk level badge                        │
│ - Risk score progress bar                 │
│ - Issues list (critical/warning)          │
│ - Passed checks list                      │
│ - Recommendations                         │
│ - Full execution trace                    │
│ - Debug information                       │
│                                           │
└──────────────────────────────────────────┘
```

---

## ✅ Success Criteria

When DBA Sandbox is complete, it should:

1. ✓ **Connection Safety:**
   - Can determine if connection is alive
   - Can check user permissions
   - Can identify DB type
   - Prevents execution on production without warning

2. ✓ **Query Safety:**
   - Detects SQL injection attempts (100% accuracy required)
   - Estimates query performance impact
   - Checks for sensitive column exposure
   - Validates syntax for target DB

3. ✓ **Failure Scenarios:**
   - Can simulate each failure type
   - Verifies system handles gracefully
   - Shows what went wrong and why
   - Suggests fixes

4. ✓ **Risk Assessment:**
   - Risk score is meaningful (not arbitrary)
   - All critical issues detected
   - No false positives
   - Recommendations are actionable

5. ✓ **User Experience:**
   - Takes < 5 seconds to run assessment
   - Error messages are clear
   - No jargon without explanation
   - Can export/share results

---

## 🚀 Next: HR Sandbox

After DBA Sandbox is complete, apply same pattern to HR domain:
- RBAC enforcement testing
- Policy compliance validation
- Concurrent request handling
- Notification delivery verification
