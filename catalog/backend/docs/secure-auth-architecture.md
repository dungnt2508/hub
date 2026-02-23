# 🔐 Catalog Auth Service - Secure Architecture

## 📋 Tổng quan

Catalog Auth Service là **SINGLE trust anchor** cho toàn bộ hệ thống authentication và authorization.

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Frontend/Mobile)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ 1. POST /auth/google
                         │    { id_token: "google_id_token" }
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Catalog Auth Service                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Google OAuth Verification                            │  │
│  │  - Verify id_token với Google public keys            │  │
│  │  - Extract email, sub                                │  │
│  │  - KHÔNG lưu Google tokens                           │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Internal JWT Generation                              │  │
│  │  - RS256 signing với key rotation                     │  │
│  │  - Claims: iss, aud, sub, exp, iat, jti, role        │  │
│  │  - Short-lived (30 phút)                              │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Refresh Token Service                                │  │
│  │  - Opaque random string                               │  │
│  │  - Hashed before storage                              │  │
│  │  - Rotation on each use                               │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      │ 2. Response
                      │    { access_token, refresh_token }
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Client stores tokens                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 3. API Request
                     │    Authorization: Bearer <access_token>
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Downstream Services (Bot, etc.)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JWT Verification                                     │  │
│  │  - GET /.well-known/jwks.json                        │  │
│  │  - Verify với public key                             │  │
│  │  - Check iss, aud, exp                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Authentication Flows

### Flow 1: Google OAuth Login

```
1. Client obtains Google id_token (client-side OAuth flow)
2. Client → POST /auth/google { id_token, audience }
3. Catalog Auth Service:
   a. Verify id_token với Google public keys
   b. Extract email, sub từ Google payload
   c. Map hoặc tạo internal user
   d. Issue internal JWT access_token (30 phút)
   e. Issue internal refresh_token (opaque, 7 ngày)
   f. Return { access_token, refresh_token }
4. Client stores tokens securely
```

### Flow 2: Token Refresh

```
1. Client → POST /auth/refresh { refresh_token, audience }
2. Catalog Auth Service:
   a. Hash refresh_token và lookup trong DB
   b. Validate: không revoked, không expired
   c. Check reuse: nếu token match previous_token_hash → revoke all sessions
   d. Rotate token:
      - Mark old token as revoked (reason: 'rotated')
      - Generate new refresh_token
      - Link new token với old token (previous_token_hash)
   e. Issue new access_token (30 phút)
   f. Return { access_token, refresh_token: new_token }
3. Client updates stored tokens
```

### Flow 3: Logout

```
1. Client → POST /auth/logout { refresh_token }
2. Catalog Auth Service:
   a. Hash refresh_token
   b. Mark token as revoked (reason: 'logout')
   c. Return success
3. Client clears tokens
Note: Access tokens expire naturally, không revoke actively
```

### Flow 4: JWT Verification (Downstream Service)

```
1. Service receives request với Authorization: Bearer <token>
2. Service → GET /.well-known/jwks.json
3. Service:
   a. Decode JWT header để lấy kid
   b. Find public key với kid trong JWKS
   c. Verify signature với public key
   d. Validate claims:
      - iss = "catalog-auth"
      - aud = expected service name
      - exp > now
   e. Extract user_id từ sub claim
4. Service processes request với verified user_id
```

## 📊 Database Schema

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- Nullable for OAuth-only users
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### auth_providers
```sql
CREATE TABLE auth_providers (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50),  -- 'google'
    provider_user_id VARCHAR(255),  -- Google sub
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);
-- RULE: KHÔNG có access_token, refresh_token columns
```

### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA-256 hash
    previous_token_hash VARCHAR(255),  -- For rotation reuse detection
    revoked_at TIMESTAMP,  -- NULL = active
    revoked_reason VARCHAR(100),  -- 'logout', 'reuse_detected', 'rotated'
    expires_at TIMESTAMP NOT NULL,
    device_info JSONB,
    ip_address INET,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_used_at TIMESTAMP
);
```

### jwt_keys
```sql
CREATE TABLE jwt_keys (
    id UUID PRIMARY KEY,
    kid VARCHAR(50) UNIQUE NOT NULL,  -- Key ID
    algorithm VARCHAR(10),  -- 'RS256'
    public_key_pem TEXT NOT NULL,  -- Exposed via JWKS
    private_key_pem TEXT NOT NULL,  -- For signing
    is_active BOOLEAN,  -- Active key for signing
    is_revoked BOOLEAN,  -- Revoked but still in JWKS for validation
    rotated_at TIMESTAMP,
    rotated_to_kid VARCHAR(50),
    created_at TIMESTAMP,
    revoked_at TIMESTAMP
);
```

## 🔒 Security Rationale

### 1. Google OAuth chỉ dùng để verify identity
- **Rationale**: Giảm attack surface - không phụ thuộc vào Google tokens
- **Implementation**: Verify id_token, extract email/sub, discard token
- **Rule**: KHÔNG lưu Google access_token/refresh_token

### 2. Internal JWT với đầy đủ claims
- **iss = "catalog-auth"**: Identify token issuer
- **aud = service-specific**: Prevent token reuse across services
- **sub = internal user_id**: Stable identifier, không leak email
- **exp/iat**: Short expiration window (30 phút)
- **jti**: Unique token ID cho revocation tracking

### 3. RS256 với key rotation
- **Rationale**: Asymmetric keys, không share secret
- **kid**: Support key rotation without breaking existing tokens
- **JWKS endpoint**: Public key discovery for verification

### 4. Refresh token rotation
- **Rationale**: Detect token theft - reuse detection
- **Implementation**: Mỗi lần dùng, rotate token và link với previous
- **Reuse detection**: Nếu old token được dùng → revoke all sessions

### 5. Database là source of truth
- **Rationale**: Persistence, audit trail
- **Redis chỉ dùng**: Rate limiting, blacklist (short-term), OAuth state

### 6. Access token không revoke actively
- **Rationale**: Stateless, short expiry (30 phút)
- **Logout chỉ revoke refresh token**: Prevent new token generation

## 📝 JWT Payload Example

```json
{
  "iss": "catalog-auth",
  "aud": "bot-service",
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "exp": 1735689600,
  "iat": 1735687800,
  "jti": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "permissions": ["read:products", "write:reviews"]
}
```

## 🔍 Verification Example (Downstream Service)

```typescript
// Bot Service verification
import jwt from 'jsonwebtoken';
import { get } from 'https';

// 1. Fetch JWKS
const jwks = await fetch('https://catalog-service/.well-known/jwks.json');
const keys = await jwks.json();

// 2. Decode token header
const decoded = jwt.decode(token, { complete: true });
const kid = decoded.header.kid;

// 3. Find matching key
const key = keys.keys.find(k => k.kid === kid);
const publicKey = convertJWKToPEM(key);

// 4. Verify token
const payload = jwt.verify(token, publicKey, {
  issuer: 'catalog-auth',
  audience: 'bot-service',
  algorithms: ['RS256']
});

// 5. Extract user_id
const userId = payload.sub;
```

## 🚫 Things This Service MUST NEVER Do

### ❌ NEVER
1. **Store Google access_token or refresh_token**
   - Rationale: Violates security boundaries, không cần thiết

2. **Propagate Google tokens to downstream services**
   - Rationale: Services chỉ trust Catalog Auth JWTs

3. **Use shared secrets for JWT signing**
   - Rationale: Use RS256/ES256 với asymmetric keys

4. **Skip aud/iss claims in JWT**
   - Rationale: Required for zero-trust verification

5. **Store refresh tokens in Redis as long-term storage**
   - Rationale: Database is source of truth

6. **Allow service-to-service calls với user JWT**
   - Rationale: Service identity ≠ User identity

7. **Reuse refresh tokens without rotation**
   - Rationale: Prevents reuse detection

8. **Issue access tokens without expiration**
   - Rationale: Short-lived tokens reduce risk

9. **Expose private keys via JWKS**
   - Rationale: Only public keys for verification

10. **Skip token hash before storage**
    - Rationale: Defense in depth - even if DB compromised

## 🔐 Key Rotation Process

```
1. Generate new key pair (RS256)
2. Set new key as active (is_active = true)
3. Set old key as inactive (is_active = false)
4. Old key remains in JWKS (is_revoked = false) for existing token validation
5. New tokens use new kid
6. Existing tokens continue to validate with old key until expiry
7. After grace period, mark old key as revoked (is_revoked = true)
```

## 📈 Monitoring & Auditing

- **Log events**: Auth success/failure, token refresh, logout, key rotation
- **Metrics**: Token generation rate, refresh rate, revocation rate
- **Alerts**: Unusual refresh patterns, reuse detection, key expiration warnings

## ✅ Checklist

- [x] Database migrations created
- [x] JWT key management service
- [x] Refresh token service với rotation
- [x] Google OAuth verification
- [x] Internal JWT generation
- [x] JWKS endpoint
- [x] Auth endpoints implemented
- [x] Security rules enforced
- [ ] Integration tests
- [ ] Performance testing
- [ ] Security audit

