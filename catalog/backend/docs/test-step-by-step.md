# 🧪 Test Authentication - Step by Step

## Bước 1: Kiểm tra JWKS Endpoint

```bash
curl http://localhost:3001/.well-known/jwks.json
```

**Hiện tại**: `{"keys":[]}` - Chưa có keys

**Giải pháp**: Keys sẽ được tự động tạo khi có request đầu tiên đến secure auth endpoint. Hoặc chạy script để tạo keys:

```bash
cd catalog/backend
tsx scripts/init-jwt-keys.ts
```

Sau đó test lại:
```bash
curl http://localhost:3001/.well-known/jwks.json | jq
```

**Expected**: JSON với `keys` array có ít nhất 1 key

## Bước 2: Test Google OAuth Flow

### Option 1: Dùng Frontend (Recommended)

1. **Start frontend**:
   ```bash
   cd catalog/frontend
   npm run dev
   ```

2. **Mở browser**: `http://localhost:3000/login`

3. **Click "Đăng nhập với Google"**

4. **Complete OAuth flow**

5. **Check tokens trong browser console**:
   ```javascript
   localStorage.getItem('token')  // access_token
   localStorage.getItem('refresh_token')  // refresh_token
   ```

### Option 2: Dùng Google OAuth Playground

1. Truy cập: https://developers.google.com/oauthplayground/
2. Chọn "Google OAuth2 API v2" → "userinfo.email"
3. Authorize → Copy `id_token` từ response

4. **Test endpoint**:
   ```bash
   export GOOGLE_ID_TOKEN="eyJhbGciOiJSUzI1NiIs..."
   
   curl -X POST http://localhost:3001/auth/google \
     -H "Content-Type: application/json" \
     -d "{
       \"id_token\": \"$GOOGLE_ID_TOKEN\",
       \"audience\": \"bot-service\"
     }" | jq
   ```

**Expected Response**:
```json
{
  "success": true,
  "message": "Google authentication successful",
  "data": {
    "user": {...},
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "abc123...",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

**Lưu tokens để test tiếp**:
```bash
export ACCESS_TOKEN="eyJhbGciOiJSUzI1NiIs..."
export REFRESH_TOKEN="abc123..."
```

## Bước 3: Verify JWT Token

### Decode JWT để xem payload:
```bash
# Decode payload (không verify)
echo "$ACCESS_TOKEN" | cut -d. -f2 | base64 -d | jq
```

**Expected**:
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

### Verify với Bot Service:
```bash
cd bot/backend
python scripts/test-jwt-verification.py "$ACCESS_TOKEN"
```

**Expected Output**:
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
```

## Bước 4: Test Token Refresh

```bash
curl -X POST http://localhost:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\",
    \"audience\": \"bot-service\"
  }" | jq
```

**Expected**: New `access_token` và `refresh_token` (rotated)

**Lưu ý**: Old refresh token sẽ không dùng được nữa (rotation).

## Bước 5: Test Logout

```bash
curl -X POST http://localhost:3001/auth/logout \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }" | jq
```

**Expected**: Success response

## Bước 6: Test Token Reuse Detection

Sau khi refresh token, thử dùng old token:

```bash
OLD_REFRESH_TOKEN="old_token_here"

curl -X POST http://localhost:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$OLD_REFRESH_TOKEN\",
    \"audience\": \"bot-service\"
  }"
```

**Expected**: Error - "Refresh token reuse detected - all sessions revoked"

## ✅ Checklist

- [ ] JWKS endpoint returns keys (sau khi init hoặc first request)
- [ ] Google OAuth flow works
- [ ] Access token issued với đúng claims (iss, aud, sub)
- [ ] Refresh token issued
- [ ] Token refresh works với rotation
- [ ] Logout revokes refresh token
- [ ] Bot service verifies JWT correctly
- [ ] Token reuse detection works
- [ ] Frontend stores tokens correctly

## 🔧 Troubleshooting

### Issue: JWKS returns empty keys
**Solution**: 
```bash
cd catalog/backend
tsx scripts/init-jwt-keys.ts
```

### Issue: Bot service can't verify token
**Check**:
1. `CATALOG_SERVICE_URL` có đúng không?
2. JWKS endpoint accessible từ bot service?
3. Token `iss` và `aud` có match config không?

### Issue: Token verification fails
**Check token claims**:
```bash
echo "$ACCESS_TOKEN" | cut -d. -f2 | base64 -d | jq
```

Verify:
- `iss` = "catalog-auth"
- `aud` = "bot-service" (hoặc audience bạn config)
- `exp` > current timestamp

