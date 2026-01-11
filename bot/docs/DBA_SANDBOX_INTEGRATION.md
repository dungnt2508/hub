# DBA Sandbox Integration Guide

## Overview

DBA Sandbox hiện đã fully integrate với connection registry. Khi bạn setup database connections, chúng sẽ tự động hiển thị trong sandbox.

## How It Works

### 1. Connection Registry (Backend)

```
Environment Variable
    ↓
DBA_CONNECTIONS_JSON
    ↓
ConnectionRegistry.load_from_env()
    ↓
Stored in memory with get_registry()
```

### 2. API Endpoints

```
GET /api/admin/v1/test-sandbox/dba/connections
    ├─ Loads from ConnectionRegistry
    ├─ Tests each connection
    ├─ Returns status + permissions
    └─ Displayed in Frontend

GET /api/admin/v1/test-sandbox/dba/connections/{id}
    ├─ Get specific connection
    └─ Returns detailed info

POST /api/admin/v1/test-sandbox/dba/validate-connection
    ├─ Uses registry to get connection config
    ├─ Creates database client
    ├─ Tests connection + gets stats
    └─ Returns validation result
```

### 3. Frontend Integration

```
DBA Sandbox Page
    ↓
useEffect: loadConnections()
    ↓
dbaSandboxService.getConnections()
    ↓
GET /api/admin/v1/test-sandbox/dba/connections
    ↓
Display in UI with status badges
    ├─ 🟢 Available (green)
    ├─ ✗ Unavailable (gray)
    ├─ 🔴 Production (red)
    └─ Permissions list
```

## Setup Instructions

### Step 1: Install Database Drivers

```bash
# SQL Server
pip install pyodbc

# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install mysql-connector-python
```

### Step 2: Configure Connections

Create `DBA_CONNECTIONS_JSON` environment variable:

```bash
export DBA_CONNECTIONS_JSON='[
  {
    "id": "dev-1",
    "name": "DEV_DB",
    "db_type": "sql_server",
    "host": "localhost",
    "port": 1433,
    "database": "development",
    "username": "sa",
    "password": "YourPassword123",
    "is_production": false,
    "description": "Local development database"
  },
  {
    "id": "prod-1",
    "name": "PROD_MAIN",
    "db_type": "sql_server",
    "host": "prod-server.example.com",
    "port": 1433,
    "database": "production",
    "username": "readonly_user",
    "password": "SecurePassword456",
    "is_production": true,
    "description": "Production database (read-only)"
  },
  {
    "id": "dev-pg",
    "name": "DEV_POSTGRES",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "development",
    "username": "postgres",
    "password": "postgres",
    "is_production": false,
    "description": "Local PostgreSQL"
  }
]'
```

### Step 3: Start Backend

Backend sẽ tự động load connections từ environment:

```bash
# Backend automatically loads DBA_CONNECTIONS_JSON
python -m uvicorn backend.interface.api:app --reload
```

### Step 4: Access DBA Sandbox

Navigate to:
```
http://localhost:3000/admin/domain-sandboxes/dba
```

Frontend sẽ:
1. Load connections từ backend
2. Test mỗi connection
3. Display status + permissions
4. Allow user để select connection

## What Happens When You Load Sandbox

### Backend Flow

```
GET /api/admin/v1/test-sandbox/dba/connections
                    ↓
ConnectionRegistry.get_registry()
                    ↓
registry.list_connections()
                    ↓
For each connection:
    ├─ Create DatabaseClient
    ├─ Test connection (SELECT 1)
    ├─ Get permissions (SHOW GRANTS)
    ├─ Get table stats (sys.tables)
    └─ Return status + permissions
                    ↓
HTTP Response: Connection[] with status
```

### Frontend Flow

```
Frontend loads
    ↓
useEffect: loadConnections()
    ↓
dbaSandboxService.getConnections()
    ↓
Render connection list:
    ├─ If is_available == true: 🟢 Green (selectable)
    ├─ If is_available == false: ✗ Gray (disabled)
    ├─ If is_production == true: 🔴 Red label
    └─ Show permissions: ["SELECT", "INSERT", ...]
    ↓
User selects connection
    ↓
When running test:
    POST /api/admin/v1/test-sandbox/dba/validate-connection
```

## Connection Status Indicators

### 🟢 Available (Green)
- Connection alive ✓
- Credentials valid ✓
- User has SELECT permission ✓
- Ready to use!

### ✗ Unavailable (Gray)
- Host unreachable ✗
- Credentials wrong ✗
- User has no permissions ✗
- Cannot use - fix configuration

### 🔴 Production (Red Label)
- Extra warning displayed
- Should have minimal permissions
- Test thoroughly before using

## Example Workflows

### Workflow 1: Test Development Connection

```
1. Open DBA Sandbox
2. See DEV_DB: 🟢 Available
3. Click radio button to select DEV_DB
4. Enter query: "SELECT COUNT(*) FROM users"
5. Click "Run Risk Assessment"
6. Backend:
   - Uses dev-1 connection config from registry
   - Connects to localhost:1433
   - Analyzes query
   - Gets real table stats
   - Returns assessment
7. Frontend displays results
```

### Workflow 2: Production Connection with Failure

```
1. Admin sets up PROD_MAIN connection in registry
2. PROD_MAIN: ✗ Unavailable (host unreachable)
3. Admin investigates:
   - Check host/port correct
   - Check firewall allows connection
   - Check credentials valid
4. After fixing, sandbox auto-reloads
5. Now PROD_MAIN: 🟢 Available
```

### Workflow 3: Add New Connection

```
1. DBA adds new connection to environment:
   export DBA_CONNECTIONS_JSON='[..., {new_connection}]'
2. Restart backend
3. Open DBA Sandbox
4. New connection appears in list
5. Frontend tests it automatically
```

## Troubleshooting

### Connections Not Showing

**Problem:** DBA Sandbox shows "No connections configured"

**Solution:**
```bash
# 1. Check environment variable is set
echo $DBA_CONNECTIONS_JSON

# 2. Validate JSON format
python -m json.tool <<< "$DBA_CONNECTIONS_JSON"

# 3. Restart backend
# Backend loads connections on startup

# 4. Check browser console for errors
# Open DevTools → Console tab
```

### Connection Shows ✗ Unavailable

**Problem:** Connection is configured but marked unavailable

**Solution:**
```bash
# 1. Check connection is alive
telnet localhost 1433

# 2. Check credentials
# For SQL Server, try: sqlcmd -S localhost -U sa -P password
# For PostgreSQL: psql -h localhost -U postgres

# 3. Check permissions
# The user needs SELECT permission

# 4. Check firewall
# Port 1433 (SQL) or 5432 (PG) must be open
```

### Permissions Not Showing

**Problem:** Connection shows available but no permissions listed

**Solution:**
```bash
# 1. Verify user exists
SELECT name FROM sys.sql_logins  -- SQL Server
SELECT usename FROM pg_user      -- PostgreSQL

# 2. Grant minimum permissions
-- SQL Server
GRANT SELECT ON DATABASE::your_db TO your_user

-- PostgreSQL
GRANT CONNECT ON DATABASE your_db TO your_user
GRANT USAGE ON SCHEMA public TO your_user
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user
```

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│ DBA Sandbox Frontend                        │
│ /admin/domain-sandboxes/dba                 │
├─────────────────────────────────────────────┤
│ • Connection Selector                       │
│ • Query Input                               │
│ • Risk Assessment Display                   │
└─────────────────────────────────────────────┘
                    ↓ (REST API)
┌─────────────────────────────────────────────┐
│ Backend API                                 │
│ /api/admin/v1/test-sandbox/dba              │
├─────────────────────────────────────────────┤
│ • GET /connections                          │
│ • GET /connections/{id}                     │
│ • POST /validate-connection                 │
│ • POST /check-query-safety                  │
│ • POST /assess-risk                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Connection Registry                         │
├─────────────────────────────────────────────┤
│ • Load from DBA_CONNECTIONS_JSON            │
│ • Store connections in memory               │
│ • Manage connection lifecycle               │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Database Clients                            │
├─────────────────────────────────────────────┤
│ • SQLServerClient (pyodbc)                  │
│ • PostgreSQLClient (psycopg2)               │
│ • MySQLClient (mysql-connector)             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Real Databases                              │
├─────────────────────────────────────────────┤
│ • Production SQL Server                     │
│ • Development PostgreSQL                    │
│ • Analytics MySQL                           │
└─────────────────────────────────────────────┘
```

## Security Considerations

### ✅ Do's
- ✓ Store passwords in environment variables
- ✓ Use read-only users for production
- ✓ Set connection timeouts
- ✓ Log all queries
- ✓ Audit access

### ❌ Don'ts
- ✗ Hardcode passwords in code
- ✗ Commit connection configs to git
- ✗ Use admin accounts for sandbox
- ✗ Allow unbounded query results
- ✗ Trust client-provided queries without validation

## Performance Tips

### Connection Pooling

For production use, add connection pooling:

```python
from sqlalchemy import create_engine

engine = create_engine(
    'mssql+pyodbc://user:password@host/db?driver=ODBC+Driver+17+for+SQL+Server',
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

### Query Result Caching

Cache expensive validations:

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query_cost(query_hash: str):
    # Return cached estimate
    pass

def estimate_with_cache(query: str):
    h = hashlib.md5(query.encode()).hexdigest()
    return cached_query_cost(h)
```

## Monitoring and Alerts

### Connection Health Check

Add monitoring to detect unavailable connections:

```python
async def health_check_connections():
    registry = get_registry()
    for conn in registry.list_connections():
        client = DatabaseClientFactory.create(...)
        is_alive, error = await client.test_connection()
        
        if not is_alive:
            logger.warning(f"Connection {conn.name} is unavailable: {error}")
            # Send alert to admin
```

## Next Steps

1. **Setup Connections**
   - Create DBA_CONNECTIONS_JSON
   - Test each connection
   - Verify permissions

2. **Deploy Backend**
   - Install database drivers
   - Set environment variable
   - Restart backend

3. **Test Frontend**
   - Open DBA Sandbox
   - Verify connections appear
   - Test query safety checks

4. **Monitor**
   - Check connection health
   - Review audit logs
   - Alert on failures
