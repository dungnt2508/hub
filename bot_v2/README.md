# Bot V2 - Multi-tenant Catalog Chatbot Service

Hệ thống chatbot đa-tenant cho catalog/sales-lite với các đặc điểm:

- **Deterministic behavior**: Hành vi xác định, không đoán mò
- **Auditable answers**: Câu trả lời có thể kiểm tra được
- **No hallucination**: Không tạo ra thông tin không có trong database
- **No free-form AI chat**: Không phải chatbot tự do, mà là hệ thống kiến thức có kiểm soát

## Kiến trúc hệ thống
docs/ARCHITECTURE.md 
## Runtime Request Flow

### Step-by-step Query Processing

1. **Guardrail Check**
   - Kiểm tra query có vi phạm forbidden topics không
   - Nếu vi phạm → trả về fallback_message

2. **Intent Routing**
   - Pattern matching để shortlist intents
   - LLM resolution (nếu có nhiều candidates và LLM được cấu hình)
   - Chọn intent từ database (KHÔNG tự tạo)

3. **Action Execution**
   - Lấy actions cho intent (theo priority)
   - Thực thi action đầu tiên (highest priority)
   - Action types: query_db, handoff, refuse, rag

4. **Domain Handler**
   - Nếu action_type = query_db:
     - Product info → CatalogService.get_product_info()
     - Suitability → CatalogService.check_suitability()
     - FAQ → CatalogService.get_faq_answer()
     - Comparison → CatalogService.compare_products()
   - CHỈ đọc từ database, KHÔNG suy luận

5. **Response Assembly**
   - Kết hợp answer từ domain handler
   - Thêm disclaimers nếu có
   - Format response

6. **Logging**
   - Log conversation vào conversation_logs
   - Log failed queries vào failed_queries

## Key API Endpoints

### Bot API (Public)

- `POST /api/v1/bot/query` - Process user query
- `GET /api/v1/bot/health` - Health check

### Admin API

- `GET /api/v1/admin/tenants` - List tenants
- `GET /api/v1/admin/tenants/{tenant_id}` - Get tenant
- `GET /api/v1/admin/tenants/{tenant_id}/channels` - List channels
- `GET /api/v1/admin/tenants/{tenant_id}/products` - List products
- `GET /api/v1/admin/tenants/{tenant_id}/products/{product_id}` - Get product
- `GET /api/v1/admin/tenants/{tenant_id}/intents` - List intents
- `GET /api/v1/admin/tenants/{tenant_id}/intents/{intent_id}` - Get intent
- `GET /api/v1/admin/tenants/{tenant_id}/migrations` - List migrations
- `POST /api/v1/admin/tenants/{tenant_id}/migrations` - Create migration
- `GET /api/v1/admin/tenants/{tenant_id}/logs` - List conversation logs
- `GET /api/v1/admin/tenants/{tenant_id}/failed-queries` - List failed queries

## Database Schema

Xem `backend/alembic_migrations/versions/db_note.txt` để biết chi tiết schema.

Các bảng chính:
- **Core**: tenants, tenant_secrets, channels
- **Catalog**: products, product_attributes, use_cases, faqs, comparisons, guardrails
- **Intent**: intents, intent_patterns, intent_hints, intent_actions
- **Migration**: migration_jobs, migration_versions
- **Observability**: conversation_logs, failed_queries

## Runtime Rules (NON-NEGOTIABLE)

1. **Routing**: User input MUST be routed via intents từ database
2. **Answering**: 
   - Product info ONLY from products + product_attributes
   - Suitability ONLY from use_cases
   - FAQ answers ONLY from faqs
   - Comparisons ONLY if explicitly defined in comparisons
3. **Forbidden**: No reasoning from specs, no guessing, no training on chat logs
4. **Guardrails**: Always check guardrails before answering
5. **CTA**: CTA triggered only via intent_actions, payload from config

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- (Optional) LLM API key for intent resolution

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database URL and settings

# Run migrations
alembic upgrade head

# Start server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bot_v2_db
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key
LLM_PROVIDER=openai  # optional
LLM_API_KEY=your-api-key  # optional
LLM_MODEL=gpt-4o-mini  # optional
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Frontend (Admin Dashboard)

Frontend structure sẽ được tạo trong `frontend/` directory với Next.js.

Các pages chính:
- `/admin/tenants` - Tenant management
- `/admin/tenants/[id]/channels` - Channel configuration
- `/admin/tenants/[id]/migrations` - Migration UI (upload, preview, approve)
- `/admin/tenants/[id]/catalog` - Catalog editor (products, attributes, use cases, FAQs)
- `/admin/tenants/[id]/intents` - Intent & routing editor
- `/admin/tenants/[id]/logs` - Conversation logs (read-only)
- `/admin/tenants/[id]/failed-queries` - Failed queries

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=backend --cov-report=html
```

## Deployment

Hệ thống được thiết kế để chạy ổn định trong nhiều năm mà không cần refactor lớn.

- Database migrations: Alembic
- Async operations: Background workers cho migration jobs
- Tenant isolation: Enforced ở mọi query
- Observability: Conversation logs và failed queries

## License

Proprietary
