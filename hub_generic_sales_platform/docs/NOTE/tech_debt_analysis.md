# PHÂN TÍCH TECH DEBT - BOT V4

**Ngày phân tích:** 25/01/2026  
**Phạm vi:** Toàn bộ codebase

---

## 📋 TÓM TẮT

Tổng hợp các vấn đề tech debt được phát hiện trong codebase, phân loại theo mức độ ưu tiên và tác động.

---

## 🔴 CRITICAL (Cần sửa ngay)

### 1. **Error Handling Quá Rộng (Broad Exception Catching)**

**Vị trí:**
- `app/core/shared/llm_service.py:49, 71, 117`
- `app/interfaces/api/routes.py:45`
- `app/application/services/integration_handler.py:64`
- `app/application/services/slot_extractor.py:77`
- `app/application/services/guardrail_checker.py:97`

**Vấn đề:**
```python
except Exception:  # Quá rộng, che giấu lỗi thực sự
    return []
```

**Tác động:**
- Che giấu lỗi thực sự, khó debug
- Không phân biệt được lỗi network, validation, hay business logic
- Mất thông tin quan trọng khi troubleshooting

**Giải pháp:**
- Catch specific exceptions (OpenAIError, TimeoutError, etc.)
- Log chi tiết lỗi trước khi return
- Sử dụng custom exceptions từ `exceptions.py`

**Priority:** 🔴 HIGH

---

### 2. **Debug Code Trong Production**

**Vị trí:**
- `app/main.py:10` - `print(settings.database_url)`

**Vấn đề:**
```python
print(settings.database_url)  # In ra credentials trong production
```

**Tác động:**
- Security risk: Log credentials ra console
- Không sử dụng logging system

**Giải pháp:**
- Xóa hoặc chuyển sang logger với level DEBUG
- Chỉ log khi DEBUG=True

**Priority:** 🔴 HIGH

---

### 3. **Hardcoded Application Name Trong Database Config**

**Vị trí:**
- `app/infrastructure/database/engine.py:51`

**Vấn đề:**
```python
"application_name": "hr_assistant",  # Sai tên ứng dụng
```

**Tác động:**
- Monitoring/observability không chính xác
- Khó trace requests trong production

**Giải pháp:**
- Dùng `settings.app_name` thay vì hardcode

**Priority:** 🟡 MEDIUM

---

## 🟡 MEDIUM (Nên sửa sớm)

### 4. **Missing Type Hints**

**Vị trí:**
- Nhiều methods trong repositories thiếu return type hints
- `app/application/orchestrators/agent_orchestrator.py` - một số methods

**Vấn đề:**
- Khó maintain và refactor
- IDE không hỗ trợ tốt
- Type checking không hoạt động

**Giải pháp:**
- Thêm type hints cho tất cả public methods
- Sử dụng `mypy` để check

**Priority:** 🟡 MEDIUM

---

### 5. **Silent Failures Trong LLM Service**

**Vị trí:**
- `app/core/shared/llm_service.py:49, 71`

**Vấn đề:**
```python
except Exception:
    return []  # Silent failure, không log gì
```

**Tác động:**
- Không biết khi nào LLM service fail
- Khó monitor và alert

**Giải pháp:**
- Log error với logger
- Return None thay vì empty list để phân biệt "no result" vs "error"
- Raise custom exception nếu cần

**Priority:** 🟡 MEDIUM

---

### 6. **Missing Input Validation**

**Vị trí:**
- `app/interfaces/api/routes.py:23-46` - ChatMessageRequest
- `app/application/orchestrators/hybrid_orchestrator.py:34` - handle_message

**Vấn đề:**
- Không validate message length
- Không validate bot_id format
- Không sanitize input

**Tác động:**
- Security risk (injection, DoS)
- Data quality issues

**Giải pháp:**
- Thêm Pydantic validators
- Validate message length (max 5000 chars)
- Validate UUID format cho IDs

**Priority:** 🟡 MEDIUM

---

### 7. **Inconsistent Error Responses**

**Vị trí:**
- `app/interfaces/api/routes.py:45` - Generic HTTPException
- Không sử dụng custom exceptions từ `exceptions.py`

**Vấn đề:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Generic
```

**Tác động:**
- Client không biết loại lỗi
- Khó handle errors ở frontend

**Giải pháp:**
- Sử dụng custom exceptions
- Map exceptions sang HTTP status codes
- Return structured error response

**Priority:** 🟡 MEDIUM

---

### 8. **Missing Transaction Management**

**Vị trí:**
- `app/infrastructure/database/base.py` - BaseRepository methods

**Vấn đề:**
- Mỗi method tự commit (`await self.db.commit()`)
- Không support nested transactions
- Không có rollback strategy rõ ràng

**Tác động:**
- Khó implement complex workflows
- Data inconsistency risk

**Giải pháp:**
- Tách commit ra khỏi repository methods
- Sử dụng transaction context manager
- Implement Unit of Work pattern

**Priority:** 🟡 MEDIUM

---

## 🟢 LOW (Có thể để sau)

### 9. **Code Duplication**

**Vị trí:**
- Vector similarity logic trong `cache.py` và `faq.py`
- Mock setup trong tests

**Vấn đề:**
- Duplicate code cho SQLite fallback
- Khó maintain khi thay đổi logic

**Giải pháp:**
- Extract thành utility function
- Tạo VectorSearchService

**Priority:** 🟢 LOW

---

### 10. **Missing Docstrings**

**Vị trí:**
- Một số methods trong services thiếu docstrings
- Complex logic không có comments

**Vấn đề:**
- Khó hiểu intent của code
- Onboarding khó khăn

**Giải pháp:**
- Thêm docstrings cho public methods
- Follow Google/NumPy style

**Priority:** 🟢 LOW

---

### 11. **Unused Imports**

**Vị trí:**
- `app/core/shared/llm_service.py:4` - `import os` (không dùng)
- Một số files khác

**Vấn đề:**
- Code clutter
- Confusion về dependencies

**Giải pháp:**
- Sử dụng linter (ruff, flake8) để detect
- Auto-remove unused imports

**Priority:** 🟢 LOW

---

### 12. **Missing Tests**

**Vị trí:**
- `app/application/services/` - nhiều services chưa có tests
- `app/interfaces/api/routes.py` - API endpoints chưa test
- Integration tests cho error scenarios

**Vấn đề:**
- Không đảm bảo quality
- Khó refactor an toàn

**Giải pháp:**
- Thêm unit tests cho services
- Thêm integration tests cho API
- Test error scenarios

**Priority:** 🟢 LOW

---

### 13. **Hardcoded Values**

**Vị trí:**
- `app/application/orchestrators/agent_orchestrator.py:78` - `max_turns = 3`
- `app/application/orchestrators/hybrid_orchestrator.py:98` - `threshold=0.9`

**Vấn đề:**
- Khó config trong production
- Không thể tune performance

**Giải pháp:**
- Move vào settings
- Cho phép override qua env vars

**Priority:** 🟢 LOW

---

### 14. **Missing Logging Context**

**Vị trí:**
- Nhiều nơi không log với context (tenant_id, session_id, etc.)

**Vấn đề:**
- Khó trace requests trong production
- Debug khó khăn

**Giải pháp:**
- Sử dụng structured logging với context
- Pass context qua function calls

**Priority:** 🟢 LOW

---

## 📊 TỔNG KẾT

| Mức độ | Số lượng | Tác động |
|--------|----------|----------|
| 🔴 Critical | 3 | Security, Reliability |
| 🟡 Medium | 5 | Maintainability, Quality |
| 🟢 Low | 6 | Code quality, DX |

---

## 🎯 KHUYẾN NGHỊ ƯU TIÊN

### Sprint tiếp theo nên fix:

1. **Error Handling** (Critical)
   - Refactor exception handling trong LLM service
   - Implement proper error logging
   - Sử dụng custom exceptions

2. **Security** (Critical)
   - Xóa debug prints
   - Thêm input validation
   - Fix hardcoded credentials

3. **Type Safety** (Medium)
   - Thêm type hints
   - Setup mypy checking

4. **Testing** (Medium)
   - Thêm tests cho services
   - Test error scenarios

---

## 📝 NOTES

- Codebase nhìn chung có structure tốt (Clean Architecture)
- Async implementation đúng cách
- Exception system đã có nhưng chưa được sử dụng đầy đủ
- Cần improve observability và error handling

---

**Người phân tích:** AI Assistant  
**Cập nhật:** 25/01/2026