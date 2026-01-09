# ✅ DBA Domain - Implementation Checklist

## Phase 1: Foundation (Week 1)

### Infrastructure Setup
- [ ] Tạo cấu trúc thư mục `backend/domain/dba/`
- [ ] Tạo `__init__.py` files
- [ ] Setup base imports

### MCP DB Integration
- [ ] Tạo `ports/mcp_client.py` với `IMCPDBClient` interface
- [ ] Tạo `adapters/mcp_db_client.py` implementation
- [ ] Implement `execute_query()` method
- [ ] Implement `get_slow_queries()` method
- [ ] Implement `get_wait_stats()` method
- [ ] Implement `get_index_stats()` method
- [ ] Implement `detect_blocking()` method
- [ ] Implement `get_connection_info()` method
- [ ] Error handling và retry logic
- [ ] Unit tests cho MCP client

### Entities
- [ ] Tạo `entities/query_analysis.py`
- [ ] Tạo `entities/index_health.py`
- [ ] Tạo `entities/blocking_session.py`
- [ ] Tạo `entities/wait_stat.py`
- [ ] Tạo `entities/capacity_forecast.py`
- [ ] Tạo `entities/incident.py`
- [ ] Unit tests cho entities

### Base Use Cases
- [ ] Tạo `use_cases/base_use_case.py` (kế thừa từ shared)
- [ ] Implement `analyze_slow_query.py`
- [ ] Implement `check_index_health.py`
- [ ] Implement `detect_blocking.py`
- [ ] Unit tests cho use cases

### Entry Handler
- [ ] Tạo `entry_handler.py`
- [ ] Register use cases
- [ ] Error handling

---

## Phase 2: Core Use Cases (Week 2)

### Query Templates
- [ ] Tạo `adapters/query_templates.py`
- [ ] PostgreSQL query templates
- [ ] MySQL query templates
- [ ] SQL Server query templates
- [ ] MongoDB query templates (nếu cần)

### Remaining Use Cases
- [ ] `analyze_query_regression.py`
- [ ] `detect_deadlock_pattern.py`
- [ ] `analyze_wait_stats.py`
- [ ] `analyze_io_pressure.py`
- [ ] `capacity_forecast.py`
- [ ] `validate_custom_sql.py`
- [ ] `compare_sp_blitz_vs_custom.py`
- [ ] `incident_triage.py`

### Testing
- [ ] Integration tests với test databases
- [ ] Test với multiple database types
- [ ] Test error scenarios

---

## Phase 3: Advanced Features (Week 3)

### RBAC (Optional)
- [ ] Tạo `middleware/rbac.py`
- [ ] Define permissions cho each use case
- [ ] Implement permission checks
- [ ] Integration với existing RBAC system

### Advanced Algorithms
- [ ] Query regression detection algorithm
- [ ] Capacity forecasting algorithm
- [ ] Deadlock pattern detection
- [ ] Incident triage logic

### Performance
- [ ] Connection pooling
- [ ] Query result caching (nếu cần)
- [ ] Async optimization

---

## Phase 4: Integration & Testing (Week 4)

### Router Integration
- [ ] Update `config/intent_registry.yaml` với DBA patterns
- [ ] Test routing đến DBA domain
- [ ] Verify intent extraction

### Use Case Registry
- [ ] Update `backend/domain/use_case_registry.py`
- [ ] Add DBA domain discovery
- [ ] Add intent descriptions

### Documentation
- [ ] API documentation
- [ ] Use case examples
- [ ] Database connection guide
- [ ] Troubleshooting guide

### E2E Testing
- [ ] Test full flow từ router → domain → response
- [ ] Test với real user queries
- [ ] Performance testing
- [ ] Load testing

---

## Phase 5: Production Readiness

### Security
- [ ] Security review
- [ ] SQL injection prevention
- [ ] Connection string encryption
- [ ] Audit logging

### Monitoring
- [ ] Add metrics cho DBA operations
- [ ] Add tracing
- [ ] Error alerting

### Deployment
- [ ] Environment configuration
- [ ] Docker setup (nếu cần)
- [ ] Migration scripts (nếu cần)

---

## Notes

- MCP Server: Cần quyết định sử dụng MCP server có sẵn hay build custom
- Connection Management: Cần design connection pooling strategy
- Testing: Cần setup test databases cho integration tests

