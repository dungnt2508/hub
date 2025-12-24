# 🧪 Test Authentication - Hướng dẫn

## Prerequisites

1. **Catalog Service đang chạy**: `http://localhost:3001`
2. **Database migrations đã chạy**: `npm run migrate`
3. **JWT keys đã được tạo**: Tự động tạo khi có request đầu tiên

## Test 1: JWKS Endpoint

### Kiểm tra JWKS endpoint có hoạt động

```bash
curl http://localhost:3001/.well-known/jwks.json | jq
```

**Expected Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "key_...",
      "use": "sig",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

## Test 2: Google OAuth Flow

### Step 1: Lấy Google id_token

Có 2 cách:

#### Cách 1: Dùng Google OAuth Playground
1. Truy cập: https://developers.google.com/oauthplayground/
2. Chọn "Google OAuth2 API v2" → "userinfo.email"
3. Authorize và lấy `id_token` từ response

#### Cách 2: Dùng frontend flow
1. Mở frontend: `http://localhost:3000/login`
2. Click "Đăng nhập với Google"
3. Sau khi redirect, check browser console hoặc network tab để lấy `id_token`

### Step 2: Test POST /auth/google

```bash
# Set Google id_token
export GOOGLE_ID_TOKEN="eyJhbGciOiJSUzI1NiIs..."

# Test endpoint
curl -X POST http://localhost:3001/auth/google \
  -H "Content-Type: application/json" \
  -d "{
    \"id_token\": \"$GOOGLE_ID_TOKEN\",
    \"audience\": \"bot-service\"
  }" | jq
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Google authentication successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user"
    },
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "abc123...",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

### Step 3: Lưu tokens để test tiếp

```bash
# Extract tokens từ response
export ACCESS_TOKEN="eyJhbGciOiJSUzI1NiIs..."
export REFRESH_TOKEN="abc123..."
```

## Test 3: Token Refresh

```bash
curl -X POST http://localhost:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\",
    \"audience\": \"bot-service\"
  }" | jq
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "xyz789...",  // New token (rotated)
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

**Lưu ý**: Refresh token mới sẽ được trả về (rotation).

## Test 4: Logout

```bash
curl -X POST http://localhost:3001/auth/logout \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }" | jq
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Logout successful",
  "data": {}
}
```

## Test 5: Bot Service JWT Verification

### Step 1: Decode JWT để xem payload

```bash
# Decode JWT (không verify)
echo "$ACCESS_TOKEN" | cut -d. -f2 | base64 -d | jq
```

**Expected Payload:**
```json
{
  "iss": "catalog-auth",
  "aud": "bot-service",
  "sub": "user-uuid",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "token-uuid",
  "role": "user",
  "permissions": []
}
```

### Step 2: Test Bot Service verification

```bash
cd bot/backend
python scripts/test-jwt-verification.py "$ACCESS_TOKEN"
```

**Expected Output:**
```
🧪 Testing JWT Verification
==================================================
Token (first 50 chars): eyJhbGciOiJSUzI1NiIs...

Verifying JWT token...
✅ Token verified successfully!

Payload:
  - user_id (sub): user-uuid
  - email: user@example.com
  - role: user
  - iss: catalog-auth
  - aud: bot-service
  - exp: 1234567890
  - iat: 1234567890
```

## Test 6: Frontend Integration Test

### Step 1: Start frontend
```bash
cd catalog/frontend
npm run dev
```

### Step 2: Test Google Login Flow
1. Mở `http://localhost:3000/login`
2. Click "Đăng nhập với Google"
3. Complete Google OAuth flow
4. Check browser localStorage:
   - `localStorage.getItem('token')` → should have access_token
   - `localStorage.getItem('refresh_token')` → should have refresh_token

### Step 3: Test API calls với token
1. Open browser DevTools → Network tab
2. Navigate to protected page
3. Check request headers:
   - `Authorization: Bearer <access_token>`
4. Verify response is successful

### Step 4: Test Token Refresh
1. Wait for token to expire (30 minutes) hoặc manually expire it
2. Make API call
3. Check network tab - should see:
   - First request: 401 Unauthorized
   - Automatic refresh call to `/auth/refresh`
   - Retry original request với new token

## Test 7: Token Reuse Detection

```bash
# Use old refresh token after rotation
OLD_REFRESH_TOKEN="old_token_here"

curl -X POST http://localhost:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$OLD_REFRESH_TOKEN\",
    \"audience\": \"bot-service\"
  }"
```

**Expected**: Error - "Refresh token reuse detected - all sessions revoked"

## Test 8: Invalid Token Scenarios

### Test với invalid audience
```bash
# Get token với audience="catalog-frontend"
TOKEN_FRONTEND="..."

# Try to use in bot service (expects "bot-service")
curl -X POST http://bot-service:8386/api/v1/router/route \
  -H "Authorization: Bearer $TOKEN_FRONTEND" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

**Expected**: 401 Unauthorized - "Invalid token audience"

### Test với expired token
```bash
# Use expired token
EXPIRED_TOKEN="..."

curl -X POST http://bot-service:8386/api/v1/router/route \
  -H "Authorization: Bearer $EXPIRED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

**Expected**: 401 Unauthorized - "Token has expired"

## Test 9: JWKS Key Rotation

### Step 1: Check current active key
```bash
curl http://localhost:3001/.well-known/jwks.json | jq '.keys[] | select(.kid)'
```

### Step 2: Rotate keys (manual hoặc automatic)
```bash
# Call key rotation endpoint (if exists) hoặc wait for automatic rotation
```

### Step 3: Verify old tokens still work
- Tokens signed với old key vẫn validate được (old key vẫn trong JWKS)
- New tokens dùng new key

## 🔍 Debugging Tips

### Check JWT payload
```bash
# Decode JWT header
echo "$TOKEN" | cut -d. -f1 | base64 -d | jq

# Decode JWT payload
echo "$TOKEN" | cut -d. -f2 | base64 -d | jq
```

### Check JWKS response
```bash
curl -v http://localhost:3001/.well-known/jwks.json
```

### Check Bot Service logs
```bash
# Check if JWKS fetch is successful
docker logs bot_backend | grep jwks
```

### Check Catalog Service logs
```bash
# Check auth requests
docker logs catalog_backend | grep auth
```

## ✅ Success Criteria

- [ ] JWKS endpoint returns valid keys
- [ ] Google OAuth flow works end-to-end
- [ ] Access tokens are issued correctly
- [ ] Refresh tokens work with rotation
- [ ] Logout revokes refresh tokens
- [ ] Bot service verifies JWTs correctly
- [ ] Token reuse detection works
- [ ] Invalid tokens are rejected
- [ ] Frontend stores tokens correctly
- [ ] Frontend refresh logic works

## 🐛 Common Issues

### Issue: JWKS endpoint returns 404
**Solution**: Ensure secure auth routes are registered in `index.ts`

### Issue: Bot service can't fetch JWKS
**Solution**: Check `CATALOG_SERVICE_URL` env var in bot service

### Issue: Token verification fails với "Invalid issuer"
**Solution**: Check `JWT_REQUIRED_ISS` matches token `iss` claim ("catalog-auth")

### Issue: Token verification fails với "Invalid audience"
**Solution**: Check `JWT_REQUIRED_AUD` matches token `aud` claim

### Issue: Frontend tokens not stored
**Solution**: Check browser console for errors, verify response format

