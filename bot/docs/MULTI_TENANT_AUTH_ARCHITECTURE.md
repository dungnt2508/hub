# 🔐 Multi-Tenant Bot Service - Authentication Architecture

**Status:** Production Design  
**Last Updated:** December 2025  
**Target:** Bot Service (@bot) ↔ Catalog (@catalog) Integration

---

## 📋 Tóm Tắt Executive

Bot service là một nền tảng **multi-tenant, channel-agnostic** cần tích hợp:
- ✅ Website nhúng (Web Embed Script)
- ✅ Telegram Bot
- ✅ Microsoft Teams Bot

**Tiếp cận:** Không authenticate end-user, auth ở service-level. Mỗi request phải resolve `tenant_id`, `channel`, `user_key`.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
├─────────────┬──────────────┬──────────────┬────────────────┤
│ Web Embed   │ Telegram Bot │ Teams Bot    │ Custom Channel │
│ (Script)    │ (Webhook)    │ (Adaptive)   │                │
└──────┬──────┴────────┬─────┴──────────┬───┴────────────────┘
       │               │                │
       ├───────────────┼────────────────┤
       │ Adapter Layer │ (Channel-specific)
       │ - JWT Auth    │
       │ - Bot Token   │
       │ - API Key     │
       └───────────────┼────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │   IDENTITY RESOLVER            │
       │ ┌──────────────────────────────┤
       │ │ Extract: tenant_id           │
       │ │          channel             │
       │ │          user_key            │
       │ │          (optional) identity │
       │ └──────────────────────────────┤
       │                                │
       │ Output: Context {              │
       │   tenant_id,                   │
       │   channel,                     │
       │   user_key,                    │
       │   pii_optional                 │
       │ }                              │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │   CORE BOT ENGINE              │
       │ (Multi-tenant, stateless)      │
       │                                │
       │ - Conversation handler         │
       │ - Intent routing               │
       │ - Knowledge retrieval          │
       │ - Response generation          │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │   STATE LAYER                  │
       │ - PostgreSQL (conversations)   │
       │ - Redis (session cache)        │
       │ - Cache (tenant config)        │
       └────────────────────────────────┘
```

---

## 🔑 Authentication Flows

### 1️⃣ Web Embed Flow (Most Common)

#### Phase 1: Initialization
```
Website Visitor
     │
     ├─ Load <script src="bot.service.com/embed.js"></script>
     │
     ├─ Script sends: POST /embed/init
     │   ├─ site_id (known public)
     │   ├─ origin (from browser)
     │   └─ (Optional) user email/id for progressive identity
     │
     └─ Bot Service responds: JWT token (3-5 min expiry)
        ├─ Signed with internal secret
        ├─ Payload: {
        │   tenant_id,      // từ site_id
        │   channel: "web",
        │   user_key,       // hash(session_id) or random
        │   origin,         // bind to this origin
        │   iat, exp
        │ }
        └─ Response: { token, expiresIn, initiateConversation }
```

#### Phase 2: Chat Communication
```
Chat Message (from embed widget)
     │
     ├─ POST /bot/message
     │   ├─ Authorization: Bearer <JWT>
     │   ├─ Message: "..."
     │   └─ Session: { sessionId, history: [] }
     │
     └─ Bot Service:
        ├─ Validate JWT signature + origin
        ├─ Extract: tenant_id, channel, user_key
        ├─ Load conversation state (Redis)
        ├─ Process message
        ├─ Return response with new state
        └─ Update history in PostgreSQL
```

**Security Checks:**
- ✅ JWT valid signature
- ✅ JWT not expired
- ✅ Origin match (bind token to site_id + origin)
- ✅ Rate limit per (tenant, user_key)
- ✅ No plaintext secrets in embed script

---

### 2️⃣ Telegram Webhook Flow

```
Telegram User
     │
     ├─ Send message to bot
     │
     └─ Telegram API → Bot Service (Webhook)
        POST /webhook/telegram
        ├─ Headers: X-Telegram-Bot-Id: <bot_id>
        ├─ Body: {
        │   update_id,
        │   message: {
        │     chat: { id: telegram_user_id },
        │     from: { id: telegram_user_id },
        │     text: "..."
        │   }
        │ }
        │
        └─ Bot Service:
           ├─ Verify request from Telegram (hash check)
           ├─ Extract:
           │   tenant_id = from_bot_token(X-Telegram-Bot-Id)
           │   user_key = telegram_user_id (public, not PII by default)
           │   channel = "telegram"
           ├─ Load conversation state
           ├─ Process message
           ├─ Send response via Telegram API
           └─ Update conversation state
```

**Security Checks:**
- ✅ Telegram signature verification
- ✅ Rate limit per (tenant, telegram_user_id)
- ✅ Bot token stored securely server-side
- ✅ No token in logs/responses

---

### 3️⃣ Microsoft Teams Flow

```
Teams User
     │
     ├─ Send message to bot
     │
     └─ Teams Bot Framework → Bot Service
        POST /webhook/teams
        ├─ Headers:
        │   Authorization: Bearer <microsoft_jwt>
        │   (JWT signed by Microsoft)
        ├─ Body: {
        │   type: "message",
        │   conversation: { id, tenantId },
        │   from: { aadObjectId, userPrincipalName },
        │   text: "..."
        │ }
        │
        └─ Bot Service:
           ├─ Verify JWT from Microsoft (JWKS endpoint)
           ├─ Extract:
           │   tenant_id = conversation.tenantId
           │   user_key = aadObjectId (directory object id, not email)
           │   channel = "teams"
           ├─ Load conversation state
           ├─ Process message
           ├─ Send adaptive card response
           └─ Update conversation state
```

**Security Checks:**
- ✅ JWT signature validation (Microsoft JWKS)
- ✅ Verify issuer, audience, expiration
- ✅ Rate limit per (tenant, aadObjectId)
- ✅ Conversation isolation

---

## 📊 Data Models

### 1. Tenant
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    api_key VARCHAR UNIQUE NOT NULL,     -- service-to-service auth
    webhook_secret VARCHAR,              -- for webhook verification
    plan VARCHAR NOT NULL DEFAULT 'basic',
    rate_limit_per_hour INT DEFAULT 1000,
    rate_limit_per_day INT DEFAULT 10000,
    
    -- Web Embed
    web_embed_enabled BOOLEAN DEFAULT true,
    web_embed_origins TEXT[],           -- allowed origins
    web_embed_jwt_secret VARCHAR NOT NULL,
    
    -- Telegram
    telegram_enabled BOOLEAN DEFAULT false,
    telegram_bot_token VARCHAR ENCRYPTED,
    
    -- Teams
    teams_enabled BOOLEAN DEFAULT false,
    teams_app_id VARCHAR NOT NULL,
    teams_app_password VARCHAR ENCRYPTED,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. User Key (Technical Identity)
```sql
CREATE TABLE user_keys (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    channel VARCHAR NOT NULL,           -- 'web', 'telegram', 'teams'
    user_key VARCHAR NOT NULL,          -- hash(session_id) | telegram_user_id | aadObjectId
    
    -- Progressive identity (optional)
    user_id VARCHAR,                    -- user's actual identifier (email, external_id)
    user_email VARCHAR,
    user_display_name VARCHAR,
    
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(tenant_id, channel, user_key)
);
```

### 3. Conversation (Stateless Core, Stateful State)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    channel VARCHAR NOT NULL,
    user_key VARCHAR NOT NULL,
    
    -- History window
    message_count INT DEFAULT 0,
    last_message_at TIMESTAMP,
    
    -- Context
    context_data JSONB,                 -- {intent, domain, metadata}
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(tenant_id, channel, user_key)
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,              -- 'user', 'assistant'
    content TEXT NOT NULL,
    
    intent VARCHAR,
    confidence FLOAT,
    
    metadata JSONB,                     -- routing, model used, etc.
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. JWT Token (Web Embed)
```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "channel": "web",
  "user_key": "8f8a0b3c4d5e6f7a8b9c0d1e",  // hash(session_id)
  "origin": "https://customer.com",
  "iat": 1702507200,
  "exp": 1702507500                      // 5 minutes later
}

Signature: HMAC-SHA256(header + payload, JWT_SECRET_PER_TENANT)
```

---

## 🔐 API Specification

### 1. Web Embed: Initialize

**Request:**
```http
POST /embed/init
Content-Type: application/json
Origin: https://customer.com

{
  "site_id": "customer-001",
  "platform": "web",
  "user_data": {
    "email": "user@customer.com",     // optional
    "external_id": "emp-12345"        // optional
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 300,
    "botConfig": {
      "name": "PNJ HR Assistant",
      "avatar": "https://...",
      "theme": { "primaryColor": "#007bff" }
    }
  }
}
```

**Security:**
- ✅ Validate `site_id` exists & active
- ✅ Validate `Origin` header against tenant's `web_embed_origins`
- ✅ Create `user_key` = hash(session_id or random) ← not from user input
- ✅ Issue short-lived JWT (3-5 min)
- ✅ Rate limit per origin

---

### 2. Bot Message API

**Request:**
```http
POST /bot/message
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "Tôi còn bao nhiêu ngày phép?",
  "sessionId": "session-abc123",
  "attachments": []
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "messageId": "msg-001",
    "response": "Bạn còn 8 ngày phép...",
    "intent": "hr.leave_balance",
    "confidence": 0.95,
    "followUpActions": ["schedule_leave"]
  }
}
```

**Middleware:**
1. Extract + Validate JWT
2. Verify tenant active, not rate limited
3. Extract tenant_id, channel, user_key
4. Pass to handler

---

### 3. Telegram Webhook

**Request:**
```http
POST /webhook/telegram?token=<bot-public-token>
Content-Type: application/json
X-Telegram-Bot-Id: <bot-id-from-config>

{
  "update_id": 123456,
  "message": {
    "message_id": 1,
    "date": 1702507200,
    "chat": { "id": -123456789, "type": "private" },
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "John",
      "username": "john_doe"
    },
    "text": "Hello bot"
  }
}
```

**Verification:**
```python
def verify_telegram_request(body: bytes, bot_token: str) -> bool:
    """
    Telegram webhook verification không dùng signature.
    Verify theo: IP whitelist + Bot token đúng
    """
    # 1. Check IP whitelist (Telegram's IP ranges)
    # 2. Check bot token exists & matches config
    # 3. Validate JSON structure
    return True

# Hoặc: Tự implement SHA256 hash verification nếu cần
```

---

### 4. Teams Webhook

**Request:**
```http
POST /webhook/teams?token=<public-token>
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik...
Content-Type: application/json

{
  "type": "message",
  "id": "1702507200",
  "timestamp": "2025-12-20T12:00:00Z",
  "localTimestamp": "2025-12-20T12:00:00+07:00",
  "conversation": {
    "id": "19:abcd1234@thread.skype",
    "tenantId": "default",
    "isGroup": false
  },
  "from": {
    "id": "29:User123@xxxxxxxx.onmicrosoft.com",
    "aadObjectId": "00000000-0000-0000-0000-000000000001",
    "name": "John Doe",
    "userPrincipalName": "john.doe@company.com"
  },
  "text": "hello",
  "entities": []
}
```

**Verification:**
```python
def verify_teams_jwt(token: str) -> dict:
    """
    Verify JWT từ Microsoft Teams
    1. Fetch JWKs từ Microsoft endpoint
    2. Validate signature
    3. Check iss, aud, exp
    """
    # See: https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-authentication-components?tabs=csharp
```

---

## 🛡️ Security Checklist

| Threat | Mitigation | Status |
|--------|-----------|--------|
| **Cross-Origin Embed** | JWT bind origin + CORS validation | ✅ |
| **Token Hijacking** | Short-lived JWT (3-5 min), HTTPS only | ✅ |
| **Replay Attack** | Token + nonce, rate limit | ✅ |
| **Tenant Isolation** | All queries filtered by tenant_id | ✅ |
| **Unauthorized Access** | JWT validation, API key verification | ✅ |
| **Rate Limit Bypass** | Redis rate limit, per tenant + user | ✅ |
| **Cross-Tenant Data Leak** | Strict SQL WHERE clauses | ✅ |
| **Webhook Spoofing** | Request verification (IP, signature) | ✅ |
| **PII Exposure** | Use user_key by default, progressive identity | ✅ |
| **Secret Leakage** | Encrypt sensitive fields, no logs | ✅ |

---

## 📈 Scaling Strategy

### Stateless Workers
```
Load Balancer
    ├─ Worker 1: Fastify + Orchestrator
    ├─ Worker 2: Fastify + Orchestrator
    └─ Worker N: Fastify + Orchestrator

Shared State:
├─ PostgreSQL (conversations, history)
├─ Redis (rate limit, session cache, tenant config)
└─ External: OpenAI, n8n, Knowledge Base
```

### Rate Limiting Architecture
```python
# Redis key pattern: rate_limit:<tenant_id>:<user_key>:<window>
# Example: rate_limit:tenant-001:user-key-123:1702507200

def is_rate_limited(tenant_id, user_key, plan):
    key = f"rate_limit:{tenant_id}:{user_key}:{current_minute()}"
    count = redis.incr(key)
    
    if count == 1:
        redis.expire(key, 60)  # 1 minute window
    
    limit = PLAN_LIMITS[plan]
    return count > limit
```

### Horizontal Scaling
```
# Kafka topics (for async processing)
- bot.messages.incoming
- bot.messages.processed
- bot.conversations.created

# Worker pool (async tasks)
- Intent classification
- Knowledge retrieval
- Response generation
```

---

## 🔄 Integration with Catalog

### Catalog Initiates Bot Session
```
1. Catalog Admin creates Tenant in Bot Service
   POST /admin/tenants
   ├─ payload: {
   │   name: "GSNAKE Marketplace",
   │   site_id: "gsnake-001",
   │   web_embed_origins: ["https://gsnake.com"],
   │   telegram_enabled: false
   │ }
   └─ response: { tenant_id, api_key, jwt_secret }

2. Catalog Frontend gets /embed/init token
   POST /embed/init (from catalog.com)
   ├─ site_id: "gsnake-001"
   └─ response: { token, botConfig }

3. Catalog Frontend uses token for /bot/message
   POST /bot/message
   ├─ Authorization: Bearer <token>
   └─ Conversation with bot enabled
```

### Catalog Backend → Bot Service (Service-to-Service)
```python
# Catalog wants to update tenant config
headers = {
    "Authorization": f"Bearer {bot_api_key}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://bot.service/admin/tenants/update",
    headers=headers,
    json={"rate_limit_per_hour": 2000}
)
```

---

## 📝 Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create Tenant model + CRUD
- [ ] Create User Key model
- [ ] Implement JWT generation for Web Embed
- [ ] API: `/embed/init` endpoint

### Phase 2: Web Embed (Week 1-2)
- [ ] Embed.js script
- [ ] JWT validation middleware
- [ ] API: `/bot/message` endpoint
- [ ] Rate limiting logic
- [ ] Session state management (Redis)

### Phase 3: Telegram Integration (Week 2)
- [ ] Telegram adapter
- [ ] Webhook verification
- [ ] Telegram API integration
- [ ] Tests

### Phase 4: Teams Integration (Week 2-3)
- [ ] Teams adapter
- [ ] JWT verification (Microsoft JWKS)
- [ ] Adaptive cards response
- [ ] Tests

### Phase 5: Production (Week 3+)
- [ ] Monitoring + logging
- [ ] Rate limit analytics
- [ ] Disaster recovery
- [ ] Security audit

---

## ✅ Success Criteria

- ✅ Bot works on any website (via embed script)
- ✅ Telegram bot handles 1000s of users
- ✅ Teams bot integrates seamlessly
- ✅ Tenant data perfectly isolated
- ✅ Zero PII leakage by default
- ✅ Rate limits prevent abuse
- ✅ JWT doesn't expose secrets
- ✅ Scales horizontally to N workers
- ✅ Easy to add new channels

---

## 📚 References

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Microsoft Bot Framework](https://learn.microsoft.com/en-us/azure/bot-service/)
- [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Next Step:** Triển khai Phase 1 & 2

