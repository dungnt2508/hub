# 🔌 Bot Service Integration Guide

**Status:** Ready for Implementation  
**Audience:** Frontend + Backend Engineers  
**Purpose:** Step-by-step integration of bot service into your website

---

## 📋 Quick Overview

Bot Service được thiết kế để **plug-and-play** vào bất kỳ website nào.

**Quy trình:**
1. **Backend:** Admin cấu hình bot service (tenant creation)
2. **Frontend:** Embed bot script vào trang web
3. **Runtime:** Người dùng tương tác với bot qua chat widget

---

## 🏗️ Architecture: Website ↔ Bot Service

```
┌─────────────────────────────────────┐
│   Your Website (Any Framework)      │
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
        │   Bot Service                │
        │                             │
        │  Tenant: your-site-id       │
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

## 🔧 Step 1: Backend Setup

### 1.1 Create Tenant in Bot Service

**Liên hệ team bot service để:**
- Tạo tenant cho website của bạn
- Nhận Site ID (ví dụ: `your-site-001`)
- Nhận API URL (ví dụ: `https://bot.yourdomain.com`)
- Whitelist domain của bạn

**Thông tin cần cung cấp:**
- Domain website (ví dụ: `https://yourwebsite.com`)
- Tên tenant (ví dụ: "Your Company Website")
- Plan (basic/professional/enterprise)

**Sau khi tạo tenant, bạn sẽ nhận:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "00000000-0000-0000-0000-000000000001",
    "site_id": "your-site-001",
    "api_key": "api_key_very_secure",
    "jwt_secret": "jwt_secret_for_embed_tokens",
    "web_embed_script_url": "https://bot.yourdomain.com/embed.js"
  }
}
```

### 1.2 Store Configuration (Optional - for backend integration)

Nếu bạn muốn tích hợp bot service vào backend của mình:

**Backend Model:**
```typescript
interface BotIntegrationConfig {
  tenant_id: string          // From bot service
  site_id: string            // "your-site-001"
  api_key: string            // For backend communication
  jwt_secret: string         // For token verification (optional)
  web_embed_script_url: string
  enabled: boolean
  created_at: Date
  updated_at: Date
}
```

---

## 🎨 Step 2: Frontend Setup

### 2.1 HTML/Static Sites

**Thêm script vào `<head>` hoặc trước `</body>`:**

```html
<script 
  src="https://bot.yourdomain.com/embed.js"
  data-site-id="your-site-001"
  data-api-url="https://bot.yourdomain.com"
  async
  defer
></script>
```

**Thay thế:**
- `https://bot.yourdomain.com` → API URL của bot service
- `your-site-001` → Site ID của bạn

### 2.2 React/Next.js

**Option 1: Dùng component có sẵn**

Copy file `BotEmbed.tsx` vào project của bạn:

```tsx
// src/components/BotEmbed.tsx
// (Copy từ integration_plan/BotEmbed.tsx)

// Trong layout hoặc root component:
import BotEmbed from '@/components/BotEmbed';

export default function Layout() {
  return (
    <div>
      <YourContent />
      <BotEmbed />
    </div>
  );
}
```

**Option 2: Load script manually**

```tsx
import { useEffect } from 'react';

export default function Layout() {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = process.env.NEXT_PUBLIC_BOT_API_URL + '/embed.js';
    script.setAttribute('data-site-id', process.env.NEXT_PUBLIC_BOT_SITE_ID);
    script.setAttribute('data-api-url', process.env.NEXT_PUBLIC_BOT_API_URL);
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  }, []);

  return <div>Your content</div>;
}
```

**Environment Variables (.env.local):**
```bash
NEXT_PUBLIC_BOT_API_URL=https://bot.yourdomain.com
NEXT_PUBLIC_BOT_SITE_ID=your-site-001
```

### 2.3 Vue.js

```vue
<template>
  <div>
    <!-- Your content -->
  </div>
</template>

<script>
export default {
  mounted() {
    const script = document.createElement('script');
    script.src = process.env.VUE_APP_BOT_API_URL + '/embed.js';
    script.setAttribute('data-site-id', process.env.VUE_APP_BOT_SITE_ID);
    script.setAttribute('data-api-url', process.env.VUE_APP_BOT_API_URL);
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  }
}
</script>
```

### 2.4 Angular

```typescript
// app.component.ts
import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html'
})
export class AppComponent implements OnInit {
  ngOnInit() {
    const script = document.createElement('script');
    script.src = environment.botApiUrl + '/embed.js';
    script.setAttribute('data-site-id', environment.botSiteId);
    script.setAttribute('data-api-url', environment.botApiUrl);
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  }
}
```

### 2.5 Bot Widget Appears Automatically

**Embed Script Behavior:**
1. Loads embedded JWT token from `/embed/init`
2. Validates origin (domain của bạn)
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
User visits https://yourwebsite.com
    │
    ├─ Browser loads embed.js
    │
    ├─ embed.js calls POST /embed/init
    │  {
    │    "site_id": "your-site-001",
    │    "platform": "web",
    │    "user_data": {}  // optional
    │  }
    │
    │  Headers:
    │  ├─ Origin: https://yourwebsite.com
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

User sends: "Hello"
    │
    ├─ Widget captures message
    │
    ├─ POST /bot/message
    │  {
    │    "message": "Hello",
    │    "sessionId": "session-abc123"
    │  }
    │
    │  Headers:
    │  ├─ Authorization: Bearer <JWT token>
    │  ├─ Origin: https://yourwebsite.com
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
             "response": "Hello! How can I help you?",
             "intent": "general.greeting",
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
  "origin": "https://yourwebsite.com",
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

**For Your Backend:**
1. Store `api_key` securely (environment variable)
2. Use for admin endpoints (create/update tenant config)
3. Never expose to frontend

**For Your Frontend:**
1. Never hardcode JWT tokens
2. Let embed.js handle authentication
3. No credentials needed

### 4.3 Rate Limiting

Bot service applies rate limits per (tenant, user_key):

- **Basic Plan:** 20 req/min, 1000 req/hour
- **Professional:** 100 req/min, 5000 req/hour
- **Enterprise:** Unlimited

**Check your plan:** Contact bot service team

---

## 🚀 Step 5: Advanced Features (Optional)

### 5.1 Progressive Identity

Optionally identify users:

```javascript
// Before loading embed.js
window.botConfig = {
  siteId: "your-site-001",
  apiUrl: "https://bot.yourdomain.com",
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
  siteId: "your-site-001",
  apiUrl: "https://bot.yourdomain.com",
  theme: {
    primaryColor: "#007bff",        // Your brand color
    backgroundColor: "#FFFFFF",
    textColor: "#1A1A1A",
    borderRadius: "12px",
    fontFamily: "Inter, sans-serif"
  }
};
```

### 5.3 Programmatic Control

```javascript
// Open chat programmatically
window.BotEmbed.open();

// Close chat
window.BotEmbed.close();

// Send message programmatically
window.BotEmbed.sendMessage("Hello bot!");
```

---

## 📊 Step 6: Analytics & Monitoring

### 6.1 Bot Metrics (from Bot Service)

Contact bot service team to get:
- Messages per day
- Unique users
- Average response time
- Top intents
- Rate limit exceeded count

### 6.2 Your-Side Logging (Optional)

If you want to log bot interactions in your database:

```typescript
// Listen to bot events
window.addEventListener('bot:message-sent', (event) => {
  // Log user message
  console.log('User said:', event.detail.message);
});

window.addEventListener('bot:message-received', (event) => {
  // Log bot response
  console.log('Bot said:', event.detail.response);
});
```

---

## 🔄 Step 7: Integration Checklist

### Backend (Optional)

- [ ] Store bot service credentials securely (if needed)
- [ ] Add webhook endpoint for bot callbacks (optional)
- [ ] Implement logging for bot interactions (optional)
- [ ] Add monitoring/alerting for bot failures (optional)

### Frontend

- [ ] Add bot script to main layout
- [ ] Test bot appears on production domain
- [ ] Customize bot theme to match your design (optional)
- [ ] Test chat functionality
- [ ] Add error handling for bot failures (optional)
- [ ] Mobile testing (responsive chat widget)

### Deployment

- [ ] Whitelist your domains in bot service
- [ ] Set correct plan (basic/professional/enterprise)
- [ ] Configure rate limits appropriate for traffic
- [ ] Set up monitoring alerts (optional)
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
curl -X POST https://bot.yourdomain.com/embed/init \
  -H "Origin: https://yourwebsite.com" \
  -H "Content-Type: application/json" \
  -d '{"site_id":"your-site-001","platform":"web"}'

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
curl https://bot.yourdomain.com/health

# Should return:
# {"status":"healthy","service":"pnj-hub-router","redis":"healthy"}
```

### Rate Limit Exceeded

**Check plan:**
Contact bot service team to check your plan and rate limits.

**Solution:**
- Upgrade plan if needed
- Contact bot service operator
- Implement client-side debouncing

---

## 📚 References

- **Quick Start:** [README.md](./README.md)
- **Embed Script:** [embed.js](./embed.js)
- **React Component:** [BotEmbed.tsx](./BotEmbed.tsx)

---

## ✅ Success Criteria

After integration, you should see:

- ✅ Bot widget visible on your website
- ✅ Chat works (send/receive messages)
- ✅ No CORS errors in console
- ✅ Origin validation working (test different domain → 403)
- ✅ Rate limiting working (send many messages → 429)
- ✅ Performance acceptable (< 500ms response time)
- ✅ Mobile responsive
- ✅ Analytics logged (if configured)

---

**Next:** 📞 Contact bot service team for tenant creation & configuration

