# 🚀 Implementation Roadmap - Multi-Tenant Bot Service

**Status:** Design Complete, Ready for Implementation  
**Timeline:** 3-4 weeks  
**Team:** Backend Engineers (Python/FastAPI)  
**Target:** Integrate @bot with @catalog

---

## 📦 Deliverables Overview

| File | Purpose | Status |
|------|---------|--------|
| `bot/docs/MULTI_TENANT_AUTH_ARCHITECTURE.md` | Complete auth architecture | ✅ Done |
| `bot/backend/schemas/multi_tenant_types.py` | Type definitions | ✅ Done |
| `bot/backend/interface/middleware/multi_tenant_auth.py` | Auth middleware | ✅ Done |
| `bot/backend/shared/auth_config.py` | Auth config helpers | ✅ Done |
| `bot/backend/interface/handlers/embed_init_handler.py` | Embed init API | ✅ Done |
| `bot/backend/infrastructure/rate_limiter.py` | Rate limiting | ✅ Done |
| `bot/backend/interface/multi_tenant_bot_api.py` | Main API integration | ✅ Done |
| `catalog/docs/BOT_SERVICE_INTEGRATION_GUIDE.md` | Catalog integration guide | ✅ Done |
| `bot/backend/scripts/test_multi_tenant_auth.py` | Test suite | ✅ Done |

---

## 🎯 Phase 1: Foundation (Week 1)

### Goals
- Set up database models for multi-tenant support
- Implement tenant registration & management
- Create JWT token generation infrastructure

### Tasks

```
1.1 Database Schema
    ├─ CREATE TABLE tenants
    │  ├─ id, name, api_key, webhook_secret
    │  ├─ web_embed_* config columns
    │  ├─ telegram_* config columns
    │  └─ teams_* config columns
    │
    ├─ CREATE TABLE user_keys
    │  ├─ id, tenant_id, channel, user_key (unique combo)
    │  └─ optional: user_id, email, display_name (progressive identity)
    │
    └─ CREATE TABLE conversations
       ├─ id, tenant_id, channel, user_key (unique combo)
       ├─ message_count, last_message_at
       ├─ context_data (JSONB)
       └─ conversation_messages table (messages log)

1.2 Tenant Service
    ├─ create_tenant(name, site_id, web_embed_origins)
    │  └─ Returns: tenant_id, api_key, jwt_secret
    │
    ├─ get_tenant_config(tenant_id)
    │  └─ Returns: TenantConfig object
    │
    ├─ activate_tenant(tenant_id)
    │
    └─ deactivate_tenant(tenant_id)

1.3 JWT Infrastructure
    ├─ generate_jwt(tenant_id, user_key, origin, expiry_seconds)
    │
    ├─ verify_jwt(token, tenant_id, origin)
    │  └─ Validates: signature, origin, expiration
    │
    └─ refresh_jwt(old_token)
       └─ Issues new token if old still valid

1.4 Tests
    └─ test_jwt_generation_and_verification()
```

**Deliverable:** Tenant registration working, JWT tokens issued & verified

---

## 🌐 Phase 2: Web Embed (Week 1-2)

### Goals
- Implement `/embed/init` endpoint for web embed initialization
- Create embed.js client script
- Full JWT-based authentication for web channel

### Tasks

```
2.1 Backend: /embed/init Endpoint
    ├─ POST /embed/init
    │  ├─ Input: {site_id, platform, user_data}
    │  ├─ Validation: origin whitelist, site_id exists
    │  ├─ Output: {token, expiresIn, botConfig}
    │  └─ Headers: Origin required
    │
    └─ Error handling:
       ├─ 400: Invalid site_id
       ├─ 403: Origin not allowed
       └─ 404: Tenant not found

2.2 Backend: /bot/message Endpoint
    ├─ POST /bot/message
    │  ├─ Auth: JWT in Authorization header
    │  ├─ Input: {message, sessionId, attachments}
    │  ├─ Process: rate limit check → router → response
    │  └─ Output: {messageId, response, intent, confidence}
    │
    └─ Error handling:
       ├─ 401: Invalid JWT
       ├─ 429: Rate limit exceeded
       └─ 400: Invalid message

2.3 Frontend: embed.js Script
    ├─ Load behavior:
    │  ├─ Call /embed/init on page load
    │  ├─ Create floating widget
    │  └─ Listen to messages
    │
    ├─ Send behavior:
    │  ├─ Capture message from input
    │  ├─ POST /bot/message with JWT
    │  └─ Update chat history
    │
    ├─ Auto-refresh JWT:
    │  ├─ Call /embed/init before expiry
    │  └─ Seamless user experience
    │
    └─ Styling:
       ├─ Floating button (customizable theme)
       ├─ Chat window (responsive, mobile-friendly)
       └─ Animations (smooth transitions)

2.4 Integration with Catalog
    ├─ Add script tag to catalog layout
    ├─ Test on catalog domain
    └─ Verify CORS headers

2.5 Tests
    ├─ test_embed_init_valid_origin()
    ├─ test_embed_init_invalid_origin()
    ├─ test_bot_message_valid_jwt()
    ├─ test_bot_message_expired_jwt()
    ├─ test_bot_message_rate_limit()
    └─ test_jwt_auto_refresh()
```

**Deliverable:** Web embed working on catalog, messages flow correctly

---

## 📱 Phase 3: Telegram Integration (Week 2)

### Goals
- Implement Telegram webhook handler
- Bot token management
- Telegram user identification

### Tasks

```
3.1 Backend: Telegram Configuration
    ├─ Store telegram_bot_token in tenant config
    ├─ Store telegram_webhook_url in config
    └─ Support multiple Telegram bots per service

3.2 Backend: /webhook/telegram Endpoint
    ├─ POST /webhook/telegram?token=<bot-token>
    │  ├─ Verify: bot token valid, JSON valid
    │  ├─ Extract: update_id, from.id (telegram_user_id), text
    │  ├─ Resolve: tenant_id from bot_token mapping
    │  ├─ Process: rate limit check → router → response
    │  └─ Send: reply via Telegram API
    │
    └─ Error handling:
       ├─ 401: Invalid bot token
       └─ 400: Invalid payload

3.3 Backend: Telegram API Integration
    ├─ TelegramClient class
    │  ├─ send_message(chat_id, text)
    │  ├─ send_keyboard(chat_id, options)
    │  └─ edit_message(chat_id, message_id, text)
    │
    └─ Async message sending

3.4 User Identity
    ├─ user_key = telegram_user_id
    ├─ Optional: map to user email/name
    └─ Rate limit per (tenant, telegram_user_id)

3.5 Tests
    ├─ test_telegram_webhook_valid_token()
    ├─ test_telegram_webhook_invalid_token()
    ├─ test_telegram_user_identification()
    └─ test_telegram_rate_limiting()
```

**Deliverable:** Bot responds to Telegram messages, user isolation working

---

## 🤖 Phase 4: Microsoft Teams Integration (Week 2-3)

### Goals
- Implement Teams Bot Framework webhook
- JWT verification (Microsoft JWKS)
- Adaptive Cards response format

### Tasks

```
4.1 Backend: Teams Configuration
    ├─ Store teams_app_id in tenant config
    ├─ Store teams_app_password (encrypted) in config
    └─ Support multiple Teams bots

4.2 Backend: /webhook/teams Endpoint
    ├─ POST /webhook/teams?tenant_id=<id>
    │  ├─ Verify: JWT from Microsoft
    │  ├─ Extract: conversation.tenantId, from.aadObjectId, text
    │  ├─ Resolve: tenant_id from request/JWT
    │  ├─ Process: rate limit check → router → response
    │  └─ Send: Adaptive Card via Teams API
    │
    └─ Error handling:
       ├─ 401: Invalid JWT
       └─ 400: Invalid payload

4.3 Backend: Microsoft JWT Verification
    ├─ Fetch JWKs from Microsoft endpoint
    ├─ Verify signature + issuer + audience
    ├─ Cache JWKs for performance
    └─ Handle JWK rotation

4.4 Backend: Teams API Integration
    ├─ TeamsClient class
    │  ├─ send_message(conversation_id, text)
    │  ├─ send_adaptive_card(conversation_id, card_json)
    │  └─ send_hero_card(conversation_id, data)
    │
    └─ Async message sending

4.5 User Identity
    ├─ user_key = aadObjectId
    ├─ Optional: map to email/name
    └─ Rate limit per (tenant, aadObjectId)

4.6 Tests
    ├─ test_teams_jwt_verification()
    ├─ test_teams_invalid_jwt()
    ├─ test_teams_user_identification()
    ├─ test_teams_adaptive_card()
    └─ test_teams_rate_limiting()
```

**Deliverable:** Bot responds in Teams, user isolation working

---

## 🛡️ Phase 5: Security & Scaling (Week 3)

### Goals
- Security hardening
- Performance optimization
- Horizontal scalability

### Tasks

```
5.1 Security Audit
    ├─ JWT secret rotation strategy
    ├─ API key rotation
    ├─ Encryption at rest (sensitive fields)
    ├─ HTTPS enforcement (all endpoints)
    ├─ CORS hardening
    └─ SQL injection prevention (parameterized queries)

5.2 Rate Limiting
    ├─ Redis-based rate limiter (already done)
    ├─ Per-minute limits
    ├─ Per-hour limits
    ├─ Per-day limits
    └─ Gradual backoff strategy

5.3 Monitoring & Logging
    ├─ Structured logging (JSON format)
    ├─ Error tracking (Sentry or similar)
    ├─ Performance metrics (response times)
    ├─ Rate limit exceeded events
    └─ Dashboards (Grafana)

5.4 Database Optimization
    ├─ Indexes on (tenant_id, channel, user_key)
    ├─ Conversation history pagination
    ├─ Archive old conversations (retention policy)
    └─ Connection pooling tuning

5.5 Horizontal Scaling
    ├─ Stateless worker design (no local state)
    ├─ Load balancer (Nginx/HAProxy)
    ├─ Redis for shared cache
    ├─ Database replicas for read scaling
    └─ Message queue for async tasks (optional Kafka)

5.6 Documentation
    ├─ API documentation (OpenAPI/Swagger)
    ├─ Deployment runbook
    ├─ Emergency procedures
    └─ FAQ & troubleshooting
```

**Deliverable:** Production-ready multi-tenant bot service

---

## 📊 Phase 6: Integration & Testing (Week 3+)

### Goals
- Full integration with catalog
- End-to-end testing
- Performance testing

### Tasks

```
6.1 Catalog Integration
    ├─ Add bot config to catalog DB
    ├─ Add bot script to catalog layout
    ├─ Test on staging environment
    ├─ Test on production (limited rollout)
    └─ Monitor metrics

6.2 End-to-End Testing
    ├─ Web embed flow (catalog domain)
    ├─ JWT token lifecycle
    ├─ Rate limiting
    ├─ Error handling
    └─ Cross-domain security

6.3 Performance Testing
    ├─ Load test (1000s concurrent users)
    ├─ Response time benchmarks
    ├─ Rate limiting under load
    └─ Database query optimization

6.4 User Testing
    ├─ Catalog users test bot
    ├─ Feedback collection
    ├─ Bug fixes
    └─ UX improvements
```

**Deliverable:** Bot integrated into catalog, live to users

---

## 🔄 Implementation Checklist

### Phase 1: Foundation
- [ ] Database schema created
- [ ] Tenant management CRUD
- [ ] JWT generation & verification working
- [ ] Tests passing

### Phase 2: Web Embed
- [ ] `/embed/init` endpoint working
- [ ] `/bot/message` endpoint working
- [ ] embed.js script functional
- [ ] Rate limiting working
- [ ] Tests passing
- [ ] Catalog integration complete

### Phase 3: Telegram
- [ ] Telegram configuration model
- [ ] `/webhook/telegram` endpoint
- [ ] Telegram API client
- [ ] Tests passing

### Phase 4: Teams
- [ ] Teams configuration model
- [ ] `/webhook/teams` endpoint
- [ ] Microsoft JWT verification
- [ ] Teams API client
- [ ] Tests passing

### Phase 5: Security & Scaling
- [ ] Security audit completed
- [ ] Rate limiting optimized
- [ ] Monitoring set up
- [ ] Load testing passed
- [ ] Horizontal scaling enabled

### Phase 6: Integration
- [ ] Catalog integration complete
- [ ] End-to-end testing passed
- [ ] Performance acceptable
- [ ] Live to users

---

## 🚨 Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **JWT secret compromise** | High | Implement key rotation, store in secure vault |
| **Cross-tenant data leak** | Critical | Strict SQL filtering, testing, code review |
| **Rate limit bypass** | Medium | Redundant checks, monitoring, IP filtering |
| **Performance degradation** | Medium | Caching, DB indexing, load testing |
| **Telegram API down** | Low | Retry logic, fallback responses |
| **Teams JWT verification fails** | Medium | Cached JWKs, graceful degradation |

---

## 📞 Communication Plan

| Stakeholder | Updates | Frequency |
|-------------|---------|-----------|
| **Catalog Team** | Integration status, API changes | Weekly |
| **Bot Operators** | Performance metrics, issues | Daily (automated) |
| **Users** | Changelog, new features | Monthly |

---

## 📈 Success Metrics

After deployment:

- ✅ **Availability:** 99.9% uptime
- ✅ **Response Time:** < 500ms (P99)
- ✅ **Rate Limiting:** Effective at preventing abuse
- ✅ **User Growth:** Monitored, no performance degradation
- ✅ **Security:** Zero reported data breaches
- ✅ **Integration:** Seamless with catalog, users satisfied

---

## 📚 References

- `bot/docs/MULTI_TENANT_AUTH_ARCHITECTURE.md` - Architecture details
- `catalog/docs/BOT_SERVICE_INTEGRATION_GUIDE.md` - Catalog integration
- `bot/backend/schemas/multi_tenant_types.py` - Type definitions
- `bot/backend/scripts/test_multi_tenant_auth.py` - Test examples

---

**Next Step:** 👉 Start Phase 1 implementation (Database + Tenant Management)

