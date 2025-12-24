# 🔌 Catalog ↔ Bot Service Integration Guide

**Status:** Ready for Implementation  
**Audience:** Catalog Frontend + Backend Engineers  
**Purpose:** Step-by-step integration of bot service into catalog platform

---

## 📋 Quick Overview

Bot Service được thiết kế để **plug-and-play** vào bất kỳ website nào, kể cả Catalog.

**Quy trình:**
1. **Backend:** Catalog admin cấu hình bot service (tenant creation)
2. **Frontend:** Embed bot script vào trang web
3. **Runtime:** Người dùng tương tác với bot qua chat widget

---

## 🏗️ Architecture: Bot Service ↔ Catalog

```
┌─────────────────────────────────────┐
│   Catalog Frontend (Next.js)        │
│                                     │
│  ┌────────────────────────────────┐ │
│  │ Embed Bot Script               │ │
│  │ <script src="bot.service/e...">│ │
│  │                                │ │
│  │ Chat Widget                    │ │
│  │ (floating button)              │ │
│  └──────────┬─────────────────────┘ │
└─────────────┼─────────────────────────┘
              │
              ├─ POST /embed/init (get JWT)
              │
              ├─ POST /bot/message (chat)
              │
              └─ WebSocket (optional streaming)
                      ▼
        ┌─────────────────────────────┐
        │   Bot Service (@bot)        │
        │                             │
        │  Tenant: catalog-001        │
        │  Channel: web               │
        │  User Key: hash(session_id) │
        │                             │
        │  → Intent Routing           │
        │  → Knowledge Retrieval      │
        │  → Response Generation      │
        │                             │
        └─────────────────────────────┘
```

---

## 🔧 Step 1: Backend Setup (Catalog)

### 1.1 Create Tenant in Bot Service

**Request:**
```bash
curl -X POST https://bot.service/admin/tenants \
  -H "Authorization: Bearer <catalog-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GSNAKE Marketplace",
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

**Response:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "00000000-0000-0000-0000-000000000001",
    "api_key": "api_key_catalog_001_very_secure",
    "jwt_secret": "jwt_secret_catalog_001_for_embed_tokens",
    "web_embed_script_url": "https://bot.service/embed.js?site_id=catalog-001"
  }
}
```

### 1.2 Store Configuration in Catalog DB

**Backend Model (Catalog):**
```python
# catalog/backend/src/models/BotIntegration.ts (or similar)

interface BotIntegrationConfig {
  tenant_id: string          // From bot service
  site_id: string            // "catalog-001"
  api_key: string            // For backend communication
  jwt_secret: string         // For token verification (optional, for validation)
  web_embed_script_url: string
  enabled: boolean
  created_at: Date
  updated_at: Date
}
```

**Store in Database:**
```sql
INSERT INTO bot_integration_configs (
  tenant_id,
  site_id,
  api_key,
  jwt_secret,
  web_embed_script_url,
  enabled
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  'catalog-001',
  'api_key_catalog_001_very_secure',
  'jwt_secret_catalog_001_for_embed_tokens',
  'https://bot.service/embed.js?site_id=catalog-001',
  true
);
```

---

## 🎨 Step 2: Frontend Setup (Catalog)

### 2.1 Add Bot Script to Layout

**File:** `catalog/frontend/src/app/layout.tsx`

```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  useEffect(() => {
    // Load bot embed script dynamically
    const script = document.createElement('script');
    script.src = 'https://bot.service/embed.js?site_id=catalog-001';
    script.async = true;
    script.onload = () => {
      // Bot initialized
      console.log('Bot widget loaded');
    };
    document.body.appendChild(script);
  }, []);

  return (
    <html lang="vi">
      <body>
        <Navbar />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
```

### 2.2 Bot Widget Appears Automatically

**Embed Script Behavior:**
1. Loads embedded JWT token from `/embed/init`
2. Validates origin (`https://gsnake.com`)
3. Creates floating chat widget
4. Listens to user messages
5. Sends to `/bot/message` endpoint

**Result:**
- 🤖 Floating bot button bottom-right corner
- 💬 Click to open chat window
- ✨ Zero configuration needed

---

## 🔐 Step 3: Authentication Flow Details

### 3.1 Web Embed Flow (Frontend ↔ Bot Service)

```
User visits https://gsnake.com
    │
    ├─ Browser loads embed.js
    │
    ├─ embed.js calls POST /embed/init
    │  {
    │    "site_id": "catalog-001",
    │    "platform": "web",
    │    "user_data": {}  // optional
    │  }
    │
    │  Headers:
    │  ├─ Origin: https://gsnake.com
    │  └─ User-Agent: ...
    │
    └─ Bot Service validates:
       ├─ site_id exists & active
       ├─ origin in web_embed_origins
       └─ issues JWT (5 min expiry)
           Response:
           {
             "token": "eyJhbGciOiJIUzI1NiIs...",
             "expiresIn": 300,
             "botConfig": { ... }
           }

User sends: "Tôi là ai?"
    │
    ├─ Widget captures message
    │
    ├─ POST /bot/message
    │  {
    │    "message": "Tôi là ai?",
    │    "sessionId": "session-abc123"
    │  }
    │
    │  Headers:
    │  ├─ Authorization: Bearer <JWT token>
    │  ├─ Origin: https://gsnake.com
    │  └─ Content-Type: application/json
    │
    └─ Bot Service:
       ├─ Validates JWT signature
       ├─ Verifies origin matches token
       ├─ Checks rate limit
       ├─ Processes message
       └─ Returns response
           {
             "messageId": "msg_1234567890",
             "response": "Bạn là khách hàng của GSNAKE...",
             "intent": "general.identity",
             "confidence": 0.95
           }
```

### 3.2 JWT Token Structure

**Payload:**
```json
{
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "channel": "web",
  "user_key": "8f8a0b3c4d5e6f7a",        // hash(session_id)
  "origin": "https://gsnake.com",
  "iat": 1702507200,
  "exp": 1702507500                       // 5 minutes later
}
```

**Security:**
- ✅ Signed with tenant's `jwt_secret`
- ✅ Includes origin to prevent cross-site token reuse
- ✅ Short expiry (5 minutes) - auto-refresh in widget
- ✅ `user_key` is server-generated, not from user input

---

## 🛡️ Step 4: Security Considerations

### 4.1 Origin Validation

**IMPORTANT:** Bot service validates origin header.

❌ **Don't do this:**
```javascript
// DON'T: Hardcode token in script
const token = "hardcoded_jwt_token";
```

✅ **Do this:**
```javascript
// Embed script automatically requests fresh token
// Validates origin on every request
```

### 4.2 Secret Management

**For Catalog Backend:**
1. Store `api_key` securely (environment variable)
2. Use for admin endpoints (create/update tenant config)
3. Never expose to frontend

**For Catalog Frontend:**
1. Never hardcode JWT tokens
2. Let embed.js handle authentication
3. No credentials needed

### 4.3 Rate Limiting

Bot service applies rate limits per (tenant, user_key):

- **Basic Plan:** 20 req/min, 1000 req/hour
- **Professional:** 100 req/min, 5000 req/hour
- **Enterprise:** Unlimited

**Catalog current plan:** Check with bot service

---

## 🚀 Step 5: Advanced Features (Optional)

### 5.1 Progressive Identity

Optionally identify users:

```javascript
// embed.js initialization with user data
window.botConfig = {
  siteId: "catalog-001",
  userData: {
    userId: "user-123",
    email: "user@example.com",
    name: "John Doe"
  }
};
```

**Result:**
- Bot learns user's email/name
- Can provide personalized responses
- Still anonymous to 3rd parties

### 5.2 Custom Styling

**Embed.js supports theming:**

```javascript
window.botConfig = {
  siteId: "catalog-001",
  theme: {
    primaryColor: "#007bff",        // From catalog design tokens
    accentColor: "#0056b3",
    borderRadius: "8px",
    fontFamily: "Inter, sans-serif"
  }
};
```

### 5.3 Event Listeners

**React example:**

```tsx
useEffect(() => {
  // Listen to bot events
  window.addEventListener('bot:message-received', (event) => {
    console.log('Bot said:', event.detail.response);
  });

  return () => {
    window.removeEventListener('bot:message-received', ...);
  };
}, []);
```

---

## 📊 Step 6: Analytics & Monitoring

### 6.1 Bot Metrics (from Bot Service)

```bash
# Get usage stats for catalog tenant
curl https://bot.service/admin/tenants/catalog-001/stats \
  -H "Authorization: Bearer <api-key>"

Response:
{
  "messages_today": 1500,
  "unique_users": 350,
  "avg_response_time_ms": 245,
  "rate_limit_exceeded_count": 2,
  "top_intents": [
    "product.search" (450),
    "product.details" (320),
    "help.contact" (180)
  ]
}
```

### 6.2 Catalog-Side Logging

**Log bot interactions in Catalog DB:**

```typescript
// catalog/backend/src/routes/bot-webhook.ts

POST /api/bot/webhook (from bot service callback)

{
  "tenant_id": "catalog-001",
  "user_key": "8f8a0b3c...",
  "message": "Tôi muốn mua gì?",
  "response": "Xin mời xem catalog...",
  "intent": "product.search",
  "confidence": 0.92,
  "timestamp": "2025-12-20T12:00:00Z"
}

Save to:
CREATE TABLE bot_interactions (
  id UUID PRIMARY KEY,
  tenant_id VARCHAR,
  user_key VARCHAR,
  message TEXT,
  response TEXT,
  intent VARCHAR,
  confidence FLOAT,
  created_at TIMESTAMP
);
```

---

## 🔄 Step 7: Integration Checklist

### Backend (Catalog)

- [ ] Create bot integration database table
- [ ] Add endpoint to fetch bot config
- [ ] Store bot service credentials securely
- [ ] Add webhook endpoint for bot callbacks (optional)
- [ ] Implement logging for bot interactions
- [ ] Add monitoring/alerting for bot failures

### Frontend (Catalog)

- [ ] Add bot script to main layout
- [ ] Test bot appears on production domain
- [ ] Customize bot theme to match catalog design
- [ ] Test chat functionality
- [ ] Add error handling for bot failures
- [ ] Mobile testing (responsive chat widget)

### Deployment

- [ ] Whitelist catalog domains in bot service
- [ ] Set correct plan (basic/professional/enterprise)
- [ ] Configure rate limits appropriate for traffic
- [ ] Set up monitoring alerts
- [ ] Document in runbook/wiki

---

## 🐛 Troubleshooting

### Bot Widget Not Appearing

**Check:**
1. Script loaded? (DevTools → Network tab)
2. Origin in whitelist? (POST /embed/init returns 403?)
3. Console errors? (DevTools → Console)

**Solution:**
```bash
# Test embed init directly
curl -X POST http://bot.service/embed/init \
  -H "Origin: https://gsnake.com" \
  -H "Content-Type: application/json" \
  -d '{"site_id":"catalog-001","platform":"web"}'

# Should return:
# {"success":true,"data":{"token":"...","expiresIn":300}}
```

### Chat Messages Not Working

**Check:**
1. JWT valid? (Token expired after 5 min)
2. Rate limit hit? (Response status 429)
3. Backend down? (Check bot service health)

**Solution:**
```bash
# Check bot service health
curl http://bot.service/health

# Should return:
# {"status":"healthy","service":"pnj-hub-router","redis":"healthy"}
```

### Rate Limit Exceeded

**Check plan:**
```bash
# Get tenant config
curl http://bot.service/admin/tenants/catalog-001 \
  -H "Authorization: Bearer <api-key>"
```

**Solution:**
- Upgrade plan if needed
- Contact bot service operator
- Implement client-side debouncing

---

## 📚 References

- **Architecture:** `bot/docs/MULTI_TENANT_AUTH_ARCHITECTURE.md`
- **API Spec:** Bot service README
- **Security:** OWASP Authentication Cheat Sheet
- **Design Tokens:** Follow catalog's existing theme

---

## ✅ Success Criteria

After integration, you should see:

- ✅ Bot widget visible on catalog homepage
- ✅ Chat works (send/receive messages)
- ✅ No CORS errors in console
- ✅ Origin validation working (test different domain → 403)
- ✅ Rate limiting working (send 1000+ messages → 429)
- ✅ Performance acceptable (< 500ms response time)
- ✅ Mobile responsive
- ✅ Analytics logged

---

**Next:** 📞 Contact bot service team for tenant creation & configuration

