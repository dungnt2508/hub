# MCP DB Server

Custom MCP Server cho database operations, hỗ trợ nhiều loại database khác nhau.

## Features

- ✅ PostgreSQL support
- ✅ MySQL support
- 🔄 SQL Server support (partial)
- 🔄 MongoDB support (planned)
- 🔄 Oracle support (planned)

## API Endpoints

### POST /execute
Execute custom SQL query

### POST /slow-queries
Get slow queries from database

### POST /wait-stats
Get wait statistics

### POST /index-stats
Get index statistics

### POST /blocking
Detect blocking sessions

### POST /connection-info
Get database connection information

### GET /health
Health check endpoint

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_PORT=8387
MCP_SERVER_HOST=0.0.0.0

# Database Connection Strings (optional, can be passed in requests)
DBA_DEFAULT_POSTGRESQL_URL=postgresql://user:pass@host:5432/db
DBA_DEFAULT_MYSQL_URL=mysql://user:pass@host:3306/db
```

### 3. Run Server

**Option 1: Using script (Recommended)**
```bash
# Linux/Mac
./scripts/start_mcp_server.sh

# Windows
scripts\start_mcp_server.bat
```

**Option 2: Direct run**
```bash
# From project root
python -m mcp_server.run_server

# Or using uvicorn
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8387
```

**Option 3: Docker (if added to docker-compose)**
```bash
docker-compose up mcp-server
```

### 4. Verify Server is Running

```bash
# Check health endpoint
curl http://localhost:8387/health

# Should return: {"status": "healthy", "service": "mcp-db-server"}
```

**⚠️ Important:** MCP Server must be running before testing database connections!

## Usage Example

### Get Slow Queries

```bash
curl -X POST http://localhost:8387/slow-queries \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/mydb",
    "limit": 10,
    "min_duration_ms": 1000
  }'
```

### Check Index Health

```bash
curl -X POST http://localhost:8387/index-stats \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/mydb",
    "schema": "public"
  }'
```

## Response Format

All endpoints return MCP protocol format:

```json
{
  "data": [...],
  "error": null
}
```

Or on error:

```json
{
  "data": null,
  "error": {
    "message": "Error message",
    "type": "ErrorType"
  }
}
```

## Development

### Adding New Database Type

1. Add adapter in `database_adapters.py`
2. Add query templates in `query_templates.py`
3. Update `DatabaseType` enum

### Testing

```bash
# Test health endpoint
curl http://localhost:8387/health
```

## Notes

- Connection strings are parsed and validated
- Query parameters are sanitized (basic implementation)
- For production, add proper SQL injection prevention
- Consider connection pooling for better performance

