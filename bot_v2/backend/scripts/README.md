# Seed Data Scripts

Scripts để seed dữ liệu mẫu vào database cho development và testing.

## Seed Data Script

Script `seed_data.py` tạo dữ liệu mẫu đầy đủ cho flow hiện tại:

### Dữ liệu được tạo:

1. **Tenants** (2 tenants)
   - Demo Company (premium plan)
   - Test Tenant (basic plan)

2. **Channels** (2 channels cho tenant 1)
   - Telegram channel
   - Web channel

3. **Products** (3 products)
   - Laptop Dell XPS 15
   - iPhone 15 Pro
   - Wireless Headphones Premium

4. **Product Attributes**
   - Price, brand, RAM, storage cho các products

5. **Use Cases**
   - Allowed và disallowed use cases cho products

6. **FAQs**
   - Global FAQs
   - Product-specific FAQs

7. **Comparisons**
   - Comparison giữa các products

8. **Guardrails**
   - Forbidden topics
   - Disclaimers
   - Fallback message

9. **Intents** (3 intents)
   - ask_price
   - compare_products
   - ask_suitability

10. **Intent Patterns, Hints, Actions**
    - Patterns để match intents
    - Hints cho LLM
    - Actions để xử lý intents

11. **Migration Jobs**
    - Completed và pending jobs

12. **Conversation Logs**
    - Sample logs với success/failure

13. **Failed Queries**
    - Sample failed queries với reasons

## Cách chạy

### Option 1: Chạy trực tiếp

```bash
# Từ thư mục bot_v2
python -m backend.scripts.seed_data
```

### Option 2: Chạy với Python

```bash
# Từ thư mục bot_v2
cd backend/scripts
python seed_data.py
```

### Option 3: Chạy trong Docker

```bash
# Nếu đang chạy trong container
docker exec -it <container_name> python -m backend.scripts.seed_data
```

## Lưu ý

- Script sử dụng `ON CONFLICT DO NOTHING` để tránh duplicate data
- Script sẽ tự động commit nếu thành công, rollback nếu có lỗi
- Đảm bảo database đã được migrate (chạy `alembic upgrade head`) trước khi seed
- Script sẽ hiển thị Tenant ID để dùng cho testing

## Environment Variables

Script sử dụng database connection từ `backend.config.settings`, đọc từ:
- Environment variables (ưu tiên cao nhất)
- `.env` file
- Default values (development only)

## Troubleshooting

Nếu gặp lỗi:
1. Kiểm tra database connection string trong `.env` hoặc environment variables
2. Đảm bảo database đã được tạo và migrations đã chạy
3. Kiểm tra logs để xem lỗi cụ thể
