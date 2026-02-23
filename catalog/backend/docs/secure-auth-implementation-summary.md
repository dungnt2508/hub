# 🔐 Secure Auth Service - Implementation Summary

## ✅ Đã triển khai

### 1. Database Migrations

- **013_create_refresh_tokens_table.sql**: Tạo bảng `refresh_tokens` với:
  - Token hash (SHA-256)
  - Rotation support (previous_token_hash)
  - Revocation tracking
  - Expiration management

- **014_update_auth_providers_remove_tokens.sql**: Loại bỏ `access_token` và `refresh_token` columns từ `auth_providers`
  - Tuân thủ rule: KHÔNG lưu Google tokens

- **015_create_jwt_keys_table.sql**: Tạo bảng `jwt_keys` cho key rotation
  - RS256 key pairs
  - Key rotation support
  - JWKS endpoint data

### 2. Services

#### `jwt-key.service.ts`
- Generate RSA key pairs (RS256)
- Key rotation management
- JWKS public key export
- Active key retrieval

#### `refresh-token.service.ts`
- Opaque token generation (64 bytes random)
- SHA-256 hashing before storage
- Token rotation on each use
- Reuse detection (revoke all sessions if old token reused)
- Revocation support

#### `google-auth.service.ts`
- Google id_token verification với `google-auth-library`
- Extract email, sub từ Google payload
- Validate email_verified
- **KHÔNG lưu Google tokens**

#### `internal-jwt.service.ts`
- Generate internal JWT với đầy đủ claims:
  - `iss`: "catalog-auth"
  - `aud`: service-specific (e.g., "bot-service")
  - `sub`: internal user_id (UUID)
  - `exp`, `iat`: timestamps
  - `jti`: unique token ID
  - `role`: user role
  - `permissions`: optional permissions array
- Short-lived access tokens (30 minutes)
- RS256 signing với key rotation (kid header)

### 3. Routes

#### `secure-auth.routes.ts`
- **POST /auth/google**: Google OAuth login
  - Input: `{ id_token, audience }`
  - Output: `{ access_token, refresh_token, user }`

- **POST /auth/refresh**: Token refresh với rotation
  - Input: `{ refresh_token, audience }`
  - Output: `{ access_token, refresh_token (new) }`

- **POST /auth/logout**: Revoke refresh token
  - Input: `{ refresh_token }`
  - Output: success

- **GET /.well-known/jwks.json**: JWKS endpoint
  - Output: `{ keys: [...] }`

### 4. Repositories

#### `refresh-token.repository.ts`
- Token lookup by hash
- User tokens retrieval
- Active tokens query

#### `auth-provider.repository.ts` (updated)
- Loại bỏ access_token/refresh_token fields
- Chỉ lưu provider mapping (provider, provider_user_id)

## 🚀 Setup & Usage

### 1. Run Migrations

```bash
cd catalog/backend
npm run migrate
```

### 2. Environment Variables

Đảm bảo các biến môi trường sau được cấu hình:

```env
# Google OAuth (required for Google login)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback/google

# Database (required)
DB_HOST=localhost
DB_PORT=5433
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### 3. Initialize JWT Keys

Khi service khởi động lần đầu, keys sẽ được tự động tạo khi có request. Hoặc có thể tạo manually:

```typescript
import jwtKeyService from './services/jwt-key.service';

// Create initial key
await jwtKeyService.createNewKey('RS256');
```

### 4. API Usage Examples

#### Google Login Flow

```typescript
// 1. Client obtains Google id_token (frontend OAuth flow)
const googleIdToken = await getGoogleIdToken();

// 2. Send to Catalog Auth Service
const response = await fetch('http://localhost:3001/auth/google', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    id_token: googleIdToken,
    audience: 'bot-service',  // Target service
  }),
});

const { access_token, refresh_token, user } = await response.json();

// 3. Store tokens securely
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);
```

#### Token Refresh

```typescript
const refreshToken = localStorage.getItem('refresh_token');

const response = await fetch('http://localhost:3001/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    refresh_token: refreshToken,
    audience: 'bot-service',
  }),
});

const { access_token, refresh_token: newRefreshToken } = await response.json();

// Update stored tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', newRefreshToken);
```

#### Logout

```typescript
const refreshToken = localStorage.getItem('refresh_token');

await fetch('http://localhost:3001/auth/logout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token: refreshToken }),
});

// Clear tokens
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

#### JWT Verification (Downstream Service - Bot)

```typescript
// Bot Service verification
import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

// 1. Setup JWKS client
const client = jwksClient({
  jwksUri: 'https://catalog-service/.well-known/jwks.json',
});

function getKey(header: any, callback: any) {
  client.getSigningKey(header.kid, (err, key) => {
    const signingKey = key?.getPublicKey();
    callback(null, signingKey);
  });
}

// 2. Verify token
function verifyToken(token: string, expectedAudience: string) {
  return new Promise((resolve, reject) => {
    jwt.verify(
      token,
      getKey,
      {
        audience: expectedAudience,
        issuer: 'catalog-auth',
        algorithms: ['RS256'],
      },
      (err, decoded) => {
        if (err) reject(err);
        else resolve(decoded);
      }
    );
  });
}

// 3. Use in middleware
const token = req.headers.authorization?.replace('Bearer ', '');
const payload = await verifyToken(token, 'bot-service');
const userId = payload.sub;  // Internal user_id
```

## 🔍 Testing

### Test Google Login

```bash
# 1. Get Google id_token (use Google OAuth Playground or frontend)
# 2. Test endpoint
curl -X POST http://localhost:3001/auth/google \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN",
    "audience": "bot-service"
  }'
```

### Test JWKS Endpoint

```bash
curl http://localhost:3001/.well-known/jwks.json
```

### Test Token Refresh

```bash
curl -X POST http://localhost:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "audience": "bot-service"
  }'
```

## 🔒 Security Checklist

- [x] Google tokens không được lưu
- [x] Refresh tokens được hash trước khi lưu
- [x] JWT có đầy đủ claims (iss, aud, sub, exp, iat, jti)
- [x] RS256 với key rotation
- [x] Refresh token rotation
- [x] Reuse detection
- [x] Short-lived access tokens (30 phút)
- [x] Database là source of truth
- [x] JWKS endpoint exposed

## 📝 Next Steps

1. **Run migrations** để tạo database tables
2. **Test endpoints** với Google OAuth
3. **Update Bot Service** để verify JWT từ Catalog Auth
4. **Monitor** token usage và rotation
5. **Security audit** trước khi deploy production

## ⚠️ Important Notes

- **KHÔNG** commit private keys vào git
- **KHÔNG** log tokens (access_token, refresh_token)
- **KHÔNG** store Google tokens
- **KHÔNG** share JWT secrets across services
- **DO** rotate keys periodically
- **DO** monitor for token reuse
- **DO** enforce HTTPS in production

