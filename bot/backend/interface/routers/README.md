# 📁 API Routers - Tổ Chức Theo Chức Năng

Cấu trúc routers được tổ chức theo chức năng để dễ maintain và mở rộng.

---

## 🏗️ Cấu Trúc

```
interface/
├── api.py                    # Main FastAPI app, register routers
├── routers/                  # Organized by functionality
│   ├── __init__.py          # Export all routers
│   ├── health.py            # Health check & config
│   ├── web_embed.py         # Web embed endpoints
│   ├── admin.py             # Admin endpoints
│   └── webhooks.py          # Webhook endpoints
├── multi_tenant_bot_api.py  # Business logic classes
└── handlers/                # Request handlers
```

---

## 📋 Router Details

### 1. `health.py` - Health & Config
**Prefix:** None (root level)  
**Tags:** `["Health & Config"]`

**Endpoints:**
- `GET /health` - Health check (Redis, DB, Qdrant)
- `GET /api/v1/config` - Get router configuration

**Dependencies:** None

---

### 2. `web_embed.py` - Web Embed
**Prefix:** None (root level)  
**Tags:** `["Web Embed"]`

**Endpoints:**
- `POST /embed/init` - Initialize web embed session
- `POST /bot/message` - Send message to bot
- `GET /embed.js` - Serve embed JavaScript file

**Dependencies:**
- `MultiTenantBotAPI` (injected via `set_multi_tenant_api()`)

---

### 3. `admin.py` - Admin
**Prefix:** `/admin`  
**Tags:** `["Admin"]`

**Endpoints:**
- `POST /admin/tenants` - Create new tenant
- `POST /admin/tenants/{tenant_id}/knowledge/sync` - Sync knowledge base
- `GET /admin/tenants/{tenant_id}/knowledge/status` - Get sync status
- `DELETE /admin/tenants/{tenant_id}/knowledge` - Delete knowledge base

**Dependencies:**
- `MultiTenantBotAPI` (injected via `set_multi_tenant_api()`)
- `database_client` (global singleton)

---

### 4. `webhooks.py` - Webhooks
**Prefix:** None (root level)  
**Tags:** `["Webhooks"]`

**Endpoints:**
- `POST /webhook/telegram` - Telegram webhook
- `POST /webhook/teams` - Teams webhook
- `POST /webhooks/catalog/product-updated` - Catalog product webhook

**Dependencies:**
- `MultiTenantBotAPI` (injected via `set_multi_tenant_api()`)
- `database_client` (global singleton)

---

## 🔧 Dependency Injection Pattern

Routers sử dụng dependency injection để tránh circular imports:

```python
# In router file
_multi_tenant_api: MultiTenantBotAPI = None

def set_multi_tenant_api(api: MultiTenantBotAPI):
    """Set instance (called from main app)"""
    global _multi_tenant_api
    _multi_tenant_api = api

def get_multi_tenant_api() -> MultiTenantBotAPI:
    """Get instance"""
    if _multi_tenant_api is None:
        raise RuntimeError("Not initialized")
    return _multi_tenant_api
```

```python
# In api.py
multi_tenant_api = MultiTenantBotAPI()

from .routers.web_embed import set_multi_tenant_api as set_web_embed_api
set_web_embed_api(multi_tenant_api)

app.include_router(web_embed_router)
```

---

## ➕ Thêm Router Mới

### Bước 1: Tạo router file

```python
# routers/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/new-feature", tags=["New Feature"])

@router.get("/endpoint")
async def new_endpoint():
    return {"message": "Hello"}
```

### Bước 2: Export trong `__init__.py`

```python
# routers/__init__.py
from .new_feature import router as new_feature_router

__all__ = [
    # ... existing routers
    "new_feature_router",
]
```

### Bước 3: Register trong `api.py`

```python
# api.py
from .routers import new_feature_router

app.include_router(new_feature_router)
```

---

## ✅ Lợi Ích

1. **Tổ chức rõ ràng:** Mỗi router tập trung vào một chức năng
2. **Dễ mở rộng:** Thêm router mới không ảnh hưởng code cũ
3. **Dễ test:** Có thể test từng router độc lập
4. **Dễ maintain:** Code được chia nhỏ, dễ tìm và sửa
5. **FastAPI tags:** Tự động group trong Swagger UI

---

## 📚 Best Practices

1. **Một router = một chức năng:** Không mix nhiều chức năng trong một router
2. **Prefix rõ ràng:** Dùng prefix để group endpoints (ví dụ: `/admin`)
3. **Tags mô tả:** Dùng tags để group trong Swagger UI
4. **Dependency injection:** Không import trực tiếp từ `api.py`
5. **Error handling:** Handle errors trong router, return JSONResponse

---

## 🔍 Swagger UI

Sau khi refactor, Swagger UI sẽ tự động group endpoints theo tags:

- **Health & Config** - Health check, config
- **Web Embed** - Embed init, bot message, embed.js
- **Admin** - Tenant management, knowledge sync
- **Webhooks** - Telegram, Teams, Catalog webhooks

Truy cập: `http://localhost:8386/docs`

