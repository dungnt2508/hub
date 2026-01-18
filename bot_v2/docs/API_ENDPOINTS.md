# API Endpoints Documentation

## Base URL

```
http://localhost:8386/api/v1
```

## Authentication

Tất cả endpoints yêu cầu `X-Tenant-ID` header:

```
X-Tenant-ID: <tenant-uuid>
```

## Bot API (Public)

### POST /bot/query

Process user query.

**Request:**
```json
{
  "query": "Giá sản phẩm ABC là bao nhiêu?",
  "channel_id": "optional-channel-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sản phẩm ABC có giá 1,000,000 VNĐ",
  "intent": "ask_price",
  "domain": "product",
  "answer": {
    "type": "product_price",
    "product": {
      "id": "...",
      "sku": "ABC",
      "name": "Product ABC"
    },
    "price": "1000000"
  },
  "disclaimers": ["Thông tin giá có thể thay đổi"]
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Xin lỗi, tôi không thể trả lời câu hỏi này.",
  "reason": "guardrail_violation"
}
```

### GET /bot/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Admin API

### Tenant Management

#### GET /admin/tenants

List all tenants.

**Query Parameters:**
- `limit` (int, default: 100)
- `offset` (int, default: 0)

**Response:**
```json
{
  "tenants": [
    {
      "id": "...",
      "name": "Tenant A",
      "status": "active",
      "plan": "premium",
      "settings_version": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /admin/tenants/{tenant_id}

Get tenant by ID.

**Response:**
```json
{
  "id": "...",
  "name": "Tenant A",
  "status": "active",
  "plan": "premium",
  "settings_version": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Channel Management

#### GET /admin/tenants/{tenant_id}/channels

List channels for tenant.

**Response:**
```json
{
  "channels": [
    {
      "id": "...",
      "tenant_id": "...",
      "type": "telegram",
      "enabled": true,
      "config_json": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Catalog Management

#### GET /admin/tenants/{tenant_id}/products

List products for tenant.

**Query Parameters:**
- `query` (string, optional): Search query
- `category` (string, optional): Filter by category
- `limit` (int, default: 50)
- `offset` (int, default: 0)

**Response:**
```json
{
  "products": [
    {
      "id": "...",
      "tenant_id": "...",
      "sku": "ABC",
      "slug": "product-abc",
      "name": "Product ABC",
      "category": "Electronics",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /admin/tenants/{tenant_id}/products/{product_id}

Get product details including attributes, use cases, and FAQs.

**Response:**
```json
{
  "product": {
    "id": "...",
    "sku": "ABC",
    "name": "Product ABC",
    ...
  },
  "attributes": [
    {
      "id": "...",
      "attributes_key": "price",
      "attributes_value": "1000000",
      "attributes_value_type": "number"
    }
  ],
  "use_cases": [
    {
      "id": "...",
      "type": "allowed",
      "description": "Suitable for home use"
    }
  ],
  "faqs": [
    {
      "id": "...",
      "scope": "product",
      "question": "How to use?",
      "answer": "Follow instructions..."
    }
  ]
}
```

### Intent Management

#### GET /admin/tenants/{tenant_id}/intents

List intents for tenant.

**Query Parameters:**
- `domain` (string, optional): Filter by domain

**Response:**
```json
{
  "intents": [
    {
      "id": "...",
      "tenant_id": "...",
      "name": "ask_price",
      "domain": "product",
      "priority": 10,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /admin/tenants/{tenant_id}/intents/{intent_id}

Get intent details including patterns, hints, and actions.

**Response:**
```json
{
  "intent": {
    "id": "...",
    "name": "ask_price",
    "domain": "product",
    ...
  },
  "patterns": [
    {
      "id": "...",
      "type": "keyword",
      "pattern": "giá",
      "weight": 1.0
    }
  ],
  "hints": [
    {
      "id": "...",
      "hint_text": "User is asking about product price"
    }
  ],
  "actions": [
    {
      "id": "...",
      "action_type": "query_db",
      "config_json": {
        "handler": "product_price"
      },
      "priority": 10
    }
  ]
}
```

### Migration Management

#### GET /admin/tenants/{tenant_id}/migrations

List migration jobs.

**Query Parameters:**
- `status` (string, optional): Filter by status (pending, processing, completed, failed)
- `limit` (int, default: 50)
- `offset` (int, default: 0)

**Response:**
```json
{
  "migrations": [
    {
      "id": "...",
      "tenant_id": "...",
      "source_type": "excel",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /admin/tenants/{tenant_id}/migrations

Create migration job.

**Request:**
```json
{
  "source_type": "excel"
}
```

**Response:**
```json
{
  "id": "...",
  "tenant_id": "...",
  "source_type": "excel",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Observability

#### GET /admin/tenants/{tenant_id}/logs

List conversation logs.

**Query Parameters:**
- `limit` (int, default: 100)
- `offset` (int, default: 0)

**Response:**
```json
{
  "logs": [
    {
      "id": "...",
      "tenant_id": "...",
      "channel_id": "...",
      "intent": "ask_price",
      "domain": "product",
      "success": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /admin/tenants/{tenant_id}/failed-queries

List failed queries.

**Query Parameters:**
- `limit` (int, default: 100)
- `offset` (int, default: 0)

**Response:**
```json
{
  "queries": [
    {
      "id": "...",
      "tenant_id": "...",
      "query": "What is the meaning of life?",
      "reason": "No intent matched",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## Error Responses

All endpoints may return standard HTTP error codes:

- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Missing or invalid tenant ID
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message"
}
```
