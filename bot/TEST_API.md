# Test Bot Service API

## 1. Test `/embed/init` endpoint

### Cách 1: Dùng curl

```bash
curl -X POST http://localhost:8386/embed/init \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{
    "site_id": "catalog-001",
    "platform": "web",
    "user_data": {}
  }'
```

### Cách 2: Dùng Postman/Insomnia

- **Method**: POST
- **URL**: `http://localhost:8386/embed/init`
- **Headers**:
  - `Content-Type: application/json`
  - `Origin: http://localhost:3000`
- **Body** (raw JSON):
```json
{
  "site_id": "catalog-001",
  "platform": "web",
  "user_data": {}
}
```

### Cách 3: Dùng browser console

Mở browser console và chạy:

```javascript
fetch('http://localhost:8386/embed/init', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Origin': window.location.origin
  },
  body: JSON.stringify({
    site_id: 'catalog-001',
    platform: 'web',
    user_data: {}
  })
})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error(err));
```

## 2. Test `/bot/message` endpoint

Trước tiên cần lấy token từ `/embed/init`, sau đó:

```bash
curl -X POST "http://localhost:8386/bot/message?tenant_id=catalog-001" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_FROM_EMBED_INIT>" \
  -H "Origin: http://localhost:3000" \
  -d '{
    "message": "Xin chào",
    "sessionId": "test-session-123"
  }'
```

## 3. Test `/embed.js` endpoint

```bash
curl http://localhost:8386/embed.js
```

## 4. Test `/health` endpoint

```bash
curl http://localhost:8386/health
```

## Lưu ý

- Đảm bảo bot service đã chạy: `docker-compose up -d`
- Đảm bảo infra (postgres, redis) đã chạy
- `site_id` phải match với tenant đã đăng ký trong test data
- `Origin` header phải match với whitelist của tenant

