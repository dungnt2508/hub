# 🔄 Authentication Migration Guide

## Tổng quan

Catalog Auth Service đã được redesign theo secure architecture. Frontend và Bot Service cần update để tuân thủ rules mới.

## ✅ Đã cập nhật

### 1. Frontend (`catalog/frontend`)

#### Google OAuth Callback
- **File**: `src/app/auth/callback/google/page.tsx`
- **Thay đổi**: Sử dụng endpoint `/auth/google/callback` (backend xử lý code exchange)
- **Token storage**: 
  - `localStorage.setItem('token', access_token)`
  - `localStorage.setItem('refresh_token', refresh_token)`

#### Refresh Token Logic
- **File**: `src/shared/api/client.ts`
- **Thay đổi**: Update `refreshAccessToken()` để dùng POST `/auth/refresh` với `audience` parameter
- **Response format**: `{ access_token, refresh_token }` (thay vì `{ token, refreshToken }`)

### 2. Bot Service (`bot/backend`)

#### JWT Verification
- **File**: `bot/backend/infrastructure/auth_service.py`
- **Thay đổi**: 
  - Loại bỏ HS256 với shared secret
  - Verify với JWKS endpoint (RS256)
  - Verify `iss="catalog-auth"` và `aud="bot-service"`
  - Extract `user_id` từ `sub` claim (không phải `userId`)

#### JWKS Client
- **File mới**: `bot/backend/infrastructure/jwks_client.py`
- **Chức năng**: 
  - Fetch public keys từ `/.well-known/jwks.json`
  - Cache keys để giảm network calls
  - Convert JWK to PEM format

#### Config Updates
- **File**: `bot/backend/shared/auth_config.py`
- **Thay đổi**:
  - Loại bỏ `JWT_SECRET` (không cần nữa)
  - Thêm `CATALOG_SERVICE_URL` và `CATALOG_JWKS_URL`
  - Update `JWT_REQUIRED_ISS` = `"catalog-auth"`

### 3. Catalog Backend

#### Legacy Endpoint Update
- **File**: `catalog/backend/src/services/auth.service.ts`
- **Method**: `googleCallback()`
- **Thay đổi**: 
  - Exchange code để lấy `id_token` (không dùng `access_token`)
  - Gọi `googleAuthService.verifyIdToken()`
  - Gọi `internalJWTService.generateAccessToken()`
  - Return `access_token` và `refresh_token`

## 🔑 Token Format Changes

### Old Format (HS256)
```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "role": "user"
}
```

### New Format (RS256)
```json
{
  "iss": "catalog-auth",
  "aud": "bot-service",
  "sub": "uuid",  // user_id (NOT email, NOT google sub)
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "uuid",
  "role": "user",
  "permissions": []
}
```

## 📝 Environment Variables

### Bot Service
```env
# Required
CATALOG_SERVICE_URL=http://localhost:3001
JWT_REQUIRED_AUD=bot-service
JWT_REQUIRED_ISS=catalog-auth

# Optional
CATALOG_JWKS_URL=http://localhost:3001/.well-known/jwks.json
```

### Frontend
```env
# No changes needed - uses existing API_BASE_URL
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

## 🔍 Verification Flow

### Bot Service JWT Verification

```
1. Request arrives with Authorization: Bearer <token>
2. Bot extracts kid from JWT header
3. Bot fetches JWKS from Catalog: GET /.well-known/jwks.json
4. Bot finds public key with matching kid
5. Bot verifies JWT signature với public key (RS256)
6. Bot validates:
   - iss = "catalog-auth"
   - aud = "bot-service"
   - exp > now
7. Bot extracts user_id từ sub claim
8. Bot processes request với verified user_id
```

## ⚠️ Breaking Changes

1. **JWT Algorithm**: HS256 → RS256
2. **JWT Claims**: 
   - `userId` → `sub`
   - Thêm `iss`, `aud`, `jti` bắt buộc
3. **Token Verification**: Shared secret → JWKS public keys
4. **Refresh Token**: Opaque string với rotation

## 🚀 Migration Steps

### Step 1: Update Bot Service Config
```bash
# Update .env
CATALOG_SERVICE_URL=http://catalog-service:3001
JWT_REQUIRED_ISS=catalog-auth
JWT_REQUIRED_AUD=bot-service
```

### Step 2: Deploy Catalog Service
- Run migrations (refresh_tokens, jwt_keys tables)
- Initialize JWT keys (auto-created on first request)

### Step 3: Test Authentication
- Test Google login flow
- Test token refresh
- Test Bot service JWT verification

### Step 4: Monitor
- Check JWKS endpoint accessibility
- Monitor token validation errors
- Check key rotation

## 🔒 Security Checklist

- [x] Frontend không lưu Google tokens
- [x] Backend không lưu Google tokens
- [x] Bot service verify với JWKS (RS256)
- [x] JWT có đầy đủ claims (iss, aud, sub, exp, iat, jti)
- [x] Refresh token rotation implemented
- [x] Token reuse detection
- [x] Audit logging (không log tokens)

## 📚 Related Documentation

- `secure-auth-architecture.md` - Architecture details
- `secure-auth-implementation-summary.md` - Implementation summary
- `authen_rules.txt` - Security rules

