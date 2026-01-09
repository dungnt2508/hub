# ⚡ PHASE 2 QUICK START GUIDE

## 🚀 Bắt đầu nhanh

### 1️⃣ Thiết lập cơ sở dữ liệu

```bash
# Chạy migrations
cd bot
alembic upgrade head

# Seed test data
python backend/scripts/seed_hr_data.py
```

### 2️⃣ Chạy Tests

```bash
# Tất cả HR tests
pytest backend/tests -k hr -v

# Unit tests
pytest backend/tests/unit/test_hr_*.py -v

# Integration tests
pytest backend/tests/integration/test_hr_domain.py -v

# Test một use case cụ thể
pytest backend/tests/unit/test_hr_use_cases.py::TestQueryLeaveBalanceUseCase -v
```

### 3️⃣ Chạy ứng dụng

```bash
# Development server
python -m uvicorn backend.interface.api:app --reload --port 8386

# Production
gunicorn backend.interface.api:app --workers 4 --port 8386
```

---

## 📚 Use Cases

### Query Leave Balance
**Lấy số ngày phép còn lại của nhân viên**

```bash
curl -X POST http://localhost:8386/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "hr",
    "intent": "query_leave_balance",
    "intent_type": "OPERATION",
    "slots": {},
    "user_context": {"user_id": "user-emp-001"},
    "trace_id": "123",
    "session_id": "session-123"
  }'
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_balance": 20,
    "employee_name": "John Employee",
    "user_id": "user-emp-001"
  },
  "message": "Bạn còn 20 ngày phép"
}
```

---

### Create Leave Request
**Tạo đơn xin phép**

```bash
curl -X POST http://localhost:8386/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "hr",
    "intent": "create_leave_request",
    "intent_type": "OPERATION",
    "slots": {
      "start_date": "2025-02-05",
      "end_date": "2025-02-07",
      "reason": "Vacation"
    },
    "user_context": {"user_id": "user-emp-001"},
    "trace_id": "123",
    "session_id": "session-123"
  }'
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2025-02-05",
    "end_date": "2025-02-07",
    "status": "pending"
  },
  "message": "Đã tạo đơn xin nghỉ phép thành công"
}
```

---

### Query Leave Requests
**Lấy danh sách đơn xin phép** ⭐ NEW

```bash
curl -X POST http://localhost:8386/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "hr",
    "intent": "query_leave_requests",
    "intent_type": "OPERATION",
    "slots": {
      "status": "pending",
      "limit": 10,
      "offset": 0
    },
    "user_context": {"user_id": "user-emp-001"},
    "trace_id": "123",
    "session_id": "session-123"
  }'
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_requests": [
      {
        "leave_request_id": "550e8400-e29b-41d4-a716-446655440000",
        "start_date": "2025-02-05",
        "end_date": "2025-02-07",
        "reason": "Vacation",
        "status": "pending",
        "created_at": "2026-01-08T10:30:00"
      }
    ],
    "total_count": 1,
    "limit": 10,
    "offset": 0
  },
  "message": "Tìm thấy 1 đơn xin nghỉ phép"
}
```

---

### Approve Leave
**Duyệt đơn xin phép**

```bash
curl -X POST http://localhost:8386/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "hr",
    "intent": "approve_leave",
    "intent_type": "OPERATION",
    "slots": {
      "leave_request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "user_context": {"user_id": "user-mgr-001"},
    "trace_id": "123",
    "session_id": "session-123"
  }'
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "approved"
  },
  "message": "Đã duyệt đơn xin nghỉ phép thành công"
}
```

---

### Reject Leave
**Từ chối đơn xin phép** ⭐ NEW

```bash
curl -X POST http://localhost:8386/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "hr",
    "intent": "reject_leave",
    "intent_type": "OPERATION",
    "slots": {
      "leave_request_id": "550e8400-e29b-41d4-a716-446655440000",
      "rejection_reason": "Conflict with project deadline"
    },
    "user_context": {"user_id": "user-mgr-001"},
    "trace_id": "123",
    "session_id": "session-123"
  }'
```

**Response:**
```json
{
  "status": "SUCCESS",
  "data": {
    "leave_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "rejected",
    "rejection_reason": "Conflict with project deadline"
  },
  "message": "Đã từ chối đơn xin nghỉ phép"
}
```

---

## 🔑 Test Users

### Employee
```
user_id: user-emp-001
name: John Employee
role: employee
department: Engineering
```

### Manager
```
user_id: user-mgr-001
name: Jane Manager
role: manager
department: Engineering
```

### Admin
```
user_id: user-admin-001
name: Admin
role: admin
department: Admin
```

---

## 📂 Project Structure

```
bot/
├── backend/
│   ├── domain/
│   │   └── hr/
│   │       ├── adapters/
│   │       │   └── postgresql_repository.py ✅ ENHANCED
│   │       ├── middleware/
│   │       │   └── rbac.py ✅ ENHANCED
│   │       ├── use_cases/
│   │       │   ├── query_leave_balance.py
│   │       │   ├── create_leave_request.py
│   │       │   ├── approve_leave.py
│   │       │   ├── query_leave_requests.py ⭐ NEW
│   │       │   └── reject_leave.py ⭐ NEW
│   │       └── entry_handler.py ✅ UPDATED
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_hr_use_cases.py ⭐ NEW
│   │   │   └── test_hr_repository.py ⭐ NEW
│   │   └── integration/
│   │       └── test_hr_domain.py ✅ UPDATED
│   └── scripts/
│       └── seed_hr_data.py ⭐ NEW
├── docs/
│   └── PHASE2_IMPLEMENTATION.md ✅ NEW
├── PHASE2_SUMMARY.txt ✅ NEW
├── PHASE2_CHECKLIST.md ✅ NEW
└── PHASE2_QUICKSTART.md (this file)
```

---

## 🐛 Troubleshooting

### Problem: Database connection failed
**Solution:**
```bash
# Check if PostgreSQL is running
psql -U bot_user -d bot_db -h 127.0.0.1

# Or use Docker
docker-compose up -d

# Run migrations
alembic upgrade head
```

### Problem: Tests failing
**Solution:**
```bash
# Clean pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Run specific test
pytest bot/backend/tests/unit/test_hr_use_cases.py::TestQueryLeaveBalanceUseCase::test_execute_success -vv
```

### Problem: Import errors
**Solution:**
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd bot && pytest backend/tests -k hr -v
```

---

## 📊 Performance Tips

### 1. Database Indexing
```sql
-- Check existing indexes
SELECT * FROM pg_indexes WHERE tablename='employees';
SELECT * FROM pg_indexes WHERE tablename='leave_requests';

-- Add index if needed
CREATE INDEX idx_employees_user_id ON employees(user_id);
CREATE INDEX idx_leave_requests_employee_id ON leave_requests(employee_id);
```

### 2. Query Optimization
- Use EXPLAIN ANALYZE for slow queries
- Check connection pool settings
- Use pagination for large result sets

### 3. Caching
- Session cache TTL: 5 minutes
- Embedding cache TTL: 24 hours

---

## 🔒 Security Checklist

- [x] RBAC enforced on all operations
- [x] Input validation on all endpoints
- [x] SQL injection prevention (parameterized queries)
- [x] Authorization errors logged
- [x] Sensitive data not in logs

---

## 📖 Documentation

- [x] `docs/PHASE2_IMPLEMENTATION.md` - Full technical documentation
- [x] `PHASE2_SUMMARY.txt` - Implementation summary
- [x] `PHASE2_CHECKLIST.md` - Verification checklist
- [x] Code comments and docstrings

---

## 🎓 Key Learnings

1. **Repository Pattern** - Data access abstraction
2. **Use Cases** - Business logic isolation
3. **RBAC** - Role-based permission enforcement
4. **Testing** - Unit + Integration test strategies
5. **Error Handling** - Proper exception hierarchy

---

## 🚀 Next Steps

1. **Deploy to staging**: Test with real data
2. **Performance testing**: Load testing with 100+ concurrent users
3. **Security audit**: Penetration testing
4. **Phase 3 - Knowledge Engine**: RAG pipeline implementation

---

## ❓ FAQ

**Q: How do I add a new use case?**
A: Create a new file in `use_cases/`, inherit from `BaseUseCase`, implement `execute()` method, and register in `entry_handler.py`.

**Q: How do I modify RBAC rules?**
A: Edit `middleware/rbac.py` in the `PermissionChecker` class.

**Q: How do I test a specific scenario?**
A: Write a test case in `tests/unit/` or `tests/integration/` and run with pytest.

**Q: How do I debug a failing test?**
A: Run pytest with `-vv` flag and use `--pdb` for interactive debugging.

---

## 📞 Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review test examples in `tests/`
3. Check error messages in logs

---

**Ready to start?** 🎉

```bash
# Start the server
python -m uvicorn backend.interface.api:app --reload

# Run all tests
pytest backend/tests -k hr -v

# Try an API call
curl -X POST http://localhost:8386/domain \
  -d '{"domain":"hr", "intent":"query_leave_balance", ...}'
```

**Good luck! 🚀**

