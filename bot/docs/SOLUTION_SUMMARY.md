# 📋 SUMMARY: Multi-Tenant Bot Service Authentication

**Ngày:** December 20, 2025  
**Người tư vấn:** AI Senior Backend Architect  
**Dự án:** Tích hợp Bot Service (@bot) ↔ Catalog (@catalog)  
**Status:** ✅ Design Hoàn Thành, Sẵn Sàng Triển Khai

---

## 🎯 Tình Huống

Bạn đang build một **multi-tenant bot service** mà có thể tích hợp vào **bất kỳ website nào** của khách hàng (ví dụ Catalog). Yêu cầu:

✅ Bảo mật biên giới tenant (không nhầm lẫn dữ liệu)  
✅ Không cần authenticate end-user  
✅ Hỗ trợ đa kênh (Web Embed, Telegram, Teams)  
✅ Mở rộng ngang (horizontal scale)  
✅ Rate limiting để chống abuse  
✅ PII protection (không lưu personal info mặc định)

---

## 💡 Giải Pháp: Architecture 3 Tầng

```
┌──────────────────────────────────────┐
│  CLIENT LAYER                        │
│  (Web Embed / Telegram / Teams)      │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  ADAPTER LAYER                       │
│  ├─ JWT Auth (Web)                   │
│  ├─ Bot Token (Telegram)             │
│  └─ Microsoft JWT (Teams)            │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  IDENTITY RESOLVER                   │
│  Extracts: tenant_id, channel,       │
│            user_key, context         │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  CORE BOT ENGINE                     │
│  (Multi-tenant, stateless)           │
│  - Conversation handling             │
│  - Intent routing                    │
│  - Response generation               │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  STATE LAYER                         │
│  - PostgreSQL (conversations)        │
│  - Redis (session cache, rate limit) │
└──────────────────────────────────────┘
```

**Đặc điểm:**
- 🔐 **Multi-tenant:** Mỗi request resolve `tenant_id` → hoàn toàn isolation
- 🔑 **No user auth:** Auth ở service-level, không ở user-level
- 🌐 **Channel-agnostic:** Core logic dùng chung, adapter khác nhau
- 📊 **Stateless:** Workers không state → scale ngang dễ
- ⚡ **Rate-limited:** Per (tenant, user_key) → chống abuse

---

## 🔐 3 Flows Authentication

### 1️⃣ Web Embed (Catalog Website)

```
User visits https://gsnake.com
    ↓
Script loads: <script src="bot.service/embed.js">
    ↓
embed.js → POST /embed/init
   {site_id: "catalog-001", origin: "https://gsnake.com"}
    ↓
Bot Service returns: JWT (3-5 phút expiry)
   {token: "eyJhbGc...", expiresIn: 300}
    ↓
Chat messages → Authorization: Bearer <JWT>
    ↓
Bot validates JWT + origin → process → respond
```

**Security:**
- ✅ JWT signed with tenant's secret
- ✅ Bind token to origin (prevent cross-site reuse)
- ✅ Short expiry (5 min auto-refresh)
- ✅ user_key server-generated, không từ user input

### 2️⃣ Telegram Bot

```
Telegram user → send message to bot
    ↓
Telegram API → webhook: POST /webhook/telegram
    {from.id: 987654321, text: "hello"}
    ↓
Bot Service → verify bot token → rate limit check
    ↓
Process message → Send response via Telegram API
```

**Security:**
- ✅ Bot token verification
- ✅ user_key = telegram_user_id (public, not PII)
- ✅ Rate limit per (tenant, user_id)

### 3️⃣ Microsoft Teams Bot

```
Teams user → send message to bot
    ↓
Teams Bot Framework → webhook: POST /webhook/teams
   Headers: Authorization: Bearer <Microsoft JWT>
    ↓
Bot Service → verify Microsoft JWT (JWKS endpoint)
    ↓
Extract aadObjectId → rate limit check → process
    ↓
Send response (Adaptive Card)
```

**Security:**
- ✅ Microsoft JWT signature verification
- ✅ user_key = aadObjectId (directory ID, not email)
- ✅ Rate limit per (tenant, user_id)

---

## 📊 Data Models

### Tenant (Multi-Tenant Configuration)
```
tenants
├─ id: UUID (primary key)
├─ name: string
├─ api_key: string (service-to-service auth)
├─ plan: "basic" | "professional" | "enterprise"
│
├─ web_embed_origins: string[] (whitelist)
├─ web_embed_jwt_secret: string (encrypted)
├─ web_embed_token_expiry: int (seconds)
│
├─ telegram_enabled: boolean
├─ telegram_bot_token: string (encrypted)
│
├─ teams_enabled: boolean
├─ teams_app_id: string
├─ teams_app_password: string (encrypted)
│
└─ rate_limits: {per_minute, per_hour, per_day}
```

### User Key (Non-PII Technical Identity)
```
user_keys
├─ id: UUID
├─ tenant_id: UUID → tenants
├─ channel: "web" | "telegram" | "teams"
├─ user_key: string (unique combo)
│  (hash for web, telegram_user_id, aadObjectId)
│
├─ user_id: string (optional, progressive identity)
├─ user_email: string (optional)
├─ user_display_name: string (optional)
│
└─ UNIQUE(tenant_id, channel, user_key)
```

### Conversation (Stateful History)
```
conversations
├─ id: UUID
├─ tenant_id: UUID
├─ channel: "web" | "telegram" | "teams"
├─ user_key: string
│
├─ message_count: int
├─ context_data: JSON
├─ UNIQUE(tenant_id, channel, user_key)
│
└─ conversation_messages
   ├─ id: UUID
   ├─ role: "user" | "assistant"
   ├─ content: text
   ├─ intent: string
   ├─ confidence: float
   └─ created_at: timestamp
```

---

## 🔑 Key Implementation Details

### JWT Token Structure (Web Embed)
```json
{
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "channel": "web",
  "user_key": "8f8a0b3c4d5e6f7a",        // hash(site_id + session_id)
  "origin": "https://gsnake.com",        // prevent cross-site
  "iat": 1702507200,
  "exp": 1702507500                      // 5 minutes later
}

Signature: HMAC-SHA256(header + payload, jwt_secret_per_tenant)
```

### Rate Limiting (Redis)
```
Key: rate_limit:<tenant_id>:<user_key>:<window>:<timestamp>
Windows: per_minute (60s), per_hour (3600s), per_day (86400s)

Example:
  rate_limit:tenant-001:user-123:minute:1702507200 = 15
  (15 requests in this 1-minute window)

If 15 > limit → reject with 429 Too Many Requests
```

### Request Context (Internal)
```python
context = {
    "tenant_id": "catalog-001",
    "channel": "web",
    "user_key": "8f8a0b3c4d5e6f7a",
    "auth_method": "jwt_web_embed",
    
    # Optional progressive identity
    "user_id": "user@example.com",
    "user_email": "user@example.com",
    
    # Metadata
    "platform": "web",
    "ip": "192.168.1.1",
    "origin": "https://gsnake.com"
}
```

---

## 📁 Triển Khai Files

### Tư Vấn & Docs (✅ Hoàn Thành)
- `bot/docs/MULTI_TENANT_AUTH_ARCHITECTURE.md` - Complete design (70KB)
- `catalog/docs/BOT_SERVICE_INTEGRATION_GUIDE.md` - Integration steps
- `bot/docs/IMPLEMENTATION_ROADMAP.md` - 6-phase roadmap

### Code Templates (✅ Hoàn Thành)
- `bot/backend/schemas/multi_tenant_types.py` - Type definitions + dataclasses
- `bot/backend/interface/middleware/multi_tenant_auth.py` - Auth middleware
- `bot/backend/shared/auth_config.py` - Auth config helpers
- `bot/backend/interface/handlers/embed_init_handler.py` - `/embed/init` API
- `bot/backend/infrastructure/rate_limiter.py` - Rate limiting service
- `bot/backend/interface/multi_tenant_bot_api.py` - Main API integration
- `bot/backend/scripts/test_multi_tenant_auth.py` - Test suite

---

## 🚀 6-Phase Implementation Plan

| Phase | Duration | Goal | Status |
|-------|----------|------|--------|
| **1** | Week 1 | Foundation (DB + Tenant CRUD + JWT) | Design ✅ |
| **2** | Week 1-2 | Web Embed (embed.js + /bot/message + Catalog integration) | Design ✅ |
| **3** | Week 2 | Telegram (Webhook + Bot API + Rate limit) | Design ✅ |
| **4** | Week 2-3 | Teams (Webhook + Microsoft JWT + Adaptive Cards) | Design ✅ |
| **5** | Week 3 | Security & Scaling (Audit + Monitoring + Load testing) | Design ✅ |
| **6** | Week 3+ | Integration & Launch (E2E testing + Live to Catalog users) | Design ✅ |

**Timeline:** 3-4 weeks (với team 2-3 engineers)

---

## ✅ Success Criteria

Sau khi triển khai:

- ✅ **Catalog users** có thể trò chuyện với bot trên website
- ✅ **Bot works on Telegram** (separate bot, same core)
- ✅ **Bot works in Teams** (via Bot Framework)
- ✅ **Tenant isolation** 100% (zero data leakage)
- ✅ **Rate limiting** effective (prevent abuse)
- ✅ **Performance** < 500ms response time (P99)
- ✅ **Security** - JWT secure, origin validated, PII optional
- ✅ **Scale** - horizontal scaling to N workers via load balancer

---

## 🛡️ Security Checklist

✅ JWT Token  
├─ Signed with tenant secret  
├─ Short expiry (5 min)  
├─ Bind to origin  
└─ No plaintext secrets in frontend

✅ Multi-Tenant Isolation  
├─ All queries filtered by tenant_id  
├─ User keys unique per (tenant, channel)  
├─ No cross-tenant data access  
└─ SQL injection prevention

✅ Rate Limiting  
├─ Per (tenant, user_key)  
├─ Redis-backed (atomic operations)  
├─ Prevents abuse  
└─ Graceful degradation

✅ Webhook Verification  
├─ Telegram: Bot token validation  
├─ Teams: Microsoft JWT verification  
└─ Origin validation (web embed)

✅ PII Protection  
├─ Use user_key by default (not PII)  
├─ Progressive identity (optional)  
├─ No PII in logs  
└─ Encryption at rest for sensitive fields

---

## 📞 Integration with Catalog

### Catalog Backend
1. Create tenant in bot service (API call)
2. Store config in Catalog DB
3. Add webhook endpoint (optional, for analytics)

### Catalog Frontend
1. Add embed script to layout
2. Bot appears automatically
3. No additional code needed

### Users
1. Chat with bot on catalog website
2. Seamless experience
3. No login required

---

## 🎓 Key Learnings

### Pattern: Multi-Tenant Architecture
- **Tenant isolation:** Strict filtering, no shared state
- **Channel agnostic:** Same core logic, different adapters
- **Stateless design:** Easy horizontal scaling
- **Progressive identity:** Optional PII enrichment

### Security Best Practices
- **JWT:** Secure token lifecycle, short expiry, binding
- **Rate limiting:** Prevent abuse, smooth user experience
- **Verification:** Multiple layers (signature, origin, whitelist)
- **Logging:** No PII, structured format, monitoring ready

### Scalability
- **Stateless workers:** N workers behind load balancer
- **Shared state:** PostgreSQL (conversations), Redis (cache, rate limits)
- **Async tasks:** Message queue for heavy operations
- **Monitoring:** Metrics, alerting, dashboards

---

## 📚 Files to Read

**Bắt đầu từ đây:**
1. `MULTI_TENANT_AUTH_ARCHITECTURE.md` (tư vấn chi tiết)
2. `BOT_SERVICE_INTEGRATION_GUIDE.md` (hướng dẫn Catalog)
3. `IMPLEMENTATION_ROADMAP.md` (kế hoạch triển khai)

**Chi tiết code:**
- `multi_tenant_types.py` - Data structures
- `multi_tenant_auth.py` - Authentication logic
- `multi_tenant_bot_api.py` - API endpoints
- `test_multi_tenant_auth.py` - Examples & tests

---

## 🚨 Common Pitfalls & Solutions

| Pitfall | Solution |
|---------|----------|
| **Leaking tenant data** | Strict WHERE tenant_id filters, code review |
| **Expired JWT → bad UX** | Auto-refresh before expiry (embed.js) |
| **Rate limit too strict** | Tune per plan, monitor actual usage |
| **Cross-site token reuse** | Origin binding in JWT + header validation |
| **PII in logs** | Use user_key, never log secrets |
| **Performance degradation** | DB indexing, caching, load testing |

---

## 💬 Q&A

**Q: Làm sao bảo đảm tenant isolation?**  
A: Mỗi request đều filtered by `tenant_id`. Không có shared state giữa tenants. Strict SQL queries.

**Q: Sao không dùng user login?**  
A: Bot service là 3rd-party service. Không biết identity của user. Dùng `user_key` (technical, không PII). Progressive identity optional.

**Q: Làm sao scale?**  
A: Stateless workers. Load balancer + N FastAPI workers. Shared Redis + PostgreSQL. Horizontal scaling.

**Q: JWT hết hạn rồi?**  
A: embed.js auto-refresh trước hết hạn. User không cảm thấy gì.

**Q: Rate limit để làm gì?**  
A: Prevent abuse (spam, DDoS). Per tenant + user. Smooth degradation.

---

## 🎯 Next Steps

1. **Đọc:** MULTI_TENANT_AUTH_ARCHITECTURE.md
2. **Hiểu:** Data models, authentication flows
3. **Review:** Implementation roadmap với team
4. **Start Phase 1:** Database + Tenant management
5. **Test:** Run test_multi_tenant_auth.py examples
6. **Integrate:** Phase 2 - Web embed to Catalog

---

**Status:** ✅ Tư vấn hoàn thành, sẵn sàng bắt đầu code.

**Duration:** 3-4 weeks (Phase 1-6)

**Team:** 2-3 backend engineers (Python/FastAPI)

**Deliverable:** Production-ready multi-tenant bot service, integrated into Catalog.

---

*Tài liệu được tạo: December 20, 2025*  
*Tư vấn bởi: AI Senior Backend Architect*  
*Dự án: Hub Bot Service*

