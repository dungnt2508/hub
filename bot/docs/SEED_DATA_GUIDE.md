# Hướng Dẫn Tạo Data Cho Admin Dashboard

Hướng dẫn tạo sample data cho các pages trên frontend admin dashboard.

---

## 📋 Tổng Quan

Script seed data sẽ tạo:
- ✅ Admin user (nếu chưa có)
- ✅ Pattern Rules (5 rules)
- ✅ Keyword Hints (3 domains)
- ✅ Routing Rules (3 rules)
- ✅ Prompt Templates (4 templates)

---

## 🚀 Cách Sử Dụng

### Option 1: Chạy Script Trực Tiếp

```bash
# Từ thư mục bot/
cd bot

# Chạy script
python -m backend.scripts.seed_admin_data
```

### Option 2: Chạy Với Docker

```bash
# Nếu đang dùng Docker
docker exec -it <container_name> python -m backend.scripts.seed_admin_data
```

### Option 3: Chạy Trong Python Shell

```python
import asyncio
from backend.scripts.seed_admin_data import seed_admin_data

asyncio.run(seed_admin_data())
```

---

## 📝 Data Được Tạo

### 1. Admin User

- **Email**: `admin@example.com`
- **Password**: `admin123`
- **Role**: `admin`
- **Tenant**: Global (None)

### 2. Pattern Rules (8 rules) - Tối ưu cho tiếng Việt

#### HR - Tra cứu số ngày phép
- **Pattern**: `(?:tôi|mình|em|tớ|anh|chị)\s+(?:còn|đang có|có)\s+(?:bao nhiêu|mấy)\s+(?:ngày|ngày phép|ngày nghỉ|ngày nghỉ phép)`
- **Domain**: `hr`
- **Intent**: `query_leave_balance`
- **Priority**: 100

#### HR - Xin nghỉ phép
- **Pattern**: `(?:xin|đăng ký|tạo|tạo đơn|làm đơn)\s+(?:nghỉ phép|nghỉ|phép|nghỉ việc)`
- **Domain**: `hr`
- **Intent**: `create_leave_request`
- **Priority**: 90

#### HR - Duyệt đơn nghỉ phép
- **Pattern**: `(?:duyệt|chấp nhận|đồng ý|phê duyệt)\s+(?:đơn nghỉ phép|đơn phép|đơn xin nghỉ)`
- **Domain**: `hr`
- **Intent**: `approve_leave`
- **Priority**: 80

#### HR - Tra cứu lương
- **Pattern**: `(?:lương|tiền lương|thu nhập|bảng lương)\s+(?:tháng|này|năm|bao nhiêu)`
- **Domain**: `hr`
- **Intent**: `query_salary`
- **Priority**: 75

#### Catalog - Tìm kiếm sản phẩm
- **Pattern**: `(?:tìm|tìm kiếm|mua|bán|bán gì|mua gì|có gì)\s+(?:sản phẩm|hàng|đồ|món|sp)`
- **Domain**: `catalog`
- **Intent**: `search_products`
- **Priority**: 70

#### Catalog - Xem giá sản phẩm
- **Pattern**: `(?:giá|giá bao nhiêu|bao nhiêu tiền|giá cả)\s+(?:của|sản phẩm|món|hàng)`
- **Domain**: `catalog`
- **Intent**: `query_price`
- **Priority**: 65

#### Chào hỏi
- **Pattern**: `^(?:chào|hello|hi|xin chào|hey|chào bạn|chào anh|chào chị)`
- **Domain**: `meta`
- **Intent**: `greeting`
- **Priority**: 50

#### Cảm ơn
- **Pattern**: `^(?:cảm ơn|cám ơn|thanks|thank you|tks)`
- **Domain**: `meta`
- **Intent**: `thank_you`
- **Priority**: 45

### 3. Keyword Hints (3 domains) - Từ khóa tiếng Việt

#### HR Domain - Từ khóa tiếng Việt
- **Domain**: `hr`
- **Keywords**: 
  - nghỉ phép (0.95), ngày phép (0.95), phép (0.9)
  - nghỉ việc (0.85), xin nghỉ (0.85), đơn nghỉ (0.85)
  - duyệt đơn (0.8), lương (0.8), tiền lương (0.8), bảng lương (0.75)
  - nhân viên (0.7), nhân sự (0.7), hr (0.65)

#### Catalog Domain - Từ khóa tiếng Việt
- **Domain**: `catalog`
- **Keywords**:
  - sản phẩm (0.95), hàng (0.9), món (0.9), đồ (0.85)
  - mua (0.85), bán (0.85)
  - giá (0.8), giá cả (0.8), giá tiền (0.75)
  - tìm kiếm (0.75), tìm (0.7), catalog (0.65), danh mục (0.65)

#### Knowledge Domain - Từ khóa tiếng Việt
- **Domain**: `knowledge`
- **Keywords**:
  - là gì (0.95), là ai (0.9), là như thế nào (0.9)
  - hướng dẫn (0.85), cách làm (0.85), cách (0.8), như thế nào (0.8)
  - tại sao (0.75), vì sao (0.75)
  - giải thích (0.7), kiến thức (0.65), thông tin (0.65)

### 4. Routing Rules (5 rules)

#### HR - Tra cứu ngày phép
- **Intent**: `query_leave_balance`
- **Target Domain**: `hr`
- **Priority**: 100

#### HR - Tạo đơn nghỉ phép
- **Intent**: `create_leave_request`
- **Target Domain**: `hr`
- **Priority**: 90

#### HR - Duyệt đơn nghỉ phép
- **Intent**: `approve_leave`
- **Target Domain**: `hr`
- **Priority**: 85

#### Catalog - Tìm kiếm sản phẩm
- **Intent**: `search_products`
- **Target Domain**: `catalog`
- **Priority**: 80

#### Catalog - Tra cứu giá
- **Intent**: `query_price`
- **Target Domain**: `catalog`
- **Priority**: 75

### 5. Prompt Templates (7 templates) - Tiếng Việt

#### HR - Tra cứu ngày phép System Prompt
- **Type**: `system`
- **Domain**: `hr`
- **Template**: "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tra cứu số ngày phép còn lại. Hãy thân thiện và chuyên nghiệp. Trả lời bằng tiếng Việt."

#### HR - Tạo đơn nghỉ phép System Prompt
- **Type**: `system`
- **Domain**: `hr`
- **Template**: "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tạo đơn xin nghỉ phép. Cần thu thập thông tin: ngày bắt đầu, ngày kết thúc, và lý do nghỉ. Trả lời bằng tiếng Việt."

#### HR - Duyệt đơn nghỉ phép System Prompt
- **Type**: `system`
- **Domain**: `hr`
- **Template**: "Bạn là trợ lý nhân sự. Hãy giúp quản lý duyệt đơn nghỉ phép. Chỉ quản lý và admin mới có quyền duyệt. Trả lời bằng tiếng Việt."

#### Catalog - Tìm kiếm sản phẩm System Prompt
- **Type**: `system`
- **Domain**: `catalog`
- **Template**: "Bạn là trợ lý tìm kiếm sản phẩm. Hãy giúp người dùng tìm kiếm sản phẩm trong danh mục. Hỏi thêm thông tin nếu cần. Trả lời bằng tiếng Việt."

#### Catalog - Tra cứu giá System Prompt
- **Type**: `system`
- **Domain**: `catalog`
- **Template**: "Bạn là trợ lý tra cứu giá. Hãy giúp người dùng tra cứu giá sản phẩm. Hiển thị giá rõ ràng và đầy đủ. Trả lời bằng tiếng Việt."

#### Knowledge - Hỏi đáp System Prompt
- **Type**: `system`
- **Domain**: `knowledge`
- **Template**: "Bạn là trợ lý hỏi đáp. Hãy trả lời câu hỏi dựa trên cơ sở kiến thức được cung cấp. Nếu không biết, hãy nói rõ. Trả lời bằng tiếng Việt."

#### Meta - Chào hỏi System Prompt
- **Type**: `system`
- **Domain**: `meta`
- **Template**: "Bạn là trợ lý thân thiện. Hãy chào hỏi người dùng một cách thân thiện và nhiệt tình. Trả lời bằng tiếng Việt."

---

## ✅ Kiểm Tra Data

### 1. Kiểm Tra Admin User

```bash
# Login vào admin dashboard
# URL: http://localhost:3000/login
# Email: admin@example.com
# Password: admin123
```

### 2. Kiểm Tra Pattern Rules

- Vào `/admin/patterns`
- Sẽ thấy 5 pattern rules đã được tạo

### 3. Kiểm Tra Keyword Hints

- Vào `/admin/keywords`
- Sẽ thấy 3 keyword hints cho 3 domains

### 4. Kiểm Tra Routing Rules

- Vào `/admin/routing/rules`
- Sẽ thấy 5 routing rules

### 5. Kiểm Tra Prompt Templates

- Vào `/admin/prompts`
- Sẽ thấy 7 prompt templates (tiếng Việt)

### 6. Test Sandbox

- Vào `/admin/test-sandbox`
- Test với message: "Tôi còn bao nhiêu ngày phép?"
- Sẽ thấy routing result với trace

---

## 🔧 Customize Data

Nếu muốn thay đổi data, edit file:

```
bot/backend/scripts/seed_admin_data.py
```

### Thêm Pattern Rule Mới

```python
pattern_rules.append({
    "rule_name": "Your Rule Name",
    "pattern_regex": r"your regex pattern",
    "pattern_flags": "IGNORECASE",
    "target_domain": "your_domain",
    "target_intent": "your_intent",
    "intent_type": "OPERATION",
    "priority": 100,
    "description": "Your description",
})
```

### Thêm Keyword Hint Mới

```python
keyword_hints.append({
    "rule_name": "Your Domain Keywords",
    "domain": "your_domain",
    "keywords": {
        "keyword1": 0.9,
        "keyword2": 0.8,
    },
    "description": "Your description",
})
```

---

## 🗑️ Xóa Data (Nếu Cần)

### Xóa Tất Cả Config Data

```sql
-- Connect to PostgreSQL
DELETE FROM config_audit_logs;
DELETE FROM prompt_templates;
DELETE FROM routing_rules;
DELETE FROM keyword_hints;
DELETE FROM pattern_rules;
```

### Xóa Admin User

```sql
DELETE FROM admin_users WHERE email = 'admin@example.com';
```
script clean
```
docker exec -it bot_backend python -m backend.scripts.seed_admin_data --clean
```
---

## 📊 Sample Queries Để Test (Tiếng Việt)

Sau khi seed data, test với các queries sau:

### HR Domain
- "Tôi còn bao nhiêu ngày phép?"
- "Mình đang có mấy ngày nghỉ?"
- "Xin nghỉ phép từ ngày 1/1 đến 5/1"
- "Tạo đơn nghỉ phép"
- "Duyệt đơn nghỉ phép số 123"
- "Lương tháng này bao nhiêu?"
- "Bảng lương tháng 12"

### Catalog Domain
- "Tìm sản phẩm laptop"
- "Mua điện thoại giá rẻ"
- "Có gì bán không?"
- "Giá của sản phẩm này bao nhiêu?"
- "Giá cả như thế nào?"

### Knowledge Domain
- "Nghỉ phép là gì?"
- "Hướng dẫn tạo đơn nghỉ phép"
- "Cách xin nghỉ phép như thế nào?"
- "Tại sao cần nghỉ phép?"

### Meta
- "Chào bạn"
- "Xin chào"
- "Chào anh"
- "Cảm ơn"
- "Cám ơn bạn"

---

## ⚠️ Lưu Ý

1. **Database Connection**: Đảm bảo database đã được migrate và running
2. **Duplicate Data**: Script sẽ skip nếu data đã tồn tại (không tạo duplicate)
3. **Admin User**: Nếu admin user đã tồn tại, sẽ skip creation
4. **Cache**: Data mới sẽ tự động invalidate cache

---

## 🐛 Troubleshooting

### Lỗi: Database connection failed
```bash
# Kiểm tra database đang running
# Kiểm tra DATABASE_URL trong .env
```

### Lỗi: Admin user already exists
```
✅ Đây là behavior bình thường - script sẽ skip nếu user đã tồn tại
```

### Lỗi: Foreign key constraint
```
# Đảm bảo đã chạy migrations
alembic upgrade head
```

---

## 📚 Related Files

- `backend/scripts/seed_admin_data.py` - Seed script
- `backend/domain/admin/admin_config_service.py` - Config service
- `backend/infrastructure/config_repository.py` - Config repository
- `docs/ADMIN_DASHBOARD_ARCHITECTURE.md` - Architecture docs

---

**Happy Seeding! 🎉**

