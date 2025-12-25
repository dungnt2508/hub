# 📝 Hướng Dẫn Tạo Tenant và Site ID

Hướng dẫn chi tiết cách tạo tenant và site_id mapping cho bot service.

---

## 🎯 Tổng Quan

Khi tạo tenant, hệ thống sẽ tự động:
1. ✅ Tạo record trong `tenants` table
2. ✅ Tạo record trong `tenant_sites` table (mapping `site_id` → `tenant_id`)
3. ✅ Generate `api_key` và `jwt_secret` tự động
4. ✅ Validate `site_id` không trùng lặp

---

## 📋 Cách 1: Dùng Script Python (Khuyên dùng)

### Bước 1: Chạy script interactive

```bash
cd bot/backend
python scripts/create_tenant.py
```

Script sẽ hỏi các thông tin:
- Tên tenant
- Site ID
- Danh sách origins (mỗi origin một dòng)
- Plan (basic/professional/enterprise)
- Telegram/Teams enabled

### Bước 2: Hoặc dùng command line arguments

```bash
python scripts/create_tenant.py \
    --name "GSNAKE Catalog" \
    --site-id "catalog-001" \
    --origins "https://gsnake.com,https://www.gsnake.com,https://app.gsnake.com" \
    --plan "professional"
```

**Ví dụ đầy đủ:**
```bash
python scripts/create_tenant.py \
    --name "GSNAKE Marketplace" \
    --site-id "catalog-001" \
    --origins "https://gsnake.com,https://www.gsnake.com" \
    --plan "professional" \
    --telegram \
    --teams
```

**Output:**
```
✅ Tenant đã được tạo thành công!

📋 Thông tin tenant:
   Tenant ID: 550e8400-e29b-41d4-a716-446655440000
   Site ID: catalog-001
   Name: GSNAKE Catalog
   Plan: professional

🔑 Credentials:
   API Key: api_catalog-001_abc123xyz...
   JWT Secret: xyz789abc123...

⚠️  LƯU Ý: Lưu JWT Secret cẩn thận, không được tiết lộ!

📝 Sử dụng trong frontend:
   NEXT_PUBLIC_BOT_SITE_ID=catalog-001
   NEXT_PUBLIC_BOT_API_URL=http://localhost:8386
```

---

## 📋 Cách 2: Dùng API Endpoint

### Request

```bash
curl -X POST http://localhost:8386/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GSNAKE Catalog",
    "site_id": "catalog-001",
    "web_embed_origins": [
      "https://gsnake.com",
      "https://www.gsnake.com",
      "https://app.gsnake.com"
    ],
    "plan": "professional",
    "telegram_enabled": false,
    "teams_enabled": false
  }'
```

### Response

```json
{
  "success": true,
  "data": {
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "site_id": "catalog-001",
    "name": "GSNAKE Catalog",
    "api_key": "api_catalog-001_abc123xyz...",
    "jwt_secret": "xyz789abc123...",
    "plan": "professional",
    "created_at": "2025-01-20T10:30:00"
  }
}
```

---

## 📋 Cách 3: Dùng Python Code Trực Tiếp

```python
import asyncio
from bot.backend.domain.tenant.tenant_service import TenantService
from bot.backend.schemas.multi_tenant_types import PlanType
from bot.backend.infrastructure.database_client import database_client

async def create_tenant_example():
    async with database_client.pool.acquire() as conn:
        tenant_service = TenantService(conn)
        
        result = await tenant_service.create_tenant(
            name="GSNAKE Catalog",
            site_id="catalog-001",
            web_embed_origins=[
                "https://gsnake.com",
                "https://www.gsnake.com"
            ],
            plan=PlanType.PROFESSIONAL,
            telegram_enabled=False,
            teams_enabled=False,
        )
        
        print(result)

asyncio.run(create_tenant_example())
```

---

## 📋 Cách 4: Dùng SQL Trực Tiếp (Không khuyên dùng)

**⚠️ Lưu ý:** Cách này không khuyên dùng vì:
- Phải tự generate `api_key` và `jwt_secret`
- Dễ quên tạo record trong `tenant_sites`
- Không có validation

Nếu vẫn muốn dùng:

```sql
-- 1. Tạo tenant
INSERT INTO tenants (
    id, name, api_key, plan,
    web_embed_enabled, web_embed_origins, web_embed_jwt_secret,
    web_embed_token_expiry_seconds,
    telegram_enabled, teams_enabled,
    created_at, updated_at, is_active
) VALUES (
    gen_random_uuid(),
    'GSNAKE Catalog',
    'api_catalog-001_' || encode(gen_random_bytes(16), 'base64'),
    'professional',
    true,
    ARRAY['https://gsnake.com', 'https://www.gsnake.com'],
    encode(gen_random_bytes(32), 'base64'),  -- JWT secret (min 32 chars)
    300,  -- 5 minutes
    false,
    false,
    NOW(),
    NOW(),
    true
)
RETURNING id;

-- 2. Tạo site_id mapping (QUAN TRỌNG!)
INSERT INTO tenant_sites (id, tenant_id, site_id, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    '<tenant_id_from_step_1>',
    'catalog-001',
    true,
    NOW(),
    NOW()
);
```

---

## 🔍 Kiểm Tra Tenant Đã Tạo

### Query từ database:

```sql
-- Xem tenant
SELECT id, name, site_id, plan, is_active, created_at
FROM tenants
WHERE site_id = 'catalog-001';

-- Xem site_id mapping
SELECT ts.site_id, ts.tenant_id, t.name, ts.is_active
FROM tenant_sites ts
JOIN tenants t ON t.id = ts.tenant_id
WHERE ts.site_id = 'catalog-001';
```

### Dùng Python:

```python
from bot.backend.domain.tenant.tenant_service import TenantService
from bot.backend.infrastructure.database_client import database_client

async def check_tenant():
    async with database_client.pool.acquire() as conn:
        tenant_service = TenantService(conn)
        
        # Check by site_id
        tenant = await tenant_service.get_tenant_by_site_id("catalog-001")
        print(tenant)
        
        # Resolve tenant_id from site_id
        tenant_id = await tenant_service.resolve_tenant_id_from_site_id("catalog-001")
        print(f"Tenant ID: {tenant_id}")

asyncio.run(check_tenant())
```

---

## ⚙️ Cấu Hình Frontend

Sau khi tạo tenant, cấu hình trong frontend:

### Environment Variables:

```bash
# .env.local
NEXT_PUBLIC_BOT_API_URL=http://localhost:8386
NEXT_PUBLIC_BOT_SITE_ID=catalog-001
```

### Sử dụng trong code:

```tsx
// BotEmbed.tsx
const siteId = process.env.NEXT_PUBLIC_BOT_SITE_ID || 'catalog-001';
const apiUrl = process.env.NEXT_PUBLIC_BOT_API_URL || 'http://localhost:8386';
```

---

## 📊 Plan Types

| Plan | Rate Limit (per minute) | Rate Limit (per hour) | Rate Limit (per day) |
|------|-------------------------|----------------------|---------------------|
| `basic` | 20 | 1,000 | 10,000 |
| `professional` | 100 | 5,000 | 50,000 |
| `enterprise` | 1,000 | 100,000 | 1,000,000 |

---

## ✅ Validation Rules

1. **site_id:**
   - ✅ Bắt buộc, không được để trống
   - ✅ Phải unique (không trùng với tenant khác)
   - ✅ Format: `[a-z0-9-]+` (lowercase, numbers, hyphens)

2. **web_embed_origins:**
   - ✅ Bắt buộc, phải có ít nhất 1 origin
   - ✅ Format: `https://example.com` hoặc `http://localhost:3000`
   - ✅ Support wildcard: `*.example.com` (development only)

3. **plan:**
   - ✅ Phải là: `basic`, `professional`, hoặc `enterprise`

---

## 🐛 Troubleshooting

### Lỗi: "site_id already exists"

**Nguyên nhân:** Site ID đã được sử dụng bởi tenant khác.

**Giải pháp:**
- Dùng site_id khác
- Hoặc xóa/deactivate tenant cũ

### Lỗi: "Database connection not available"

**Nguyên nhân:** Database chưa được khởi tạo.

**Giải pháp:**
```python
# Đảm bảo database_client đã được init
from bot.backend.infrastructure.database_client import database_client
await database_client.initialize()
```

### Lỗi: "Tenant not found" khi dùng site_id

**Nguyên nhân:** 
- Migration chưa chạy
- Hoặc record trong `tenant_sites` chưa được tạo

**Giải pháp:**
```bash
# Chạy migration
cd bot/backend
alembic upgrade head

# Kiểm tra tenant_sites table
SELECT * FROM tenant_sites WHERE site_id = 'catalog-001';
```

---

## 📚 Tham Khảo

- [Priority 1 Fix Summary](../PRIORITY1_FIX_SUMMARY.md)
- [Technical Audit Report](../../integration_plan/TECHNICAL_AUDIT_REPORT.md)
- [Multi-Tenant Architecture](../docs/MULTI_TENANT_AUTH_ARCHITECTURE.md)

---

**Lưu ý:** Sau khi tạo tenant, lưu `api_key` và `jwt_secret` cẩn thận. Không commit vào git!

