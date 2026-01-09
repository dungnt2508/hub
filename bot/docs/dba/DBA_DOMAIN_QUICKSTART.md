# 🚀 DBA Domain - Quick Start Guide

## Overview

Domain DBA cung cấp các chức năng phân tích và giám sát database thông qua MCP DB integration.

## Use Cases

### 1. Analyze Slow Query
Phân tích các query chạy chậm trong database.

**Example Request:**
```json
{
  "message": "Phân tích query chậm trong PostgreSQL",
  "slots": {
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@host:5432/db",
    "limit": 10,
    "min_duration_ms": 1000
  }
}
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "slow_queries": [
      {
        "query": "SELECT * FROM users WHERE ...",
        "calls": 1000,
        "mean_time_ms": 2500,
        "max_time_ms": 5000
      }
    ],
    "count": 1,
    "db_type": "postgresql"
  },
  "message": "Tìm thấy 1 query chạy chậm"
}
```

### 2. Check Index Health
Kiểm tra sức khỏe của các index.

**Example Request:**
```json
{
  "message": "Kiểm tra index health trong MySQL",
  "slots": {
    "db_type": "mysql",
    "connection_string": "mysql://user:pass@host:3306/db",
    "schema": "mydb"
  }
}
```

### 3. Detect Blocking
Phát hiện các blocking queries.

**Example Request:**
```json
{
  "message": "Phát hiện blocking trong SQL Server",
  "slots": {
    "db_type": "sqlserver",
    "connection_string": "mssql+pyodbc://user:pass@host:1433/db"
  }
}
```

## Architecture

```
User Request
    ↓
Router (routes to DBA domain)
    ↓
DBA Entry Handler
    ↓
Use Case (e.g., AnalyzeSlowQueryUseCase)
    ↓
MCP DB Client
    ↓
MCP DB Server
    ↓
Database (PostgreSQL/MySQL/SQL Server/etc.)
```

## Setup

### 1. Environment Variables

```bash
# MCP DB Server URL
MCP_DB_SERVER_URL=http://localhost:8387

# Optional: Default database connections
DBA_DEFAULT_POSTGRESQL_URL=postgresql://user:pass@host:5432/db
```

### 2. MCP Server Setup

Cần có MCP DB Server running. Có thể:
- Sử dụng MCP server từ catalog
- Build custom MCP server
- Sử dụng existing MCP tools

### 3. Register Domain

Domain sẽ tự động được discover bởi `UseCaseRegistry` sau khi implement.

## Supported Databases

- ✅ PostgreSQL
- ✅ MySQL
- ✅ SQL Server
- 🔄 MongoDB (planned)
- 🔄 Oracle (planned)

## Example Usage

### Via API

```bash
curl -X POST http://localhost:8386/api/v1/router/route \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Phân tích query chậm trong PostgreSQL",
    "user_id": "user-123"
  }'
```

### Via Python

```python
from backend.domain.dba.entry_handler import DBAEntryHandler
from backend.schemas import DomainRequest

handler = DBAEntryHandler()

request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "postgresql",
        "connection_string": "postgresql://...",
        "limit": 10
    },
    user_context={"user_id": "user-123"}
)

response = await handler.handle(request)
print(response.message)
```

## Troubleshooting

### MCP Server Connection Failed
- Check `MCP_DB_SERVER_URL` environment variable
- Verify MCP server is running
- Check network connectivity

### Database Connection Failed
- Verify connection string format
- Check database credentials
- Ensure database is accessible from MCP server

### Unsupported Database Type
- Check `DatabaseType` enum for supported types
- Add new database type if needed

## Next Steps

1. Review [DBA_DOMAIN_PLAN.md](DBA_DOMAIN_PLAN.md) for detailed architecture
2. Check [DBA_DOMAIN_CHECKLIST.md](DBA_DOMAIN_CHECKLIST.md) for implementation tasks
3. Start with Phase 1: Foundation

