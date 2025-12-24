# Hướng dẫn Setup Project

## 1. Cài đặt Dependencies

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt packages
pip install -r requirements.txt
```

## 2. Cấu hình Environment

Copy file `.env.example` thành `.env` và điền các giá trị:

```bash
cp .env.example .env
```

Chỉnh sửa các biến môi trường trong `.env`:
- `EMBEDDING_THRESHOLD`: Ngưỡng confidence cho embedding classifier (mặc định: 0.8)
- `LLM_THRESHOLD`: Ngưỡng confidence cho LLM classifier (mặc định: 0.65)
- `ENABLE_LLM_FALLBACK`: Bật/tắt LLM fallback (mặc định: true)

## 3. Cấu hình Intent Registry

File `config/intent_registry.yaml` là single source of truth cho tất cả intents.

Thêm intent mới:
```yaml
- intent: your_new_intent
  domain: hr
  intent_type: OPERATION
  required_slots: [slot1, slot2]
  optional_slots: [slot3]
  source_allowed: [PATTERN, EMBEDDING]
  description: "Description of intent"
```

## 4. Chạy Tests

```bash
# Chạy tất cả tests
make test
# hoặc
pytest

# Chạy với coverage
pytest --cov=backend --cov-report=html
```

## 5. Development Workflow

### Code Style

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make type-check
```

### Thêm Domain Mới

1. Tạo thư mục domain: `backend/domain/your_domain/`
2. Tạo entry handler: `backend/domain/your_domain/entry_handler.py`
3. Tạo use cases: `backend/domain/your_domain/use_cases/`
4. Tạo entities: `backend/domain/your_domain/entities/`
5. Tạo ports: `backend/domain/your_domain/ports/`
6. Thêm intents vào `config/intent_registry.yaml`

### Thêm Router Step Mới

1. Tạo file step: `backend/router/steps/your_step.py`
2. Implement interface tương tự các step hiện có
3. Thêm vào `RouterOrchestrator` trong `backend/router/orchestrator.py`

## 6. Cấu trúc Code

### Router Layer
- `backend/router/orchestrator.py`: Main router orchestrator
- `backend/router/steps/`: Các routing steps (0-6)

### Domain Layer
- `backend/domain/{domain}/entry_handler.py`: Entry point
- `backend/domain/{domain}/use_cases/`: Business logic
- `backend/domain/{domain}/entities/`: Domain entities
- `backend/domain/{domain}/ports/`: Interfaces (repository, notification)

### Knowledge Layer
- `backend/knowledge/{domain}_knowledge_engine.py`: RAG pipeline

### Shared
- `backend/shared/config.py`: Configuration
- `backend/shared/logger.py`: Logging
- `backend/shared/exceptions.py`: Custom exceptions
- `backend/shared/intent_registry.py`: Intent registry loader

## 7. Testing

### Unit Tests
- Test từng component riêng lẻ
- Mock external dependencies
- Location: `tests/unit/`

### Integration Tests
- Test interaction giữa components
- Location: `tests/integration/`

### E2E Tests
- Test full flow từ request đến response
- Location: `tests/e2e/`

## 8. Deployment

### Pre-deployment Checklist

- [ ] Tất cả tests pass
- [ ] Code coverage >= 80%
- [ ] Linting pass
- [ ] Type checking pass
- [ ] Environment variables configured
- [ ] Intent registry updated
- [ ] Documentation updated

### Build

```bash
# Build package (nếu cần)
python setup.py sdist bdist_wheel
```

## 9. Troubleshooting

### Import Errors
- Đảm bảo đã cài đặt dependencies: `pip install -r requirements.txt`
- Kiểm tra PYTHONPATH nếu chạy từ thư mục khác

### Config Errors
- Kiểm tra file `.env` tồn tại và có đầy đủ biến
- Kiểm tra `config/intent_registry.yaml` có format đúng

### Test Failures
- Chạy `make clean` để xóa cache
- Kiểm tra test data và mocks

## 10. Next Steps

1. Implement các TODO trong code:
   - Session repository
   - Embedding model
   - LLM client
   - Domain repositories
   - Knowledge engine RAG pipeline

2. Thêm domains mới theo pattern HR domain

3. Thêm tests cho các components chưa có

4. Setup CI/CD pipeline

5. Setup monitoring và alerting

