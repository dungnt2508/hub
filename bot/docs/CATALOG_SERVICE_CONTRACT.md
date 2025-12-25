# Catalog Service Contract

**Status:** Production Contract  
**Last Updated:** 2025-12-20  
**Parties:** Bot Service ↔ Catalog Service

---

## Tổng Quan

Contract giữa Bot Service và Catalog Service để đảm bảo tenant isolation và data security.

---

## 🔐 Authentication & Authorization

### Bot Service → Catalog Service

**Authentication:**
- Bot Service sử dụng API key hoặc service account để authenticate với Catalog Service
- API key được lưu trong Bot Service config (environment variable hoặc secret store)

**Authorization:**
- Bot Service chỉ có thể access data của tenants mà nó được authorize
- Catalog Service validate API key và check permissions

---

## 📋 API Contract

### 1. GET /api/products

**Request:**
```http
GET /api/products?tenant_id={tenant_id}&status=published&review_status=approved&limit=100&offset=0
Authorization: Bearer {api_key}
```

**Required Parameters:**
- `tenant_id` (REQUIRED): Tenant UUID - Catalog Service MUST filter products by this tenant_id

**Optional Parameters:**
- `status`: Product status filter (default: "published")
- `review_status`: Review status filter (default: "approved")
- `limit`: Pagination limit (default: 100)
- `offset`: Pagination offset (default: 0)
- `tags`: Filter by tags
- `type`: Filter by product type
- `search`: Search query

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "product-uuid",
        "sellerId": "seller-uuid",
        "title": "Product Title",
        "description": "Product description",
        "tenantId": "tenant-uuid",  // MUST match request tenant_id
        ...
      }
    ],
    "total": 100,
    "limit": 100,
    "offset": 0
  }
}
```

**Security Requirements:**
- ✅ Catalog Service MUST validate `tenant_id` parameter
- ✅ Catalog Service MUST filter products by `tenant_id` (WHERE clause)
- ✅ Catalog Service MUST reject nếu `tenant_id` missing
- ✅ Catalog Service MUST NOT return products từ tenants khác
- ✅ Catalog Service MUST verify API key authentication

**Error Responses:**
- `400 Bad Request`: Missing or invalid `tenant_id`
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: API key không có permission cho tenant này

---

### 2. GET /api/products/{product_id}

**Request:**
```http
GET /api/products/{product_id}?tenant_id={tenant_id}
Authorization: Bearer {api_key}
```

**Required Parameters:**
- `tenant_id` (REQUIRED): Tenant UUID - Catalog Service MUST verify product belongs to this tenant

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "product-uuid",
    "sellerId": "seller-uuid",
    "title": "Product Title",
    "tenantId": "tenant-uuid",  // MUST match request tenant_id
    ...
  }
}
```

**Security Requirements:**
- ✅ Catalog Service MUST validate `tenant_id` parameter
- ✅ Catalog Service MUST verify product belongs to requested tenant
- ✅ Catalog Service MUST reject nếu product không thuộc tenant
- ✅ Catalog Service MUST return 404 nếu product không tồn tại hoặc không thuộc tenant

**Error Responses:**
- `400 Bad Request`: Missing or invalid `tenant_id`
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Product không thuộc tenant này
- `404 Not Found`: Product không tồn tại

---

## 🛡️ Tenant Isolation Rules

### Rule 1: Tenant ID is REQUIRED
- Bot Service MUST send `tenant_id` trong mọi request
- Catalog Service MUST reject requests không có `tenant_id`

### Rule 2: Tenant ID Validation
- Catalog Service MUST validate `tenant_id` exists và active
- Catalog Service MUST reject invalid `tenant_id`

### Rule 3: Data Filtering
- Catalog Service MUST filter ALL queries by `tenant_id`
- Catalog Service MUST NOT return data từ tenants khác
- Catalog Service MUST verify product ownership trước khi return

### Rule 4: API Key Authorization
- Catalog Service MUST verify API key có permission cho requested tenant
- Catalog Service MUST reject nếu API key không authorized

---

## 📊 Data Model

### Product Schema (Catalog Service)

```typescript
interface Product {
  id: string;              // Product UUID
  tenantId: string;        // Tenant UUID (REQUIRED for multi-tenant)
  sellerId: string;        // Seller UUID
  title: string;
  description: string;
  status: "published" | "draft" | "archived";
  reviewStatus: "approved" | "pending" | "rejected";
  // ... other fields
}
```

**Critical Field:**
- `tenantId`: MUST be present và match request `tenant_id`

---

## 🔄 Integration Flow

### Bot Service Sync Flow

```
1. Bot Service: GET /api/products?tenant_id={tenant_id}
   └─ Catalog Service: Validate tenant_id, filter products, return

2. Bot Service: Process products, sync to vector store
   └─ Each product MUST have tenantId matching request tenant_id

3. Bot Service: GET /api/products/{product_id}?tenant_id={tenant_id}
   └─ Catalog Service: Verify product belongs to tenant, return
```

### Webhook Flow (Catalog → Bot)

```
1. Catalog Service: POST /webhooks/catalog/product-updated
   Body: {
     "tenant_id": "tenant-uuid",
     "event": "created|updated|deleted",
     "product_id": "product-uuid"
   }

2. Bot Service: Validate tenant_id, process event
   └─ Fetch product với tenant_id verification
```

---

## ✅ Validation Checklist

### Bot Service Responsibilities:
- [x] Always send `tenant_id` trong mọi catalog API request
- [x] Validate `tenant_id` trước khi gọi catalog API
- [x] Handle errors từ catalog service (400, 401, 403, 404)
- [x] Log catalog API calls với tenant_id

### Catalog Service Responsibilities:
- [ ] Validate `tenant_id` parameter (required, non-empty, valid UUID)
- [ ] Filter products by `tenant_id` (SQL WHERE clause)
- [ ] Verify product ownership trước khi return
- [ ] Reject requests without `tenant_id`
- [ ] Return 403 nếu product không thuộc requested tenant
- [ ] Log all requests với tenant_id

---

## 🚨 Security Violations

### Critical Violations:
1. **Missing tenant_id**: Catalog Service returns ALL products → DATA LEAK
2. **No filtering**: Catalog Service không filter by tenant_id → DATA LEAK
3. **Product ownership bypass**: Catalog Service return product từ tenant khác → DATA LEAK

### Detection:
- Bot Service: Monitor catalog API responses - verify all products have matching tenantId
- Catalog Service: Audit logs - track all requests với tenant_id
- Integration tests: Verify tenant isolation

---

## 📝 Implementation Notes

### Bot Service (Current Implementation):
- ✅ `CatalogClient.get_products()` - tenant_id REQUIRED
- ✅ `CatalogClient.get_all_products()` - tenant_id REQUIRED
- ✅ `CatalogClient.get_product()` - tenant_id REQUIRED
- ✅ All methods validate tenant_id không None/empty

### Catalog Service (Expected Implementation):
- ⚠️ Catalog Service MUST implement tenant_id filtering
- ⚠️ Catalog Service MUST validate tenant_id parameter
- ⚠️ Catalog Service MUST verify product ownership

---

## 🔗 Related Documents

- `bot/docs/ARCHITECTURE_REVIEW_AND_PHASE_PLAN.md` - Architecture review
- `bot/backend/infrastructure/catalog_client.py` - Bot Service implementation
- `catalog/docs/BOT_SERVICE_INTEGRATION_GUIDE.md` - Catalog integration guide

---

**Contract Version:** 1.0  
**Effective Date:** 2025-12-20  
**Review Date:** 2026-01-20

