# Test Bot Embed từ Catalog Frontend

## Bước 1: Đảm bảo Bot Service đã chạy

### Kiểm tra bot service có đang chạy:

```bash
# Kiểm tra container
docker ps | grep hub_backend

# Hoặc kiểm tra health endpoint
curl http://localhost:8386/health

# Kết quả mong đợi:
# {"status":"healthy","service":"hub-bot-router","version":"1.0.0","redis":"healthy"}
```

### Nếu bot service chưa chạy:

```bash
# Start bot service
cd bot
docker-compose -f docker-compose.yml up -d

# Kiểm tra logs
docker-compose logs -f backend

# Kiểm tra port đã được expose
docker-compose ps
# Phải thấy: 0.0.0.0:8386->8386/tcp
```

### Troubleshooting ERR_CONNECTION_REFUSED:

1. **Bot service chưa start**:
   ```bash
   cd bot
   docker-compose up -d
   ```

2. **Port không đúng**:
   - Kiểm tra `docker-compose.yml` có expose port `8386:8386` không
   - Kiểm tra port 8386 có bị conflict không: `netstat -an | grep 8386`

3. **Network issue**:
   - Bot service phải connect được vào `hub_shared_net`
   - Kiểm tra: `docker network inspect hub_shared_net`

4. **Test trực tiếp**:
   ```bash
   # Từ host machine
   curl http://localhost:8386/health
   
   # Nếu không được, thử từ trong container
   docker exec -it hub_backend curl http://localhost:8386/health
   ```

## Bước 2: Cấu hình Environment Variables (tùy chọn)

Tạo file `.env.local` trong `catalog/frontend/`:

```env
NEXT_PUBLIC_BOT_API_URL=http://localhost:8386
NEXT_PUBLIC_BOT_SITE_ID=catalog-001
```

**Lưu ý:** Nếu không có file `.env.local`, sẽ dùng defaults:
- `NEXT_PUBLIC_BOT_API_URL`: `http://localhost:8386`
- `NEXT_PUBLIC_BOT_SITE_ID`: `catalog-001`

## Bước 3: Chạy Catalog Frontend

```bash
cd catalog/frontend
npm run dev
```

Frontend sẽ chạy tại: `http://localhost:3001` (hoặc port khác nếu 3001 đã được dùng)

## Bước 4: Test Bot Widget

1. **Mở browser**: Truy cập `http://localhost:3001`

2. **Mở Developer Tools** (F12):
   - Tab **Console**: Xem logs từ bot embed script
   - Tab **Network**: Xem các API calls

3. **Kiểm tra Bot Widget**:
   - Bot widget sẽ tự động load khi trang load
   - Tìm floating button ở góc dưới bên phải màn hình
   - Click vào button để mở chat window

4. **Kiểm tra Console Logs**:
   ```
   Bot embed script loaded
   ```

5. **Kiểm tra Network Requests**:
   - `GET http://localhost:8386/embed.js` - Load embed script
   - `POST http://localhost:8386/embed/init` - Initialize session
   - `POST http://localhost:8386/bot/message` - Send message

## Bước 5: Test Chat Functionality

1. **Click vào bot widget** để mở chat
2. **Nhập message**: "Xin chào"
3. **Nhấn Enter** hoặc click nút Send
4. **Kiểm tra response** từ bot

## Debugging

### Nếu bot widget không xuất hiện:

1. **Kiểm tra Console**:
   ```javascript
   // Chạy trong browser console
   console.log(window.BotEmbed);
   // Nếu undefined → script chưa load
   ```

2. **Kiểm tra script đã load**:
   ```javascript
   // Trong browser console
   document.querySelector('script[src*="embed.js"]');
   // Nếu null → script chưa được inject
   ```

3. **Kiểm tra Network tab**:
   - Xem request `embed.js` có thành công không (status 200)
   - Xem request `/embed/init` có lỗi không

### Nếu `/embed/init` trả về lỗi:

**Lỗi 403 - Origin not allowed**:
- Kiểm tra origin trong request header
- Đảm bảo origin match với whitelist trong test tenant config
- Test tenant mặc định cho phép: `http://localhost:3000`, `http://localhost:3001`, `*`

**Lỗi 404 - Tenant not found**:
- Kiểm tra `site_id` trong request body
- Mặc định: `catalog-001`
- Đảm bảo test data đã được setup (tự động khi bot service start)

**Lỗi 500 - Internal server error**:
- Kiểm tra bot service logs: `docker-compose logs -f backend`
- Kiểm tra database connection
- Kiểm tra Redis connection

### Manual Test trong Browser Console:

```javascript
// Test embed init manually
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
.then(data => {
  console.log('Embed init response:', data);
  if (data.success) {
    console.log('Token:', data.data.token);
    console.log('Bot config:', data.data.botConfig);
  }
})
.catch(err => console.error('Error:', err));
```

## Expected Flow

1. **Page Load** → `BotEmbed` component mount
2. **Script Load** → `embed.js` được inject vào page
3. **Auto Init** → Script tự động gọi `/embed/init`
4. **Get Token** → Nhận JWT token từ server
5. **Create Widget** → Floating button và chat window được tạo
6. **User Click** → Mở chat window
7. **User Send Message** → Gọi `/bot/message` với JWT token
8. **Bot Response** → Hiển thị response trong chat

## Troubleshooting Checklist

- [ ] Bot service đang chạy (`http://localhost:8386/health`)
- [ ] Catalog frontend đang chạy (`http://localhost:3001`)
- [ ] CORS được cấu hình đúng trong bot service
- [ ] Test tenant `catalog-001` đã được đăng ký
- [ ] Origin `http://localhost:3001` được phép trong tenant config
- [ ] Browser console không có lỗi
- [ ] Network tab shows successful requests
- [ ] Bot widget button xuất hiện ở góc dưới bên phải

