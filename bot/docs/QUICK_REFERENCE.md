# 🎯 Quick Reference - Multi-Tenant Bot Service

**Print this & keep handy** 📌

---

## 🔐 Authentication Flows at a Glance

### Web Embed (Catalog Website)
```
1. Browser: POST /embed/init
   └─ Returns: JWT token (5 min)

2. Chat: Authorization: Bearer <JWT>
   └─ Validates: JWT signature + origin

3. Rate limit: per (tenant_id, user_key)
```

### Telegram Bot
```
1. Telegram API: POST /webhook/telegram
   └─ Verify: bot token

2. Extract: telegram_user_id as user_key

3. Rate limit: per (tenant_id, user_id)
```

### Teams Bot
```
1. Teams API: POST /webhook/teams
   └─ Verify: Microsoft JWT signature

2. Extract: aadObjectId as user_key

3. Rate limit: per (tenant_id, user_id)
```

---

## 📊 Key Concepts

| Term | Meaning |
|------|---------|
| **tenant_id** | Customer ID (e.g., "catalog-001") |
| **user_key** | Technical user identity (non-PII) |
| **channel** | "web" \| "telegram" \| "teams" |
| **context** | {tenant_id, channel, user_key, ...} |
| **rate_limit** | Per (tenant, user_key) |
| **JWT_secret** | Tenant's signing key (encrypted) |

---

## 💾 Database Schema (Simplified)

```sql
-- Tenants
id | name | api_key | plan | web_embed_origins | telegram_bot_token | teams_app_id

-- User Keys
id | tenant_id | channel | user_key | user_id | email | display_name

-- Conversations
id | tenant_id | channel | user_key | message_count | context_data

-- Messages
id | conversation_id | role | content | intent | confidence | created_at
```

---

## 🔑 JWT Payload (Web Embed)

```json
{
  "tenant_id": "catalog-001",
  "channel": "web",
  "user_key": "8f8a0b3c4d5e6f7a",
  "origin": "https://gsnake.com",
  "iat": 1702507200,
  "exp": 1702507500
}
```

**Validation:**
- ✅ Signature (HMAC-SHA256 with tenant's secret)
- ✅ Expiration (< 5 minutes old)
- ✅ Origin (matches request origin header)

---

## 🔗 API Endpoints

### Public
```
POST /embed/init
  Input: {site_id, platform, user_data}
  Output: {token, expiresIn, botConfig}

POST /bot/message
  Auth: JWT
  Input: {message, sessionId}
  Output: {messageId, response, intent, confidence}

POST /webhook/telegram?token=<bot-token>
  Body: Telegram update JSON
  Verify: Bot token

POST /webhook/teams?tenant_id=<id>
  Auth: Microsoft JWT
  Body: Teams message JSON
```

### Admin (requires API key)
```
POST /admin/tenants
  Input: {name, site_id, web_embed_origins, plan}
  Output: {tenant_id, api_key, jwt_secret}

GET /admin/tenants/<id>
  Output: TenantConfig

PUT /admin/tenants/<id>
  Input: Config updates
```

---

## 🛡️ Security Checklist

- [ ] All queries: `WHERE tenant_id = ?`
- [ ] JWT: signed + expiring + origin-bound
- [ ] Rate limit: Redis atomic operations
- [ ] Secrets: encrypted, never in logs
- [ ] CORS: only allowed origins
- [ ] HTTPS: all endpoints
- [ ] User_key: server-generated, unique per (tenant, channel)
- [ ] Progressive identity: optional PII

---

## ⚡ Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Invalid JWT | Check signature, expiry, origin |
| 403 Forbidden | Origin not allowed | Add to web_embed_origins |
| 429 Too Many Requests | Rate limit exceeded | Retry after indicated time |
| 404 Not Found | Tenant not found | Verify site_id/tenant_id |

---

## 📈 Rate Limiting

```
Key: rate_limit:<tenant_id>:<user_key>:<window>:<timestamp>

Limits (per plan):
  Basic: 20/min, 1000/hour, 10000/day
  Professional: 100/min, 5000/hour, 50000/day
  Enterprise: unlimited

Response header: X-RateLimit-Limit-Minute: 20
               X-RateLimit-Current-Minute: 18
```

---

## 🚀 Deployment Checklist

- [ ] Database migrations run
- [ ] Tenants created for each customer
- [ ] API keys generated & stored securely
- [ ] CORS origins configured
- [ ] Rate limits set per plan
- [ ] Monitoring/logging configured
- [ ] Load balancer configured
- [ ] Redis cache configured
- [ ] HTTPS certificates installed
- [ ] Secrets in environment variables

---

## 📱 Testing Quick Commands

```bash
# Test embed init
curl -X POST http://localhost:8386/embed/init \
  -H "Origin: https://gsnake.com" \
  -H "Content-Type: application/json" \
  -d '{"site_id":"catalog-001","platform":"web"}'

# Test bot message (with JWT)
curl -X POST http://localhost:8386/bot/message \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Origin: https://gsnake.com" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# Health check
curl http://localhost:8386/health
```

---

## 🔄 JWT Token Lifecycle

```
Time: 0s
  ├─ Browser: POST /embed/init
  └─ Response: JWT (exp: 300s)

Time: 250s
  ├─ embed.js: Refresh JWT before expiry
  └─ New JWT issued

Time: 300s (original token expires)
  └─ New JWT used for requests

Repeat every 5 minutes...
```

---

## 🎯 Design Principles

1. **Tenant Isolation:** Every query filters by tenant_id
2. **No User Auth:** Use user_key instead of login
3. **Channel Agnostic:** Same core, different adapters
4. **Stateless:** Workers have no local state
5. **Rate Limited:** Prevent abuse per tenant+user
6. **PII Optional:** user_key first, identity progressive

---

## 📞 Support Reference

| Issue | Check |
|-------|-------|
| Bot not appearing | Script loaded? Origin whitelisted? |
| Chat not working | JWT valid? Rate limit hit? |
| Telegram not responding | Bot token correct? Rate limit? |
| Teams not responding | JWT valid? App ID configured? |
| Performance slow | DB indexes? Redis cache? |

---

## 🔗 File Map

```
bot/
├─ docs/
│  ├─ MULTI_TENANT_AUTH_ARCHITECTURE.md      ← Main design
│  ├─ IMPLEMENTATION_ROADMAP.md               ← Phase plan
│  └─ SOLUTION_SUMMARY.md                     ← This project
│
└─ backend/
   ├─ schemas/multi_tenant_types.py           ← Data models
   ├─ interface/
   │  ├─ middleware/multi_tenant_auth.py      ← Auth logic
   │  ├─ handlers/embed_init_handler.py       ← /embed/init
   │  └─ multi_tenant_bot_api.py              ← Main API
   ├─ infrastructure/rate_limiter.py          ← Rate limiting
   ├─ shared/auth_config.py                   ← Config helpers
   └─ scripts/test_multi_tenant_auth.py       ← Tests

catalog/
└─ docs/BOT_SERVICE_INTEGRATION_GUIDE.md      ← Catalog guide
```

---

**Print & Share with Your Team! 📄**

