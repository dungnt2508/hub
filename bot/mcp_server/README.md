# MCP DB Server

Custom MCP Server cho database operations, hỗ trợ nhiều loại database khác nhau.

## Features

- ✅ PostgreSQL support
- ✅ MySQL support  
- ✅ SQL Server support
- ✅ Raw query execution (used by backend execution flow)
- ✅ Connection info endpoint
- ✅ Health check endpoint

## Endpoints

### POST `/execute`
Execute raw SQL query (used by backend execution flow).

**Request:**
```json
{
  "db_type": "postgresql",
  "query": "SELECT * FROM users LIMIT 10",
  "connection_string": "postgresql://user:pass@host:5432/db",
  "params": {}
}
```

**Response:**
```json
{
  "data": [...],
  "error": null
}
```

### POST `/connection-info`
Get database connection information.

**Request:**
```json
{
  "db_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/db"
}
```

**Response:**
```json
{
  "data": {
    "database_type": "postgresql",
    "version": "14.5",
    "database": "mydb",
    "user": "postgres"
  },
  "error": null
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-db-server"
}
```

## Database Connection Strings (optional, can be passed in requests)

Set environment variables for default connections:
```bash
DBA_DEFAULT_POSTGRESQL_URL=postgresql://user:pass@host:5432/db
DBA_DEFAULT_MYSQL_URL=mysql://user:pass@host:3306/db
DBA_DEFAULT_SQLSERVER_URL=mssql+pyodbc://user:pass@host:1433/database
```

## Usage

### Run Server
```bash
cd bot/mcp_server
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Or use the run script:
```bash
python -m mcp_server.run_server
```

### Test Endpoint
```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "query": "SELECT version()",
    "connection_string": "postgresql://user:pass@host:5432/db"
  }'
```

## Architecture

**MCP Server Role:**
- Provides database adapter layer (PostgreSQL, MySQL, SQL Server)
- Executes raw SQL queries (queries come from backend `dba_query_templates` table)
- Used by backend execution flow (ExecutionPlan → MCP execute)

**Query Management:**
- ✅ Queries are managed centrally in backend database (`dba_query_templates` table)
- ✅ Backend execution flow loads queries from DB and sends to MCP `/execute`
- ✅ MCP server does NOT store queries (queries come from backend)

**Note:** 
- Standalone query endpoints (like `/slow-queries`, `/wait-stats`) have been removed
- All queries are managed centrally in backend database
- Backend execution flow uses `/execute` endpoint with queries from DB

---

## Adding New Database Type

1. Add adapter in `database_adapters.py`
2. Update `DatabaseType` enum
3. Register adapter in `_adapters` dict
