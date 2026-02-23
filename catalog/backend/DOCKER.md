# 🐳 Docker Build & Deploy Guide - Catalog Backend

## 📋 Tổng quan

Backend service được containerize với Docker để dễ deploy và scale.

## 🏗️ Build Image

### Local Build

```bash
# Từ thư mục catalog/
docker-compose build backend

# Hoặc build trực tiếp
cd catalog
docker build -f backend/Dockerfile -t catalog-backend:latest .
```

### Production Build

```bash
# Build với tag version
docker build -f backend/Dockerfile -t catalog-backend:v1.0.0 .
docker tag catalog-backend:v1.0.0 catalog-backend:latest
```

## 🚀 Chạy với Docker Compose

### 1. Chuẩn bị Environment

```bash
cd catalog/backend
cp env.example .env
# Chỉnh sửa .env với các giá trị phù hợp
```

**Quan trọng cho LOCAL:**
```env
# Database - Connect vào infra
DB_HOST=hub_postgres
DB_PORT=5432
DB_NAME=catalog_db
DB_USER=catalog_user
DB_PASSWORD=catalog_pw
DATABASE_URL=postgresql://catalog_user:catalog_pw@hub_postgres:5432/catalog_db

# Redis - Connect vào infra
REDIS_HOST=hub_redis
REDIS_PORT=6379

# JWT Secret (phải giống với Bot service)
JWT_SECRET=your-jwt-secret-key-minimum-32-characters
```

### 2. Khởi động Infrastructure

```bash
# Đảm bảo infra đã chạy
cd ../../infra
docker-compose -f docker-compose.infra.yml up -d
```

### 3. Chạy Backend Service

```bash
# Từ thư mục catalog/
docker-compose up -d backend

# Xem logs
docker-compose logs -f backend

# Kiểm tra health
curl http://localhost:3001/health
```

## 📦 Image Structure

```
catalog-backend:latest
├── Node.js 18 Alpine
├── Production dependencies only
├── Built TypeScript code (dist/)
├── Shared types package
├── Migration files
└── Uploads directory (mounted volume)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PORT` | Server port | No | 3001 |
| `NODE_ENV` | Environment | No | production |
| `JWT_SECRET` | JWT secret key | Yes | - |
| `DB_HOST` | Database host | Yes | - |
| `DB_PORT` | Database port | Yes | 5432 |
| `DB_NAME` | Database name | Yes | - |
| `DB_USER` | Database user | Yes | - |
| `DB_PASSWORD` | Database password | Yes | - |
| `REDIS_HOST` | Redis host | Yes | - |
| `REDIS_PORT` | Redis port | Yes | 6379 |

### Volumes

- `./backend/uploads:/app/uploads` - Uploads directory (persist files)

### Ports

- `3001:3001` - API server port

## 🧪 Testing

### Health Check

```bash
curl http://localhost:3001/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "database": "connected"
}
```

### Test API

```bash
# Test với authentication
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

## 🐛 Troubleshooting

### Container không start

```bash
# Xem logs
docker-compose logs backend

# Kiểm tra environment variables
docker-compose exec backend env | grep DB_
```

### Database connection failed

**Nguyên nhân:**
- Database chưa sẵn sàng
- Network không connect được
- Credentials sai

**Giải pháp:**
```bash
# Kiểm tra infra services
docker ps | grep hub_postgres

# Test connection từ container
docker-compose exec backend sh
# Trong container:
nc -zv hub_postgres 5432
```

### Build failed

**Nguyên nhân:**
- Dependencies không install được
- TypeScript build errors
- Shared types chưa build

**Giải pháp:**
```bash
# Build lại từ đầu
docker-compose build --no-cache backend

# Kiểm tra build logs
docker-compose build backend 2>&1 | tee build.log
```

## 📝 Production Deployment

### 1. Build và Push Image

```bash
# Build
docker build -f backend/Dockerfile -t registry.example.com/catalog-backend:v1.0.0 .

# Push
docker push registry.example.com/catalog-backend:v1.0.0
```

### 2. Deploy với Docker Compose

```bash
# Update image tag trong docker-compose.yml
# Chạy production profile
docker-compose --profile production up -d
```

### 3. Run Migrations

```bash
# Chạy migrations trong container
docker-compose exec backend npm run migrate
```

## 🔒 Security Notes

1. **JWT Secret**: Phải dùng secret mạnh (ít nhất 32 ký tự)
2. **Database Password**: Không commit vào code
3. **Environment Variables**: Dùng secrets management trong production
4. **Image Scanning**: Scan image trước khi deploy

## 📚 Related Files

- `Dockerfile` - Build configuration
- `.dockerignore` - Files to exclude from build
- `docker-compose.yml` - Service definition
- `env.example` - Environment variables template

