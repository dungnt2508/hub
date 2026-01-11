# Database Connection Setup Guide for DBA Sandbox

## Overview

The DBA Sandbox supports real database connections for SQL Server, PostgreSQL, and MySQL. This guide shows how to configure and use them.

## Supported Databases

- ✅ **Microsoft SQL Server** (2016+)
- ✅ **PostgreSQL** (10+)
- ✅ **MySQL** (5.7+) / **MariaDB** (10.2+)

## Installation

### SQL Server Support (pyodbc)

```bash
# Install SQL Server driver
pip install pyodbc

# On Windows: ODBC Driver 17 for SQL Server is usually pre-installed
# On Linux/Mac:
brew install unixodbc  # macOS
sudo apt-get install unixodbc  # Ubuntu/Debian

# Then install driver
# macOS: brew install msodbcsql17
# Ubuntu: curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && ...
```

### PostgreSQL Support (psycopg2)

```bash
pip install psycopg2-binary
```

### MySQL Support (mysql-connector-python)

```bash
pip install mysql-connector-python
```

## Configuration

### Option 1: Environment Variable (Recommended)

```bash
# Set environment variable with JSON connection list
export DBA_CONNECTIONS_JSON='[
  {
    "id": "dev-1",
    "name": "DEV_SQL_SERVER",
    "db_type": "sql_server",
    "host": "localhost",
    "port": 1433,
    "database": "development",
    "username": "sa",
    "password": "YourPassword123",
    "is_production": false,
    "description": "Local development SQL Server"
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
    "description": "Production SQL Server"
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

### Option 2: Programmatic Registration

```python
from backend.domain.sandbox import get_registry, ConnectionConfig

registry = get_registry()

# Add connection
config = ConnectionConfig(
    id="dev-mysql",
    name="DEV_MYSQL",
    db_type="mysql",
    host="localhost",
    port=3306,
    database="development",
    username="root",
    password="root",
    is_production=False,
    description="Local MySQL for testing",
)

registry.add_connection(config)
```

## Usage in DBA Sandbox

### 1. Test Connection Validation

```bash
curl -X POST http://localhost:8000/api/admin/v1/test-sandbox/dba/validate-connection \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "connection_id": "dev-1"
  }'
```

**Response:**
```json
{
  "connection_id": "dev-1",
  "is_alive": true,
  "db_type": "sql_server",
  "is_production": false,
  "user_permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"],
  "server_version": "Microsoft SQL Server 2019 (15.0.2000.5)",
  "database_name": "development",
  "table_stats": [
    {
      "name": "users",
      "row_count": 100000,
      "size_mb": 12.5,
      "schema": "dbo"
    },
    ...
  ],
  "duration_ms": 145
}
```

### 2. Check Query Safety with Real Table Stats

```bash
curl -X POST http://localhost:8000/api/admin/v1/test-sandbox/dba/check-query-safety \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "connection_id": "dev-1",
    "sql_query": "SELECT * FROM users WHERE id = 1"
  }'
```

**Response:**
```json
{
  "query": "SELECT * FROM users WHERE id = 1",
  "syntax_valid": true,
  "sql_injection_safe": true,
  "performance_acceptable": true,
  "estimated_rows": 1,
  "estimated_duration_ms": 50,
  "sensitive_columns_found": null,
  "warnings": [
    "Using SELECT * - consider specifying columns explicitly"
  ],
  "errors": [],
  "duration_ms": 32
}
```

### 3. Full Risk Assessment

```bash
curl -X POST http://localhost:8000/api/admin/v1/test-sandbox/dba/assess-risk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "connection_id": "dev-1",
    "sql_query": "SELECT id, name FROM users WHERE status = 'active'",
    "simulate_failures": ["connection_timeout", "permission_denied"]
  }'
```

## Security Best Practices

### 1. Never Hardcode Passwords

❌ **Bad:**
```python
password = "MyPassword123"
```

✅ **Good:**
```python
password = os.getenv('DB_PASSWORD')  # From environment or vault
```

### 2. Use Read-Only Users for Sandbox

```sql
-- SQL Server
CREATE LOGIN readonly_user WITH PASSWORD = 'SecurePassword123'
CREATE USER readonly_user FOR LOGIN readonly_user
GRANT SELECT ON DATABASE::production TO readonly_user

-- PostgreSQL
CREATE USER readonly_user WITH PASSWORD 'SecurePassword123'
GRANT CONNECT ON DATABASE production TO readonly_user
GRANT USAGE ON SCHEMA public TO readonly_user
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user
```

### 3. Use Vault for Credentials

Instead of environment variables, integrate with:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Kubernetes Secrets

Example with Vault:
```python
import hvac

def get_connection_from_vault(connection_id: str):
    client = hvac.Client(url='http://vault.example.com:8200')
    secret = client.secrets.kv.v2.read_secret_version(
        path=f'database-connections/{connection_id}'
    )
    return secret['data']['data']
```

### 4. Connection Timeout and Limits

- Connection timeout: 5 seconds (prevents hanging)
- Query timeout: 30 seconds (prevents resource exhaustion)
- Max result rows: 10,000 (prevents memory issues)
- Connection limit: 10 per database (prevents saturation)

## Troubleshooting

### "pyodbc not installed"

```bash
pip install pyodbc

# If ODBC driver missing:
# Windows: Download from Microsoft
# macOS: brew install msodbcsql17
# Linux: Follow Microsoft docs for your distribution
```

### "Connection refused"

1. Verify host/port are correct
2. Check database server is running
3. Verify firewall allows connection
4. Check credentials

### "Permission denied"

1. Verify user has required permissions
2. Check database-level permissions
3. Check schema-level permissions
4. Check table-level permissions

### "Query timeout"

1. Query is too slow
2. Missing indexes
3. Large dataset

## Examples

### SQL Server Development Setup

```bash
# Using Docker
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourPassword123" \
  -p 1433:1433 \
  mcr.microsoft.com/mssql/server:2019-latest

# Set connection
export DBA_CONNECTIONS_JSON='[{
  "id":"dev-1","name":"DEV_DB","db_type":"sql_server",
  "host":"localhost","port":1433,"database":"master",
  "username":"sa","password":"YourPassword123",
  "is_production":false
}]'
```

### PostgreSQL Development Setup

```bash
# Using Docker
docker run -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:13

# Set connection
export DBA_CONNECTIONS_JSON='[{
  "id":"dev-pg","name":"DEV_PG","db_type":"postgresql",
  "host":"localhost","port":5432,"database":"postgres",
  "username":"postgres","password":"postgres",
  "is_production":false
}]'
```

### MySQL Development Setup

```bash
# Using Docker
docker run -e MYSQL_ROOT_PASSWORD=root \
  -p 3306:3306 \
  mysql:8

# Set connection
export DBA_CONNECTIONS_JSON='[{
  "id":"dev-mysql","name":"DEV_MYSQL","db_type":"mysql",
  "host":"localhost","port":3306,"database":"mysql",
  "username":"root","password":"root",
  "is_production":false
}]'
```

## Architecture

```
Frontend (Browser)
    ↓
API Endpoint (/test-sandbox/dba/check-query-safety)
    ↓
Connection Registry (get_registry())
    ↓
Database Client Factory
    ↓
Specific DB Client (SQLServerClient, PostgreSQLClient, etc.)
    ↓
Real Database Connection
    ↓
Table Statistics + Query Execution
    ↓
Query Cost Estimator (uses real stats)
    ↓
Risk Assessment Report
```

## Performance Considerations

### Connection Pooling

For production use, implement connection pooling:

```python
from sqlalchemy import create_engine

# SQL Server with pooling
engine = create_engine(
    'mssql+pyodbc://user:password@host/database?driver=ODBC+Driver+17+for+SQL+Server',
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

### Query Result Caching

Cache expensive validation results:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cache_query_cost(query_hash: str):
    # Return cached cost estimate
    pass

def estimate_with_cache(query: str):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return cache_query_cost(query_hash)
```

## Future Enhancements

- [ ] Connection pooling
- [ ] Query result caching
- [ ] Vault integration
- [ ] Connection health monitoring
- [ ] Query performance history
- [ ] Automated permission detection
- [ ] Index recommendation
