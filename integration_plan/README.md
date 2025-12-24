# 🤖 Bot Service Integration Package

**Gói tích hợp bot service cho khách hàng**

Bộ file này chứa tất cả những gì cần thiết để tích hợp bot service vào website của bạn.

---

## 📦 Nội dung gói tích hợp

```
integration_plan/
├── README.md                    # File này - hướng dẫn tổng quan
├── INTEGRATION_GUIDE.md         # Hướng dẫn tích hợp chi tiết từng bước
├── embed.js                     # Script embed chính (copy vào website)
├── BotEmbed.tsx                 # React component (cho Next.js/React apps)
└── config.example.js            # Ví dụ cấu hình
```

---

## 🚀 Quick Start (3 bước)

### Bước 1: Lấy thông tin từ Bot Service

Liên hệ với team bot service để nhận:
- **Site ID**: Ví dụ `catalog-001`
- **API URL**: Ví dụ `https://bot.yourdomain.com`
- **Whitelist domain**: Domain của website bạn (ví dụ: `https://yourwebsite.com`)

### Bước 2: Thêm script vào website

**Cách 1: HTML đơn giản (cho static sites)**
```html
<!-- Thêm vào <head> hoặc trước </body> -->
<script 
  src="https://bot.yourdomain.com/embed.js"
  data-site-id="catalog-001"
  data-api-url="https://bot.yourdomain.com"
  async
  defer
></script>
```

**Cách 2: React/Next.js (dùng component có sẵn)**
```tsx
// Xem file BotEmbed.tsx
import BotEmbed from './BotEmbed';

export default function Layout() {
  return (
    <div>
      {/* Your content */}
      <BotEmbed />
    </div>
  );
}
```

### Bước 3: Kiểm tra

1. Mở website của bạn
2. Kiểm tra góc dưới bên phải → sẽ thấy nút chat bot
3. Click vào nút → chat window mở ra
4. Gửi tin nhắn test → bot sẽ trả lời

---

## 📋 Yêu cầu

- **Website**: Bất kỳ website nào (HTML, React, Vue, Angular, v.v.)
- **HTTPS**: Production phải dùng HTTPS (development có thể dùng HTTP)
- **Domain whitelist**: Domain của bạn phải được whitelist trong bot service

---

## 🔧 Cấu hình

### Environment Variables (cho React/Next.js)

Tạo file `.env.local`:
```bash
NEXT_PUBLIC_BOT_API_URL=https://bot.yourdomain.com
NEXT_PUBLIC_BOT_SITE_ID=catalog-001
```

### Customization

Bot widget tự động lấy theme từ bot service config. Nếu muốn customize:

```javascript
// Trước khi load embed.js
window.botConfig = {
  siteId: 'catalog-001',
  apiUrl: 'https://bot.yourdomain.com',
  theme: {
    primaryColor: '#FF6B35',
    backgroundColor: '#FFFFFF',
    textColor: '#1A1A1A',
    borderRadius: '12px'
  }
};
```

---

## 📚 Tài liệu chi tiết

- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Hướng dẫn tích hợp từng bước
- **[embed.js](./embed.js)** - Source code của embed script (tham khảo)
- **[BotEmbed.tsx](./BotEmbed.tsx)** - React component (cho Next.js/React)

---

## 🐛 Troubleshooting

### Bot widget không hiện

1. **Kiểm tra script đã load chưa:**
   - Mở DevTools (F12) → Network tab
   - Tìm request `embed.js` → phải status 200

2. **Kiểm tra console errors:**
   - DevTools → Console tab
   - Tìm lỗi màu đỏ

3. **Kiểm tra domain whitelist:**
   - Domain của bạn phải được whitelist trong bot service
   - Liên hệ team bot service để thêm domain

### Chat không hoạt động

1. **Kiểm tra bot service:**
   ```bash
   curl https://bot.yourdomain.com/health
   ```
   Phải trả về: `{"status":"healthy"}`

2. **Kiểm tra JWT token:**
   - DevTools → Network tab
   - Tìm request `POST /embed/init` → phải trả về token

3. **Kiểm tra rate limit:**
   - Nếu gửi quá nhiều tin nhắn → có thể bị rate limit
   - Đợi 1 phút rồi thử lại

---

## 🔐 Security

- ✅ **JWT tokens**: Tự động refresh mỗi 5 phút
- ✅ **Origin validation**: Bot service chỉ chấp nhận requests từ domain đã whitelist
- ✅ **HTTPS required**: Production phải dùng HTTPS
- ✅ **No credentials**: Không cần lưu password/API key ở frontend

---

## 📞 Support

Nếu gặp vấn đề:
1. Đọc [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) phần Troubleshooting
2. Kiểm tra console errors trong browser
3. Liên hệ team bot service với:
   - Site ID của bạn
   - Domain của website
   - Screenshot lỗi (nếu có)

---

## ✅ Checklist tích hợp

- [ ] Nhận Site ID và API URL từ bot service
- [ ] Domain được whitelist trong bot service
- [ ] Thêm script vào website
- [ ] Test bot widget hiển thị
- [ ] Test chat hoạt động
- [ ] Test trên mobile
- [ ] Customize theme (optional)
- [ ] Deploy lên production

---

**Chúc bạn tích hợp thành công! 🎉**

