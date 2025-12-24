# Infrastructure Services

Docker Compose setup cho các infrastructure services dùng chung (PostgreSQL, Redis, pgAdmin, Redis Insight).

## 🗄️ Database Architecture

### Multi-Database Setup

Infra tạo **2 database riêng biệt** trong cùng PostgreSQL instance để tránh conflict:

1. **`bot_db`** - Database cho Bot Service
   - User: `bot_user`
   - Password: `bot_pw`
   - Connection: `postgresql+asyncpg://bot_user:bot_pw@hub_postgres:5432/bot_db`

2. **`catalog_db`** - Database cho Catalog Service
   - User: `catalog_user`
   - Password: `catalog_pw`
   - Connection: `postgresql://catalog_user:catalog_pw@hub_postgres:5432/catalog_db`

### Tại sao cần tách database?

- **Tránh conflict table names**: Cả 2 service đều có thể có bảng `users`, `sessions`, etc.
- **Dễ quản lý**: Mỗi service có database riêng, dễ backup/restore độc lập
- **Bảo mật**: Có thể cấp quyền khác nhau cho từng user
- **Production-ready**: Dễ scale và tách riêng khi cần

## 🚀 Cách sử dụng

### 1. Khởi động Infrastructure

```bash
cd infra
docker-compose -f docker-compose.infra.yml up -d
```

### 2. Kiểm tra services

```bash
# Kiểm tra containers
docker-compose -f docker-compose.infra.yml ps

# Kiểm tra database đã được tạo
docker exec -it hub_postgres psql -U bot_user -d bot_db -c "\l"
```

Bạn sẽ thấy cả 2 database: `bot_db` và `catalog_db`

### 3. Kết nối từ các service khác

#### Bot Service
```env
DATABASE_URL=postgresql+asyncpg://bot_user:bot_pw@hub_postgres:5432/bot_db
```

#### Catalog Service
```env
DB_HOST=hub_postgres
DB_PORT=5432
DB_NAME=catalog_db
DB_USER=catalog_user
DB_PASSWORD=catalog_pw
DATABASE_URL=postgresql://catalog_user:catalog_pw@hub_postgres:5432/catalog_db
```

## 📊 Management Tools

- **pgAdmin**: http://localhost:5050
  - Email: `admin@pnj-hub.local`
  - Password: `admin`

- **Redis Insight**: http://localhost:8389

## 🔧 Troubleshooting

### Database chưa được tạo?

Nếu database `gsnake1102` chưa được tạo, có thể do:
1. Init script chưa chạy (chỉ chạy lần đầu khi container mới)
2. Volume đã tồn tại từ trước

**Giải pháp:**
```bash
# Xóa volume và tạo lại (CẢNH BÁO: Mất dữ liệu!)
docker-compose -f docker-compose.infra.yml down -v
docker-compose -f docker-compose.infra.yml up -d

# Hoặc tạo database thủ công
docker exec -it hub_postgres psql -U catalog_user -d postgres -c "CREATE DATABASE catalog_db;"
```

### Kiểm tra user và quyền

```bash
# Kiểm tra users
docker exec -it hub_postgres psql -U catalog_user -d postgres -c "\du"

# Kiểm tra databases
docker exec -it hub_postgres psql -U catalog_user -d postgres -c "\l"
```

## 📝 Notes

- Init script (`01_create_databases.sql`) chỉ chạy khi PostgreSQL container được tạo lần đầu
- Nếu volume đã tồn tại, init script sẽ không chạy lại
- Để chạy lại init script, cần xóa volume: `docker-compose down -v`

