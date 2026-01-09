# 🔐 DBA Connection Setup Guide - 20 SQL Server Example

## Tóm Tắt

Hệ thống Connection Management cho phép bạn lưu trữ và quản lý **20 SQL Server connections** (hoặc bất kỳ số lượng nào) một cách an toàn với encryption.

## 🎯 Giải Pháp

### 1. Lưu Trữ Connections

Connections được lưu trong **database table `dba_connections`** với:
- ✅ **Encryption**: Connection strings được encrypt bằng Fernet
- ✅ **Metadata**: Name, environment, tags để dễ quản lý
- ✅ **Multi-tenant**: Hỗ trợ tenant_id để phân quyền
- ✅ **Status tracking**: Track connection status và last tested

### 2. Sử Dụng Connections

Có 3 cách để specify connection:

1. **Connection Name** (Recommended):
   ```python
   slots = {
       "db_type": "sqlserver",
       "connection_name": "SQL Server Production 01"
   }
   ```

2. **Connection ID**:
   ```python
   slots = {
       "db_type": "sqlserver",
       "connection_id": "uuid-here"
   }
   ```

3. **Connection String** (Direct, for testing):
   ```python
   slots = {
       "db_type": "sqlserver",
       "connection_string": "mssql://..."
   }
   ```

## 📋 Setup Steps

### Step 1: Run Migration

```bash
cd bot
alembic upgrade head
```

Tạo table `dba_connections` trong database.

### Step 2: Set Encryption Key

```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "DB_CONNECTION_ENCRYPTION_KEY=your-generated-key-here" >> .env
```

### Step 3: Create Connections

#### Option A: Using Script

```bash
python scripts/setup_sqlserver_connections.py
```

#### Option B: Using Python API

```python
from backend.domain.dba.services.connection_registry import connection_registry

# Create 20 connections
for i in range(1, 21):
    connection = await connection_registry.create_connection(
        name=f"SQL Server Production {i:02d}",
        db_type="sqlserver",
        connection_string=f"mssql+pyodbc://user:pass@server{i}.example.com:1433/db",
        environment="production",
        tags=["sqlserver", "production"],
        tenant_id="tenant-123"
    )
    print(f"Created: {connection.connection_id}")
```

#### Option C: Using Admin API (Future)

```bash
POST /admin/dba/connections
{
  "name": "SQL Server Production 01",
  "db_type": "sqlserver",
  "connection_string": "mssql+pyodbc://...",
  "environment": "production",
  "tags": ["sqlserver", "production"]
}
```

## 🚀 Usage Examples

### Example 1: Analyze Slow Query

```python
from backend.domain.dba.entry_handler import DBAEntryHandler
from backend.schemas import DomainRequest

handler = DBAEntryHandler()

# Use connection by name
request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "sqlserver",
        "connection_name": "SQL Server Production 01",  # ✅ Lookup from registry
        "limit": 10,
        "min_duration_ms": 1000
    },
    user_context={
        "user_id": "user-123",
        "tenant_id": "tenant-123"
    }
)

response = await handler.handle(request)
print(response.message)
```

### Example 2: Check Index Health

```python
request = DomainRequest(
    intent="check_index_health",
    slots={
        "db_type": "sqlserver",
        "connection_name": "SQL Server Production 02",
        "schema": "dbo"
    },
    user_context={"user_id": "user-123", "tenant_id": "tenant-123"}
)

response = await handler.handle(request)
```

### Example 3: Detect Blocking

```python
request = DomainRequest(
    intent="detect_blocking",
    slots={
        "db_type": "sqlserver",
        "connection_id": "uuid-of-connection"  # ✅ Use connection_id
    },
    user_context={"user_id": "user-123", "tenant_id": "tenant-123"}
)

response = await handler.handle(request)
```

## 📊 List Connections

```python
from backend.domain.dba.services.connection_registry import connection_registry

# List all SQL Server connections
connections = await connection_registry.list_connections(
    db_type="sqlserver",
    tenant_id="tenant-123",
    environment="production",
    status="active"
)

for conn in connections:
    print(f"{conn.name} - {conn.environment} - {conn.status}")
```

## 🔄 Update Connection

```python
# Update connection
await connection_registry.update_connection(
    connection_id="uuid-here",
    description="Updated description",
    status="inactive"
)
```

## 🗑️ Delete Connection

```python
await connection_registry.delete_connection("uuid-here")
```

## 🔍 Connection Lookup Flow

```
User Request
    ↓
Use Case (analyze_slow_query)
    ↓
MCP DB Client
    ↓
Connection Registry
    ↓ (lookup by name/id)
Connection Repository
    ↓ (query database)
dba_connections table
    ↓ (decrypt)
Connection String
    ↓
MCP Server
    ↓
SQL Server
```

## 📝 Best Practices

1. **Naming Convention**:
   - `SQL Server Production 01`
   - `SQL Server Staging - DB1`
   - `MySQL Production - Analytics`

2. **Environment Tags**:
   - `production`
   - `staging`
   - `development`

3. **Tags for Filtering**:
   - `["sqlserver", "production", "critical"]`
   - `["mysql", "analytics", "read-only"]`

4. **Security**:
   - ✅ Never commit encryption key to git
   - ✅ Use key management service in production
   - ✅ Rotate credentials regularly
   - ✅ Test connections periodically

## 🎯 Summary

Với hệ thống này, bạn có thể:

- ✅ Lưu trữ **20 SQL Server connections** (hoặc bất kỳ số lượng nào)
- ✅ Sử dụng bằng **connection_name** thay vì connection_string
- ✅ **Encryption** tự động cho connection strings
- ✅ **Multi-tenant** support
- ✅ **Metadata** và **tagging** để quản lý dễ dàng

**Ready to use!** 🎉

