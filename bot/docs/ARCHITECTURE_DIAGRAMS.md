# 📊 Architecture Diagrams & Flows

## 1. System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                              │
├────────────────────┬─────────────────────┬───────────────────────┤
│  Web Embed         │  Telegram Bot       │  Teams Bot            │
│  (Script)          │  (User Message)     │  (User Message)       │
│                    │                     │                       │
│  GSNAKE.com        │  @hr_bot            │  HR Assistant         │
└─────────┬──────────┴────────────┬────────┴──────────┬────────────┘
          │                       │                    │
          │ HTTPS POST            │ Telegram Webhook   │ Teams Webhook
          │ /embed/init           │ /webhook/telegram  │ /webhook/teams
          │                       │                    │
┌─────────▼───────────────────────▼────────────────────▼────────────┐
│                    ADAPTER LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐      ┌──────────────┐      ┌────────────────┐  │
│  │ JWT Auth    │      │ Bot Token    │      │ Microsoft JWT  │  │
│  │ (Web Embed) │      │ Verification │      │ Verification   │  │
│  └──────┬──────┘      └──────┬───────┘      └────────┬───────┘  │
│         │                    │                       │            │
└─────────┼────────────────────┼───────────────────────┼────────────┘
          │                    │                       │
          └────────┬───────────┼───────────┬───────────┘
                   │           │           │
              ┌────▼───────────▼───────────▼────┐
              │  IDENTITY RESOLVER              │
              │                                 │
              │  Extract:                       │
              │  • tenant_id                    │
              │  • channel                      │
              │  • user_key                     │
              │  • auth_method                  │
              │  • metadata (IP, origin, etc)   │
              └────┬─────────────────────────────┘
                   │
              ┌────▼─────────────────────────────┐
              │  REQUEST CONTEXT                 │
              │  {                               │
              │    tenant_id,                    │
              │    channel,                      │
              │    user_key,                     │
              │    auth_method,                  │
              │    user_id (optional),           │
              │    user_email (optional)         │
              │  }                               │
              └────┬─────────────────────────────┘
                   │
              ┌────▼──────────────────────────────┐
              │  RATE LIMIT CHECK                 │
              │  Key: rate_limit:                 │
              │    <tenant_id>:                   │
              │    <user_key>:                    │
              │    <window>:<timestamp>           │
              │                                  │
              │  Redis: atomic increment          │
              │  Reject if > limit               │
              └────┬──────────────────────────────┘
                   │
              ┌────▼──────────────────────────────┐
              │  CORE BOT ENGINE                  │
              │  (Multi-tenant, Stateless)        │
              │                                  │
              │  ├─ Intent Classification        │
              │  ├─ Knowledge Retrieval          │
              │  ├─ Router / Domain Handler      │
              │  └─ Response Generation          │
              └────┬──────────────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼──┐  ┌──▼────┐  ┌─▼─────┐
    │  Web  │  │Telegram│ │ Teams │
    │Channel│  │Channel │ │Channel│
    │Return │  │Send via│ │Send  │
    │ JWT   │  │Telegram│ │Adaptive
    └───────┘  │API     │ │Card
         │  └────────┘  └────────┘
         │         │         │
         └─────────┼─────────┘
                   │
              ┌────▼──────────────────────────────┐
              │  STATE LAYER                      │
              │                                  │
              │  ┌──────────────────────────┐   │
              │  │ PostgreSQL               │   │
              │  │ • conversations          │   │
              │  │ • messages (history)     │   │
              │  │ • user_keys              │   │
              │  │ • tenants                │   │
              │  └──────────────────────────┘   │
              │                                  │
              │  ┌──────────────────────────┐   │
              │  │ Redis                    │   │
              │  │ • rate_limit:<key>       │   │
              │  │ • session_cache          │   │
              │  │ • tenant_config_cache    │   │
              │  └──────────────────────────┘   │
              └────────────────────────────────┘
```

---

## 2. Web Embed Authentication Flow

```
Timeline: User visits https://gsnake.com

T=0ms
┌──────────────────────────────┐
│ Browser loads page           │
│ <script src="bot.service/... │
│ /embed.js?site_id=catalog-001"│
└──────┬───────────────────────┘
       │
T=50ms │ embed.js loaded
       │
       ├─ Create floating widget
       │
       └─ Call POST /embed/init
           ├─ Headers: Origin: https://gsnake.com
           │
           └─ Body: {
               "site_id": "catalog-001",
               "platform": "web"
             }

T=150ms  ┌─ Bot Service receives request
         │
         ├─ Validate origin:
         │  ├─ Get tenant config (site_id → catalog-001)
         │  ├─ Check: https://gsnake.com in allowed_origins
         │  └─ ✅ Valid
         │
         ├─ Generate user_key:
         │  ├─ session_id = random 16 bytes
         │  ├─ user_key = hash(site_id + session_id)
         │  └─ Result: "8f8a0b3c4d5e6f7a"
         │
         ├─ Generate JWT:
         │  ├─ Payload:
         │  │  {
         │  │    "tenant_id": "catalog-001",
         │  │    "channel": "web",
         │  │    "user_key": "8f8a0b3c4d5e6f7a",
         │  │    "origin": "https://gsnake.com",
         │  │    "iat": 1702507200,
         │  │    "exp": 1702507500
         │  │  }
         │  │
         │  ├─ Get tenant's JWT secret
         │  ├─ Sign: HMAC-SHA256(payload, jwt_secret)
         │  └─ Result: "eyJhbGciOiJIUzI1NiI..."
         │
         └─ Return response:
            {
              "token": "eyJhbGciOiJIUzI1NiI...",
              "expiresIn": 300,
              "botConfig": {
                "name": "HR Assistant",
                "theme": {...}
              }
            }

T=200ms  ┌─ Browser receives response
         │
         ├─ embed.js stores token
         │
         ├─ Show chat widget
         │
         └─ Ready for user messages

T=5000ms User types: "Tôi còn bao nhiêu ngày phép?"
         │
         ├─ Click "Send"
         │
         └─ POST /bot/message
            ├─ Headers:
            │  ├─ Authorization: Bearer eyJhbGciOiJIUzI1NiI...
            │  ├─ Origin: https://gsnake.com
            │  └─ Content-Type: application/json
            │
            └─ Body: {
               "message": "Tôi còn bao nhiêu ngày phép?",
               "sessionId": "session-abc123"
             }

T=5100ms  ┌─ Bot Service receives request
          │
          ├─ Extract JWT from Authorization header
          │
          ├─ Verify JWT:
          │  ├─ Check signature (HMAC-SHA256)
          │  │  ├─ Get jwt_secret for tenant
          │  │  ├─ Recalculate signature
          │  │  └─ ✅ Match
          │  │
          │  ├─ Check expiration:
          │  │  ├─ exp = 1702507500
          │  │  ├─ now = 1702507200 (approx)
          │  │  └─ ✅ Not expired
          │  │
          │  └─ Check origin:
          │     ├─ JWT origin: https://gsnake.com
          │     ├─ Request origin: https://gsnake.com
          │     └─ ✅ Match
          │
          ├─ Extract context:
          │  {
          │    tenant_id: "catalog-001",
          │    channel: "web",
          │    user_key: "8f8a0b3c4d5e6f7a",
          │    auth_method: "jwt_web_embed"
          │  }
          │
          ├─ Check rate limit:
          │  ├─ Key: rate_limit:catalog-001:8f8a0b3c4d5e6f7a:minute:1702507200
          │  ├─ Redis INCR: 1
          │  ├─ Limit (professional): 100/min
          │  └─ ✅ 1 < 100, allowed
          │
          ├─ Process message:
          │  ├─ Load conversation history (Redis cache or DB)
          │  ├─ Add user message to conversation
          │  ├─ Route to domain engine (HR bot)
          │  ├─ Get response: "Bạn còn 8 ngày phép"
          │  └─ Add to conversation
          │
          └─ Return response:
             {
               "messageId": "msg_1702507251",
               "response": "Bạn còn 8 ngày phép",
               "intent": "hr.leave_balance",
               "confidence": 0.95
             }

T=5200ms  ┌─ Browser receives response
          │
          ├─ embed.js updates chat UI
          │
          ├─ Show bot response in chat
          │
          └─ Ready for next message
             │
             └─ [At T=295s: auto-refresh JWT before expiry]
                └─ POST /embed/init (same as T=0ms)
                   └─ New token for next 5 minutes
```

---

## 3. Telegram Webhook Flow

```
Timeline: Telegram user sends message

┌─────────────────────────────┐
│ Telegram User sends message │
│ to @hr_bot                  │
└──────────┬──────────────────┘
           │
           └─ Telegram API processes message
              ├─ Identifies bot by token
              ├─ Finds webhook URL in bot config
              └─ POST https://bot.service/webhook/telegram?token=123456789:ABC
                 Headers:
                   Content-Type: application/json
                 Body: {
                   "update_id": 123456789,
                   "message": {
                     "message_id": 1,
                     "date": 1702507200,
                     "chat": { "id": 987654321 },
                     "from": {
                       "id": 111222333,
                       "first_name": "John",
                       "username": "johndoe"
                     },
                     "text": "Tôi còn bao nhiêu ngày phép?"
                   }
                 }

┌─────────────────────────────┐
│ Bot Service Webhook Handler │
└──────────┬──────────────────┘
           │
           ├─ Extract bot token from query param
           │  └─ token = "123456789:ABC"
           │
           ├─ Verify bot token:
           │  ├─ Look up bot token → tenant_id mapping
           │  ├─ Get tenant config from DB
           │  ├─ Compare: stored_token == provided_token
           │  └─ ✅ Valid
           │
           ├─ Parse JSON body
           │  └─ Extract: update_id, from.id (111222333), text
           │
           ├─ Extract context:
           │  {
           │    tenant_id: <tenant-id-from-bot-token>,
           │    channel: "telegram",
           │    user_key: "111222333",
           │    auth_method: "telegram_bot"
           │  }
           │
           ├─ Check rate limit:
           │  ├─ Key: rate_limit:<tenant_id>:111222333:minute:<timestamp>
           │  ├─ Redis INCR
           │  ├─ If > limit: ignore & return 200 OK to Telegram
           │  └─ Otherwise: continue
           │
           ├─ Process message:
           │  ├─ Load conversation (or create new)
           │  ├─ Add message to history
           │  ├─ Send to router/domain engine
           │  ├─ Get response
           │  └─ Store in DB
           │
           ├─ Send response via Telegram API:
           │  └─ POST https://api.telegram.org/bot<TOKEN>/sendMessage
           │     {
           │       "chat_id": 987654321,
           │       "text": "Bạn còn 8 ngày phép",
           │       "reply_to_message_id": 1
           │     }
           │
           └─ Return 200 OK to Telegram:
              {
                "ok": true
              }

┌─────────────────────────────┐
│ Telegram User receives reply │
│ in chat                      │
└─────────────────────────────┘
```

---

## 4. Teams Message Flow

```
Timeline: Teams user sends message

┌────────────────────────────────────────┐
│ Teams User sends message to bot        │
│ (in Teams conversation)                │
└───────────┬────────────────────────────┘
            │
            └─ Microsoft Teams Bot Framework
               ├─ Validates bot registration
               ├─ Creates JWT (signed by Microsoft)
               ├─ Finds webhook URL
               └─ POST https://bot.service/webhook/teams?tenant_id=catalog-001
                  Headers:
                    Authorization: Bearer <Microsoft JWT>
                    Content-Type: application/json
                  Body: {
                    "type": "message",
                    "id": "1702507200",
                    "conversation": {
                      "id": "19:abcd1234@thread.skype",
                      "tenantId": "default"
                    },
                    "from": {
                      "aadObjectId": "00000000-0000-0000-0000-000000000001",
                      "userPrincipalName": "john.doe@company.com"
                    },
                    "text": "Tôi còn bao nhiêu ngày phép?"
                  }

┌────────────────────────────────────────┐
│ Bot Service Webhook Handler            │
└───────────┬────────────────────────────┘
            │
            ├─ Extract JWT from Authorization header
            │  └─ token = "eyJhbGciOiJSUzI1NiI..."
            │
            ├─ Verify Microsoft JWT:
            │  ├─ Fetch JWKs from Microsoft endpoint
            │  ├─ Verify signature with public key
            │  ├─ Check issuer = Microsoft
            │  ├─ Check aud = bot app ID
            │  ├─ Check exp (not expired)
            │  └─ ✅ Valid
            │
            ├─ Extract context from JWT:
            │  {
            │    tenant_id: <from JWT or query param>,
            │    channel: "teams",
            │    user_key: "00000000-0000-0000-0000-000000000001",
            │    auth_method: "teams_bot"
            │  }
            │
            ├─ Check rate limit:
            │  ├─ Key: rate_limit:<tenant_id>:00000000...:minute:<ts>
            │  ├─ Redis INCR
            │  └─ If exceeded: return error card
            │
            ├─ Process message:
            │  ├─ Load conversation history
            │  ├─ Add user message
            │  ├─ Route to domain engine
            │  ├─ Get response
            │  └─ Store in DB
            │
            ├─ Create Adaptive Card response:
            │  └─ {
            │       "$schema": "...",
            │       "type": "AdaptiveCard",
            │       "body": [
            │         {
            │           "type": "TextBlock",
            │           "text": "Bạn còn 8 ngày phép"
            │         }
            │       ]
            │     }
            │
            ├─ Send response via Teams API:
            │  └─ POST /v3/conversations/.../activities
            │     Body: Adaptive Card (from above)
            │
            └─ Return 200 OK:
               {
                 "type": "message",
                 "text": "Response sent"
               }

┌────────────────────────────────────────┐
│ Teams User receives reply               │
│ (as Adaptive Card in conversation)      │
└────────────────────────────────────────┘
```

---

## 5. Data Flow: Message Processing

```
Request arrives with context:
{
  tenant_id: "catalog-001",
  channel: "web",
  user_key: "8f8a0b3c4d5e6f7a",
  message: "Tôi còn bao nhiêu ngày phép?"
}

       ↓

┌─────────────────────────────────┐
│ Step 1: Load Conversation       │
│ (From Redis cache or DB)        │
├─────────────────────────────────┤
│ Key: conv:catalog-001:web:      │
│      8f8a0b3c4d5e6f7a           │
│                                 │
│ Returns: {                      │
│   id: "conv-123",               │
│   messages: [ ... ],            │
│   context_data: { ... }         │
│ }                               │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 2: Add User Message        │
│ to Conversation                 │
├─────────────────────────────────┤
│ Append: {                       │
│   role: "user",                 │
│   content: "Tôi còn bao...",    │
│   timestamp: now()              │
│ }                               │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 3: Intent Classification   │
│ (Embedding or LLM)              │
├─────────────────────────────────┤
│ Intent: "hr.leave_balance"      │
│ Confidence: 0.95                │
│ Entities: {}                    │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 4: Route to Domain Engine  │
│ (HR bot in this case)           │
├─────────────────────────────────┤
│ Domain: "hr"                    │
│ Intent: "leave_balance"         │
│ Context: conversation history   │
│ User: catalog-001 / web / ...   │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 5: Knowledge Retrieval     │
│ (RAG / Vector DB)               │
├─────────────────────────────────┤
│ Query: "leave balance"          │
│ Results: [                      │
│   "Employee has 8 days...",     │
│   "Leave policy: ..."           │
│ ]                               │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 6: Generate Response       │
│ (LLM with context)              │
├─────────────────────────────────┤
│ Prompt: "Answer based on:       │
│ - User message: ..."            │
│ - Knowledge: ..."               │
│ - Conversation: ..."            │
│                                 │
│ Response: "Bạn còn 8 ngày      │
│ phép theo hệ thống..."          │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 7: Add Bot Response        │
│ to Conversation                 │
├─────────────────────────────────┤
│ Append: {                       │
│   role: "assistant",            │
│   content: "Bạn còn 8...",      │
│   intent: "hr.leave_balance",   │
│   confidence: 0.95,             │
│   timestamp: now()              │
│ }                               │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 8: Save Conversation       │
│ (DB + Redis cache)              │
├─────────────────────────────────┤
│ PostgreSQL: conversation_messages│
│ Redis: cache with TTL           │
│ Update: last_message_at         │
│ Increment: message_count        │
└────────────┬────────────────────┘
             ↓

┌─────────────────────────────────┐
│ Step 9: Return Response          │
│ to Client                       │
├─────────────────────────────────┤
│ {                               │
│   messageId: "msg_1234567890",  │
│   response: "Bạn còn 8...",     │
│   intent: "hr.leave_balance",   │
│   confidence: 0.95,             │
│   followUpActions: [...]        │
│ }                               │
└─────────────────────────────────┘
```

---

## 6. Rate Limiting Timeline

```
User: catalog-001 / web / 8f8a0b3c4d5e6f7a
Limit: 20 requests/min

Timeline (each request):

12:00:00 (T=0s)
  Request #1 → Redis INCR → count=1 ✅ allowed
  Request #2 → Redis INCR → count=2 ✅ allowed
  ...
  Request #20 → Redis INCR → count=20 ✅ allowed
  Request #21 → Redis INCR → count=21 ❌ REJECTED (429)
  
  Key: rate_limit:catalog-001:8f8a0b3c4d5e6f7a:minute:1702507200
  TTL: 60 seconds (expires at 12:01:00)

12:00:15 (T=15s)
  Key still exists, count still = 21
  Request #22 → Redis INCR → count=22 ❌ REJECTED (429)

12:00:59 (T=59s)
  Request #23 → Redis INCR → count=23 ❌ REJECTED (429)

12:01:00 (T=60s)
  Redis key expires (TTL=60s)
  ├─ Key automatically deleted by Redis
  └─ New minute window starts

12:01:00+ (T=60s+)
  Request #24 → Redis INCR (new key) → count=1 ✅ allowed
  Request #25 → Redis INCR → count=2 ✅ allowed
  ...

Retry-After Header:
  When rejected → Response includes:
  Retry-After: 1    (retry in 1 second to 12:01:00)
```

---

**Diagrams are ASCII art for easy sharing in docs/code!**

