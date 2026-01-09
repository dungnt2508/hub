# 🔐 DBA Domain - Connection Management

## Overview

Hệ thống quản lý connections cho phép lưu trữ và quản lý nhiều database connections một cách an toàn với encryption.

## Architecture

```
┌─────────────────────────────────────────┐
│      DBA Use Cases                      │
│  (analyze_slow_query, etc.)            │
└──────────────┬──────────────────────────┘
               │
               │ uses connection_name/connection_id
               ▼
┌─────────────────────────────────────────┐
│      MCP DB Client                      │
│  - Resolves connection from registry    │
└──────────────┬──────────────────────────┘
               │
               │ looks up
               ▼
┌─────────────────────────────────────────┐
│      Connection Registry                 │
│  - get_connection_string()              │
└──────────────┬──────────────────────────┘
               │
               │ queries
               ▼
┌─────────────────────────────────────────┐
│      Connection Repository               │
│  - PostgreSQL implementation            │
└──────────────┬──────────────────────────┘
               │
               │ reads from
               ▼
┌─────────────────────────────────────────┐
│      dba_connections table              │
│  - Encrypted connection strings         │
│  - Metadata (name, environment, tags)   │
└─────────────────────────────────────────┘
```

## Database Schema

### Table: `dba_connections`

```sql
CREATE TABLE dba_connections (
    id BIGSERIAL PRIMARY KEY,
    connection_id VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL,
    connection_string TEXT NOT NULL,  -- Encrypted
    description TEXT,
    environment VARCHAR(50),
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'active',
    last_tested_at TIMESTAMP,
    last_error TEXT,
    created_by VARCHAR(255),
    tenant_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, tenant_id)
);

CREATE INDEX idx_dba_connections_db_type ON dba_connections(db_type);
CREATE INDEX idx_dba_connections_tenant ON dba_connections(tenant_id);
CREATE INDEX idx_dba_connections_status ON dba_connections(status);
CREATE INDEX idx_dba_connections_environment ON dba_connections(environment);
```

## Usage

### 1. Create Connection

```python
from backend.domain.dba.services.connection_registry import connection_registry

# Create connection (connection string will be encrypted)
connection = await connection_registry.create_connection(
    name="SQL Server Production",
    db_type="sqlserver",
    connection_string="mssql+pyodbc://user:pass@server:1433/database",
    description="Production SQL Server",
    environment="production",
    tags=["production", "sqlserver", "critical"],
    created_by="admin@example.com",
    tenant_id="tenant-123"
)
```

### 2. Use Connection in Use Cases

```python
# Option 1: Use connection_name
request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "sqlserver",
        "connection_name": "SQL Server Production",  # Lookup from registry
        "limit": 10
    },
    user_context={"user_id": "user-123", "tenant_id": "tenant-123"}
)

# Option 2: Use connection_id
request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "sqlserver",
        "connection_id": "uuid-here",  # Lookup from registry
        "limit": 10
    },
    user_context={"user_id": "user-123"}
)

# Option 3: Use connection_string directly (for testing)
request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "sqlserver",
        "connection_string": "mssql://...",  # Direct connection
        "limit": 10
    },
    user_context={"user_id": "user-123"}
)
```

### 3. List Connections

```python
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

### 4. Update Connection

```python
await connection_registry.update_connection(
    connection_id="uuid-here",
    description="Updated description",
    status="inactive"
)
```

### 5. Delete Connection

```python
await connection_registry.delete_connection("uuid-here")
```

## Encryption

Connection strings được encrypt bằng Fernet (symmetric encryption) từ `cryptography` library.

### Setup Encryption Key

```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in environment
export DB_CONNECTION_ENCRYPTION_KEY="your-generated-key-here"
```

### Security Notes

- ✅ Connection strings được encrypt trong database
- ✅ Decryption chỉ xảy ra khi cần sử dụng
- ✅ Connection strings không được expose trong API responses (mặc định)
- ⚠️ Encryption key phải được bảo vệ (không commit vào git)
- ⚠️ Consider using key management service (AWS KMS, Azure Key Vault) trong production

## Migration

Run migration để tạo table:

```bash
cd bot
alembic upgrade head
```

## Example: 20 SQL Server Connections

```python
# Create 20 SQL Server connections
servers = [
    {"name": f"SQL Server {i}", "host": f"server{i}.example.com"}
    for i in range(1, 21)
]

for server in servers:
    connection = await connection_registry.create_connection(
        name=server["name"],
        db_type="sqlserver",
        connection_string=f"mssql+pyodbc://user:pass@{server['host']}:1433/db",
        environment="production",
        tags=["sqlserver", "production"],
        tenant_id="tenant-123"
    )
    print(f"Created: {connection.connection_id} - {connection.name}")

# Use in use cases
request = DomainRequest(
    intent="analyze_slow_query",
    slots={
        "db_type": "sqlserver",
        "connection_name": "SQL Server 1",  # Automatically resolved
        "limit": 10
    },
    user_context={"user_id": "user-123", "tenant_id": "tenant-123"}
)
```

## Admin API (Future)

Có thể tạo Admin API để quản lý connections qua web interface:

```python
# POST /admin/dba/connections
# GET /admin/dba/connections
# PUT /admin/dba/connections/{id}
# DELETE /admin/dba/connections/{id}
# POST /admin/dba/connections/{id}/test
```

## Best Practices

1. **Naming Convention**: Sử dụng tên rõ ràng, ví dụ: "SQL Server Production - DB1"
2. **Environment Tags**: Tag connections theo environment (prod, staging, dev)
3. **Regular Testing**: Test connections định kỳ để đảm bảo chúng vẫn hoạt động
4. **Access Control**: Sử dụng tenant_id để phân quyền
5. **Rotation**: Rotate credentials và update connections khi cần

---

**Ready to use!** 🎉

