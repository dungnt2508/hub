# 🗄️ DBA Domain - Implementation Plan

**Ngày tạo**: 2026-01-08  
**Mục tiêu**: Xây dựng domain DBA để đảm bảo hiệu năng, độ ổn định và tính đúng đắn của hệ quản trị cơ sở dữ liệu  
**Trạng thái**: 📋 Planning

---

## 📋 Tóm Tắt Executive

Domain DBA sẽ cung cấp các chức năng phân tích và giám sát database thông qua:
- **12 Use Cases** cho các tác vụ DBA phổ biến
- **MCP DB Integration** để hỗ trợ đa dạng database engines (PostgreSQL, MySQL, SQL Server, MongoDB, etc.)
- **Clean Architecture** tuân thủ pattern hiện tại của project
- **Multi-database support** với abstraction layer

---

## 🎯 Use Cases

### 1. Performance Analysis
- **`analyze_slow_query`**: Phân tích các query chạy chậm
- **`analyze_query_regression`**: Phát hiện query performance regression
- **`analyze_wait_stats`**: Phân tích wait statistics
- **`analyze_io_pressure`**: Phân tích I/O pressure

### 2. Health & Monitoring
- **`check_index_health`**: Kiểm tra sức khỏe index
- **`detect_blocking`**: Phát hiện blocking queries
- **`detect_deadlock_pattern`**: Phát hiện deadlock patterns

### 3. Capacity & Planning
- **`capacity_forecast`**: Dự báo capacity

### 4. Validation & Comparison
- **`validate_custom_sql`**: Validate custom SQL queries
- **`compare_sp_blitz_vs_custom`**: So sánh sp_Blitz vs custom checks

### 5. Incident Management
- **`incident_triage`**: Phân loại và xử lý database incidents

---

## 🏗️ Kiến Trúc

### Cấu Trúc Thư Mục

```
backend/domain/dba/
├── __init__.py
├── entry_handler.py              # Entry point cho DBA domain
│
├── entities/                     # Domain Entities
│   ├── __init__.py
│   ├── query_analysis.py         # QueryAnalysis entity
│   ├── index_health.py           # IndexHealth entity
│   ├── blocking_session.py       # BlockingSession entity
│   ├── wait_stat.py              # WaitStat entity
│   ├── capacity_forecast.py      # CapacityForecast entity
│   └── incident.py               # Incident entity
│
├── use_cases/                    # Business Logic
│   ├── __init__.py
│   ├── base_use_case.py          # Base class (kế thừa từ shared)
│   │
│   ├── analyze_slow_query.py
│   ├── analyze_query_regression.py
│   ├── check_index_health.py
│   ├── detect_blocking.py
│   ├── detect_deadlock_pattern.py
│   ├── analyze_wait_stats.py
│   ├── analyze_io_pressure.py
│   ├── capacity_forecast.py
│   ├── validate_custom_sql.py
│   ├── compare_sp_blitz_vs_custom.py
│   └── incident_triage.py
│
├── ports/                        # Interfaces (Repository, MCP Client)
│   ├── __init__.py
│   ├── repository.py             # IDBARepository interface
│   └── mcp_client.py             # IMCPDBClient interface
│
├── adapters/                     # Implementations
│   ├── __init__.py
│   ├── mcp_db_client.py          # MCP DB Client implementation
│   └── postgresql_repository.py   # PostgreSQL repository (optional, nếu cần cache)
│
└── middleware/                   # Optional middleware
    ├── __init__.py
    └── rbac.py                    # RBAC cho DBA operations (nếu cần)
```

---

## 🔌 MCP DB Integration

### Architecture Pattern

```
┌─────────────────────────────────────────┐
│         DBA Use Cases                   │
│  (analyze_slow_query, etc.)             │
└──────────────┬──────────────────────────┘
               │
               │ uses
               ▼
┌─────────────────────────────────────────┐
│      IMCPDBClient (Port)                │
│  - execute_query(db_type, query)        │
│  - get_slow_queries(db_type, filters)   │
│  - get_wait_stats(db_type)              │
│  - get_index_stats(db_type)              │
│  - detect_blocking(db_type)              │
└──────────────┬──────────────────────────┘
               │
               │ implements
               ▼
┌─────────────────────────────────────────┐
│      MCPDBClient (Adapter)              │
│  - Connects to MCP DB Server            │
│  - Maps database-specific queries        │
│  - Handles connection pooling            │
│  - Error handling & retry logic         │
└──────────────┬──────────────────────────┘
               │
               │ calls
               ▼
┌─────────────────────────────────────────┐
│      MCP DB Server                      │
│  - PostgreSQL adapter                   │
│  - MySQL adapter                        │
│  - SQL Server adapter                   │
│  - MongoDB adapter                      │
│  - etc.                                 │
└─────────────────────────────────────────┘
```

### MCP Client Interface

```python
# ports/mcp_client.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    ORACLE = "oracle"
    SQLITE = "sqlite"

class IMCPDBClient(ABC):
    """Interface for MCP DB Client"""
    
    @abstractmethod
    async def execute_query(
        self,
        db_type: DatabaseType,
        query: str,
        connection_string: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on specified database"""
        pass
    
    @abstractmethod
    async def get_slow_queries(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        limit: int = 10,
        min_duration_ms: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get slow queries from database"""
        pass
    
    @abstractmethod
    async def get_wait_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get wait statistics"""
        pass
    
    @abstractmethod
    async def get_index_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get index statistics"""
        pass
    
    @abstractmethod
    async def detect_blocking(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Detect blocking sessions"""
        pass
    
    @abstractmethod
    async def get_connection_info(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get database connection info"""
        pass
```

### MCP Client Implementation

```python
# adapters/mcp_db_client.py
import httpx
from typing import Dict, Any, List, Optional
from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ...shared.logger import logger
from ...shared.exceptions import ExternalServiceError

class MCPDBClient(IMCPDBClient):
    """MCP DB Client implementation using MCP protocol"""
    
    def __init__(self, mcp_server_url: str = None):
        """
        Initialize MCP DB Client
        
        Args:
            mcp_server_url: MCP server URL (defaults to env var)
        """
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_DB_SERVER_URL", "http://localhost:8387")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_query(
        self,
        db_type: DatabaseType,
        query: str,
        connection_string: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query via MCP server"""
        try:
            response = await self.client.post(
                f"{self.mcp_server_url}/execute",
                json={
                    "db_type": db_type.value,
                    "query": query,
                    "connection_string": connection_string,
                    "params": params or {}
                }
            )
            response.raise_for_status()
            return response.json()["data"]
        except httpx.HTTPError as e:
            logger.error(f"MCP DB client error: {e}")
            raise ExternalServiceError(f"Failed to execute query: {e}")
    
    # Implement other methods...
```

---

## 📊 Database-Specific Query Mapping

### Query Templates per Database

Mỗi use case sẽ có query templates cho từng loại database:

```python
# adapters/query_templates.py
QUERY_TEMPLATES = {
    DatabaseType.POSTGRESQL: {
        "slow_queries": """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                max_time
            FROM pg_stat_statements
            WHERE mean_time > %(min_duration_ms)s
            ORDER BY mean_time DESC
            LIMIT %(limit)s
        """,
        "wait_stats": """
            SELECT 
                wait_event_type,
                wait_event,
                count(*) as wait_count
            FROM pg_stat_activity
            WHERE wait_event IS NOT NULL
            GROUP BY wait_event_type, wait_event
        """,
        "index_health": """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE idx_scan < 10
            ORDER BY idx_scan ASC
        """,
        "blocking": """
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocking_locks.pid AS blocking_pid,
                blocked_activity.query AS blocked_query,
                blocking_activity.query AS blocking_query
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
            WHERE NOT blocked_locks.granted
        """
    },
    DatabaseType.MYSQL: {
        "slow_queries": """
            SELECT 
                sql_text,
                exec_count,
                avg_timer_wait / 1000000000000 as avg_time_sec,
                max_timer_wait / 1000000000000 as max_time_sec
            FROM performance_schema.events_statements_summary_by_digest
            WHERE avg_timer_wait > %(min_duration_ns)s
            ORDER BY avg_timer_wait DESC
            LIMIT %(limit)s
        """,
        # ... other MySQL queries
    },
    DatabaseType.SQLSERVER: {
        "slow_queries": """
            SELECT TOP %(limit)s
                query_stats.execution_count,
                query_stats.total_elapsed_time / 1000000.0 as total_elapsed_time_ms,
                query_stats.avg_elapsed_time / 1000000.0 as avg_elapsed_time_ms,
                sql_text.text
            FROM sys.dm_exec_query_stats query_stats
            CROSS APPLY sys.dm_exec_sql_text(query_stats.sql_handle) AS sql_text
            WHERE query_stats.avg_elapsed_time / 1000000.0 > %(min_duration_ms)s
            ORDER BY query_stats.avg_elapsed_time DESC
        """,
        # ... other SQL Server queries
    }
}
```

---

## 🔄 Use Case Examples

### Example 1: Analyze Slow Query

```python
# use_cases/analyze_slow_query.py
from typing import Optional
from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.query_analysis import QueryAnalysis

class AnalyzeSlowQueryUseCase(BaseUseCase):
    """Analyze slow queries use case"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        self.mcp_client = mcp_client
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Extract slots
        db_type_str = request.slots.get("db_type", "postgresql")
        connection_string = request.slots.get("connection_string")
        limit = int(request.slots.get("limit", 10))
        min_duration_ms = int(request.slots.get("min_duration_ms", 1000))
        
        # Validate
        try:
            db_type = DatabaseType(db_type_str.lower())
        except ValueError:
            raise InvalidInputError(f"Unsupported database type: {db_type_str}")
        
        # Get slow queries via MCP
        slow_queries = await self.mcp_client.get_slow_queries(
            db_type=db_type,
            connection_string=connection_string,
            limit=limit,
            min_duration_ms=min_duration_ms
        )
        
        # Create entities
        analyses = [
            QueryAnalysis.from_dict(q) for q in slow_queries
        ]
        
        # Build response
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "slow_queries": [a.to_dict() for a in analyses],
                "count": len(analyses),
                "db_type": db_type.value
            },
            message=f"Tìm thấy {len(analyses)} query chạy chậm"
        )
```

### Example 2: Check Index Health

```python
# use_cases/check_index_health.py
class CheckIndexHealthUseCase(BaseUseCase):
    """Check index health use case"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        self.mcp_client = mcp_client
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        db_type_str = request.slots.get("db_type", "postgresql")
        connection_string = request.slots.get("connection_string")
        schema = request.slots.get("schema")
        
        db_type = DatabaseType(db_type_str.lower())
        
        # Get index stats
        index_stats = await self.mcp_client.get_index_stats(
            db_type=db_type,
            connection_string=connection_string,
            schema=schema
        )
        
        # Analyze health
        unhealthy_indexes = [
            idx for idx in index_stats
            if idx.get("idx_scan", 0) < 10  # Rarely used
        ]
        
        return DomainResponse(
            status=DomainResult.SUCCESS,
            data={
                "unhealthy_indexes": unhealthy_indexes,
                "total_indexes": len(index_stats),
                "unhealthy_count": len(unhealthy_indexes)
            },
            message=f"Phát hiện {len(unhealthy_indexes)} index không khỏe mạnh"
        )
```

---

## 🔐 Security & RBAC

### RBAC Middleware (Optional)

```python
# middleware/rbac.py
class DBARBACMiddleware:
    """RBAC middleware for DBA operations"""
    
    PERMISSIONS = {
        "analyze_slow_query": ["dba.read", "dba.analyze"],
        "check_index_health": ["dba.read", "dba.analyze"],
        "detect_blocking": ["dba.read", "dba.monitor"],
        "incident_triage": ["dba.admin", "dba.incident"],
    }
    
    async def enforce_permission(
        self,
        user_id: str,
        operation: str
    ):
        """Enforce permission check"""
        required_perms = self.PERMISSIONS.get(operation, [])
        # Check user permissions...
        pass
```

---

## 📦 Dependencies

### New Dependencies

```txt
# requirements.txt additions
httpx>=0.25.0  # For MCP client (already exists)
pydantic>=2.0.0  # For entities (already exists)
```

### MCP DB Server

Cần setup MCP DB Server riêng hoặc sử dụng MCP server có sẵn. Có thể:
1. Sử dụng MCP server từ MCP catalog
2. Build custom MCP server với database adapters
3. Sử dụng existing MCP tools nếu có

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Tạo cấu trúc thư mục domain/dba
- [ ] Implement MCP DB Client interface và adapter
- [ ] Tạo base entities (QueryAnalysis, IndexHealth, etc.)
- [ ] Implement 2-3 use cases cơ bản (analyze_slow_query, check_index_health)
- [ ] Unit tests cho MCP client

### Phase 2: Core Use Cases (Week 2)
- [ ] Implement remaining use cases
- [ ] Database-specific query templates
- [ ] Error handling và retry logic
- [ ] Integration tests với test databases

### Phase 3: Advanced Features (Week 3)
- [ ] Incident triage logic
- [ ] Capacity forecasting algorithms
- [ ] Query regression detection
- [ ] RBAC middleware (nếu cần)

### Phase 4: Integration & Testing (Week 4)
- [ ] Register domain trong use_case_registry
- [ ] Add routing patterns cho DBA domain
- [ ] End-to-end testing
- [ ] Documentation

---

## 🔗 Integration Points

### 1. Router Integration

Cần thêm patterns cho DBA domain trong `intent_registry.yaml`:

```yaml
dba:
  patterns:
    - "phân tích query chậm"
    - "kiểm tra index"
    - "phát hiện blocking"
    - "phân tích wait stats"
    - "dự báo capacity"
  intents:
    - analyze_slow_query
    - check_index_health
    - detect_blocking
    - analyze_wait_stats
    - capacity_forecast
    - incident_triage
```

### 2. Use Case Registry

Update `use_case_registry.py`:

```python
# backend/domain/use_case_registry.py
from .dba.entry_handler import DBAEntryHandler

# In _discover_use_cases:
dba_handler = DBAEntryHandler()
dba_intents = list(dba_handler.use_cases.keys())

self._domains["dba"] = {
    "name": "dba",
    "display_name": "Quản trị Database",
    "description": "Phân tích và giám sát database",
    "intents": [
        {
            "intent": intent,
            "display_name": self._format_intent_name(intent),
            "description": self._get_intent_description("dba", intent),
            "intent_type": "OPERATION",
        }
        for intent in dba_intents
    ],
    "intent_type": "OPERATION",
}
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test each use case với mock MCP client
- Test entity validation
- Test query template mapping

### Integration Tests
- Test với real MCP server (test containers)
- Test với multiple database types
- Test error scenarios

### E2E Tests
- Test full flow từ router → domain → response
- Test với real user queries

---

## 📝 Configuration

### Environment Variables

```bash
# MCP DB Server
MCP_DB_SERVER_URL=http://localhost:8387

# Default database connections (optional, có thể pass qua slots)
DBA_DEFAULT_POSTGRESQL_URL=postgresql://user:pass@host:5432/db
DBA_DEFAULT_MYSQL_URL=mysql://user:pass@host:3306/db

# RBAC (nếu cần)
DBA_RBAC_ENABLED=true
```

---

## 🎯 Success Criteria

- ✅ Tất cả 12 use cases hoạt động đúng
- ✅ Hỗ trợ ít nhất 3 database types (PostgreSQL, MySQL, SQL Server)
- ✅ MCP integration hoạt động ổn định
- ✅ Error handling đầy đủ
- ✅ Unit tests coverage > 80%
- ✅ Documentation đầy đủ

---

## 📚 References

- [Clean Architecture Pattern](../clean_architecture/)
- [HR Domain Implementation](../domain/hr/) (reference)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- Database-specific documentation:
  - PostgreSQL: pg_stat_statements, pg_stat_activity
  - MySQL: performance_schema
  - SQL Server: sys.dm_exec_query_stats, sys.dm_os_wait_stats

---

## ❓ Open Questions

1. **MCP Server**: Sử dụng MCP server có sẵn hay build custom?
2. **Connection Management**: Làm thế nào để manage database connections? (connection pool, credentials)
3. **Caching**: Có cần cache kết quả phân tích không?
4. **Real-time vs Batch**: Use cases chạy real-time hay batch?
5. **Alerting**: Có tích hợp alerting system không?

---

**Next Steps**: Review plan và bắt đầu Phase 1 implementation.

