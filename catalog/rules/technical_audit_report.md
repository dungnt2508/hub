# Kiểm toán Kỹ thuật - gsnake1102 Marketplace Platform

## 1. KIẾN TRÚC & THIẾT KẾ

### ❌ Lỗi 1.1: Thiếu Separation of Concerns trong Repository Layer
**Vị trí**: `backend/src/repositories/*.repository.ts`  
**Vấn đề**: Repositories trộn lẫn logic xử lý data mapping với SQL queries, làm code khó maintain  
**Rủi ro**: Technical debt cao, khó test, khó mở rộng

**Sửa**:
```typescript
// Tách riêng SQL builder và data mapper
// File: backend/src/repositories/base/query-builder.ts
export class QueryBuilder {
    buildSelect(table: string, columns: string[], conditions: WhereClause[]): string
    buildInsert(table: string, data: Record<string, any>): string
}

// File: backend/src/repositories/base/data-mapper.ts
export class DataMapper<T> {
    mapRow(row: any): T
    mapRows(rows: any[]): T[]
}
```
**Lý do**: Single Responsibility Principle - mỗi class chỉ làm 1 việc, dễ test và maintain

---

### ❌ Lỗi 1.2: Folder `application/use-cases/` và `models/` deprecated nhưng chưa xóa
**Vị trí**: `backend/src/application/`, `backend/src/models/`  
**Vấn đề**: Dead code gây confusion cho developers mới  
**Rủi ro**: Waste time, có thể dùng nhầm code cũ

**Sửa**: Xóa hoàn toàn 2 folder này
```bash
rm -rf backend/src/application/use-cases
rm -rf backend/src/models
```
**Lý do**: Clean codebase, tránh confusion

---

###❌ Lỗi 1.3: Không có API Versioning
**Vị trí**: `backend/src/index.ts` (routes registration)  
**Vấn đề**: Tất cả routes đều `/api/*`, không có version (vd: `/api/v1/*`)  
**Rủi ro**: Breaking changes sẽ phá vỡ clients cũ, không rollback được

**Sửa**:
```typescript
// backend/src/index.ts
await fastify.register(authRoutes, { prefix: '/api/v1/auth' });
await fastify.register(productRoutes, { prefix: '/api/v1/products' });
// Khi có breaking change, tạo v2
await fastify.register(productsV2Routes, { prefix: '/api/v2/products' });
```
**Lý do**: Backwards compatibility, progressive migration

---

### ⚠️ Lỗi 1.4: Tight coupling với n8n
**Vị trí**: `backend/src/services/*.service.ts` (gọi trực tiếp n8n API)  
**Vấn đề**: Direct HTTP call tới n8n, không có queue/retry mechanism  
**Rủi ro**: Nếu n8n down, request fail ngay lập tức, không retry

**Sửa**: Implement message queue (Bull/BullMQ + Redis đã có sẵn)
```typescript
// backend/src/services/workflow-queue.service.ts
import Bull from 'bull';
import { REDIS_HOST, REDIS_PORT } from '../config/env';

export const workflowQueue = new Bull('n8n-workflows', {
    redis: { host: REDIS_HOST, port: REDIS_PORT }
});

workflowQueue.process(async (job) => {
    const { workflowId, payload } = job.data;
    return await n8nClient.triggerWorkflow(workflowId, payload);
});

// Retry config: 3 lần, exponential backoff
workflowQueue.defaultJobOptions = {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 }
};
```
**Lý do**: Resilience, retry logic, decoupling

---

## 2. BẢO MẬT

### 🔴 CRITICAL 2.1: Weak JWT Secret trong .env.example
**Vị trí**: `backend/.env.example` line 4  
**Vấn đề**:
```env
JWT_SECRET=your-secret-key-change-in-production  # WEAK! Chỉ 38 ký tự
```
**Rủi ro**: CRITICAL - JWT có thể bị brute-force, attacker forge tokens

**Sửa**:
```env
# Generate bằng: openssl rand -base64 64
JWT_SECRET=YourSecretMustBeAtLeast512BitsLongForHS512OrBetterUseRS256WithPrivateKeyInstead1234567890
```
Và validate trong `env.ts`:
```typescript
JWT_SECRET: z.string().min(64, 'JWT_SECRET phải >= 64 ký tự (512 bits)'),
```
**Lý do**: HS256 cần min 256 bits (32 bytes base64 = ~43 chars), nên dùng 512 bits an toàn hơn

---

### 🔴 CRITICAL 2.2: Leak Sensitive Data qua console.log trong Production
**Vị trí**: `backend/src/services/auth.service.ts` lines 182-183  
**Vấn đề**:
```typescript
console.info('[googleCallback] redirectUri:', authConfig.google.redirectUri);
console.info('[googleCallback] clientId:', authConfig.google.clientId);
```
**Rủi ro**: CRITICAL - Logs production chứa sensitive config, nếu logs bị leak = attacker có OAuth credentials

**Sửa**: Xóa hoàn toàn hoặc dùng proper logger với log levels
```typescript
// Xóa hẳn, hoặc:
fastify.log.debug({ redirectUri: authConfig.google.redirectUri }, 'Google OAuth callback');
// Debug level không xuất hiện trong production logs
```
**Lý do**: OWASP A09:2021 - Security Logging Failures

---

### 🔴 CRITICAL 2.3: SQL Injection Potential (Partial)
**Vị trí**: `backend/src/repositories/product.repository.ts`  
**Vấn đề**: Tuy dùng parameterized queries `$1, $2` nhưng động building có thể có lỗ hổng khi build ORDER BY, WHERE từ user input

**Rủi ro**: SQL Injection nếu sort_by/filter fields không được whitelist

**Sửa**: Whitelist tất cả dynamic query parts
```typescript
const ALLOWED_SORT_FIELDS = ['created_at', 'rating', 'downloads', 'title'];
if (!ALLOWED_SORT_FIELDS.includes(filters.sort_by)) {
    throw new Error('Invalid sort field');
}
const query = `SELECT * FROM products ORDER BY ${filters.sort_by}`;
```
**Lý do**: OWASP A03:2021 - Injection

---

### ❌ Lỗi 2.4: Không có Rate Limiting cho file upload
**Vị trí**: `backend/src/routes/product.routes.ts` (upload endpoints)  
**Vấn đề**: Rate limiting chỉ áp dụng global, không có riêng cho file upload  
**Rủi ro**: DoS bằng cách upload files lớn liên tục, cạn kiệt disk/bandwidth

**Sửa**:
```typescript
// backend/src/routes/product.routes.ts
fastify.post('/upload', {
    preHandler: [authenticate, requireSeller],
    config: {
        rateLimit: { max: 10, timeWindow: '15 minutes' } // Per-seller
    },
    handler: uploadHandler
});
```
**Lý do**: OWASP A05:2021 - Security Misconfiguration (rate limiting)

---

### ❌ Lỗi 2.5: Không validate file type/size trong upload
**Vị trí**: `backend/src/routes/product.routes.ts`  
**Vấn đề**: Multipart upload không kiểm tra MIME type, file size  
**Rủi ro**: Upload file độc hại (.exe, .sh), cạn kiệt disk

**Sửa**:
```typescript
await fastify.register(multipart, {
    limits: {
        fileSize: 50 * 1024 * 1024, // 50MB
        files: 5
    },
    onFile: async (part) => {
        const allowedMimes = ['application/json', 'image/jpeg', 'image/png'];
        if (!allowedMimes.includes(part.mimetype)) {
            throw new Error('Invalid file type');
        }
    }
});
```
**Lý do**: OWASP A04:2021 - Insecure Design

---

### ❌ Lỗi 2.6: CORS quá lỏng trong production
**Vị trí**: `backend/src/index.ts` lines 49-58  
**Vấn đề**:
```typescript
origin: process.env.NODE_ENV === 'development' 
    ? true // NGUY HIỂM: Allow ALL origins
    : FRONTEND_URL,
```
**Rủi ro**: Trong dev, bất kỳ origin nào cũng call được API, dễ bị CSRF

**Sửa**: Whitelist origins ngay cả trong dev
```typescript
origin: (origin, callback) => {
    const whitelist = ['http://localhost:3000', 'http://localhost:3001', FRONTEND_URL];
    if (!origin || whitelist.includes(origin)) {
        callback(null, true);
    } else {
        callback(new Error('Not allowed by CORS'));
    }
},
```
**Lý do**: OWASP A01:2021 - Broken Access Control

---

### ❌ Lỗi 2.7: Thiếu CSRF protection
**Vị trí**: Toàn bộ backend  
**Vấn đề**: Không có CSRF token cho state-changing operations  
**Rủi ro**: Attacker có thể trick user vào site độc hại để gọi API thay họ

**Sửa**: Implement CSRF tokens cho non-GET requests
```typescript
import csrf from '@fastify/csrf-protection';
await fastify.register(csrf);

// Trong cookies gửi CSRF token
fastify.post('/api/products', {
    preHandler: fastify.csrfProtection,
    handler: createProduct
});
```
**Lý do**: OWASP A01:2021 - Broken Access Control

---

### ❌ Lỗi 2.8: Không có input sanitization
**Vị trí**: Toàn bộ services/repositories  
**Vấn đề**: Input từ user không được sanitize trước khi lưu DB (XSS stored)  
**Rủi ro**: Stored XSS - attacker inject `<script>` vào product.title/description

**Sửa**:
```typescript
// backend/src/utils/sanitize.ts
import validator from 'validator';

export function sanitizeHtml(input: string): string {
    return validator.escape(input); // Convert <script> -> &lt;script&gt;
}

// Trong product.service.ts
async createProduct(data: CreateProductInput) {
    data.title = sanitizeHtml(data.title);
    data.description = sanitizeHtml(data.description);
    // ...
}
```
**Lý do**: OWASP A03:2021 - Injection (XSS)

---

### ⚠️ Lỗi 2.9: JWT không có refresh token mechanism
**Vị trí**: `backend/src/services/auth.service.ts`  
**Vấn đề**: Chỉ có access token, expiresIn = 7 days (quá dài)  
**Rủi ro**: Token bị đánh cắp có thể dùng 7 ngày, không revoke được

**Sửa**: Implement refresh token + short-lived access token
```typescript
// Access token: 15 phút
const accessToken = jwt.sign(payload, secret, { expiresIn: '15m' });
// Refresh token: 7 ngày, lưu DB để revoke được
const refreshToken = jwt.sign({ userId: user.id, type: 'refresh' }, secret, { expiresIn: '7d' });
await redisClient.set(`refresh:${user.id}`, refreshToken, 'EX', 7*24*3600);
return { accessToken, refreshToken };
```
**Lý do**: Best practice - short-lived tokens + revokable refresh tokens

---

## 3. HIỆU NĂNG

### ❌ Lỗi 3.1: N+1 Query Problem
**Vị trí**: `backend/src/services/product.service.ts` method `getProductWithDetails`  
**Vấn đề**:
```typescript
// Load từng product -> loop artifacts -> loop workflows = N+1
result.artifacts = await artifactRepository.findByProductId(id);
result.workflowDetails = await workflowRepository.findByProductId(id);
```
**Rủi ro**: 100 products = 300 queries thay vì 3 queries

**Sửa**: Batch loading hoặc JOIN
```typescript
// Sử dụng SQL JOIN
SELECT p.*, 
    json_agg(DISTINCT a.*) as artifacts,
    json_agg(DISTINCT w.*) as workflow_details
FROM products p
LEFT JOIN product_artifacts a ON p.id = a.product_id
LEFT JOIN product_workflows w ON p.id = w.product_id
WHERE p.id = ANY($1)
GROUP BY p.id
```
**Lý do**: Giảm DB roundtrips từ O(N) xuống O(1)

---

### ❌ Lỗi 3.2: Không có database indexes
**Vị trí**: `backend/migrations/*.sql`  
**Vấn đề**: Không thấy indexes nào ngoài PRIMARY KEY  
**Rủi ro**: Queries chậm khi data lớn (vd: search products, filter by seller_id)

**Sửa**: Thêm migration tạo indexes
```sql
-- backend/migrations/012_add_indexes.sql
CREATE INDEX idx_products_seller_id ON products(seller_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_review_status ON products(review_status);
CREATE INDEX idx_products_type ON products(type);
CREATE INDEX idx_products_created_at ON products(created_at DESC);
CREATE INDEX idx_products_rating ON products(rating DESC);
CREATE INDEX idx_users_email ON users(email); -- Nếu chưa có
CREATE INDEX idx_users_role ON users(role);
```
**Lý do**: Tăng tốc search/filter queries hàng trăm lần

---

### ❌ Lỗi 3.3: Không có DB connection pool config tối ưu
**Vị trí**: `backend/src/config/database.ts` line 10  
**Vấn đề**:
```typescript
max: 20, // Hardcoded, không tuỳ chỉnh theo env
idleTimeoutMillis: 30000, // 30s có thể quá ngắn
```
**Rủi ro**: High load environments có thể hết connection pool, hoặc waste connections

**Sửa**:
```typescript
const pool = new Pool({
    max: parseInt(process.env.DB_POOL_SIZE || '20'),
    min: parseInt(process.env.DB_POOL_MIN || '5'),
    idleTimeoutMillis: 60000, // 1 phút
    connectionTimeoutMillis: 2000,
    statement_timeout: 30000, // Kill slow queries sau 30s
    query_timeout: 30000
});
```
**Lý do**: Production tuning, tránh connection exhaustion

---

### ❌ Lỗi 3.4: Không có response caching
**Vị trí**: Frontend `src/shared/api/client.ts`, Backend routes  
**Vấn đề**: Mỗi request đều hit backend/DB, không cache  
**Rủi ro**: Slow response time, DB overload với public data (product list)

**Sửa**:
```typescript
// Backend: Cache public products trong Redis
async getProducts(filters) {
    const cacheKey = `products:${JSON.stringify(filters)}`;
    const cached = await redisClient.get(cacheKey);
    if (cached) return JSON.parse(cached);
    
    const result = await productRepository.findMany(filters);
    await redisClient.setex(cacheKey, 300, JSON.stringify(result)); // 5 phút
    return result;
}

// Frontend: React Query đã dùng staleTime/cacheTime, config thêm:
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 phút
            cacheTime: 10 * 60 * 1000, // 10 phút
        }
    }
});
```
**Lý do**: Giảm DB load, tăng response time

---

### ❌ Lỗi 3.5: Không có pagination defaults
**Vị trí**: `backend/src/repositories/product.repository.ts`  
**Vấn đề**: Nếu không truyền `limit`, có thể fetch toàn bộ DB (vd: 10,000 products)  
**Rủi ro**: OOM, slow queries, bandwidth waste

**Sửa**:
```typescript
async findMany(filters: ProductQueryFilters) {
    const limit = Math.min(filters.limit || 50, 100); // Default 50, max 100
    const offset = filters.offset || 0;
    // ...
}
```
**Lý do**: Protect DB từ unbounded queries

---

## 4. DỮ LIỆU & DATABASE

### ❌ Lỗi 4.1: Thiếu down migrations cho 3 migrations mới nhất
**Vị trí**: `backend/migrations/down/` folder  
**Vấn đề**: Chỉ có down migrations tới 008, thiếu 009, 010, 011  
**Rủi ro**: Không rollback được nếu deploy fail

**Sửa**: Tạo down migrations cho 009, 010, 011
```sql
-- backend/migrations/down/011_down_phase1_product_artifacts_and_workflows.sql
DROP TABLE IF EXISTS product_workflows;
DROP TABLE IF EXISTS product_artifacts;
-- ... reverse tất cả changes trong 011_up
```
**Lý do**: Database rollback safety, CI/CD requirement

---

### ❌ Lỗi 4.2: Không có database constraints đầy đủ
**Vị trí**: Migration files  
**Vấn đề**: Thiếu CHECK constraints cho business rules (vd: price > 0 nếu is_free=false)  
**Rủi ro**: Data integrity issues, bad data vào DB

**Sửa**:
```sql
-- Trong migration 007 hoặc tạo migration mới
ALTER TABLE products ADD CONSTRAINT price_check 
CHECK (
    (is_free = TRUE AND price IS NULL) OR 
    (is_free = FALSE AND price > 0)
);

ALTER TABLE products ADD CONSTRAINT valid_status 
CHECK (status IN ('draft', 'published', 'archived'));
```
**Lý do**: Data integrity tại DB level, không rely vào application logic

---

### ❌ Lỗi 4.3: Không có unique constraints
**Vị trí**: `users` table  
**Vấn đề**: `email` không có UNIQUE constraint (chỉ rely vào app logic)  
**Rủi ro**: Race condition -> duplicate emails vào DB

**Sửa**:
```sql
-- Migration
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
```
**Lý do**: Race condition protection

---

### ❌ Lỗi 4.4: Soft delete không được implement
**Vị trí**: Repositories dùng `DELETE FROM`  
**Vấn đề**: Hard delete = mất data permanently, không audit được  
**Rủi ro**: Compliance issues (GDPR audit logs), không restore được

**Sửa**: Thêm `deleted_at` column + soft delete
```sql
ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP NULL;
CREATE INDEX idx_products_deleted_at ON products(deleted_at);

-- Repository
async delete(id: string): Promise<boolean> {
    const result = await pool.query(
        'UPDATE products SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL',
        [id]
    );
    return result.rowCount > 0;
}
```
**Lý do**: GDPR compliance, audit trails, data recovery

---

### ❌ Lỗi 4.5: Thiếu database backups automation
**Vị trí**: Infrastructure (không có trong code)  
**Vấn đề**: Không thấy backup strategy  
**Rủi ro**: Data loss nếu DB crash

**Sửa**: Setup pg_dump cron job
```bash
# Trong docker-compose.yml hoặc cron
0 2 * * * pg_dump -h localhost -U gsnake1102_user gsnake1102 | gzip > /backups/gsnake_$(date +\%Y\%m\%d).sql.gz
# Retention: xóa backups > 30 ngày
```
**Lý do**: Disaster recovery, business continuity

---

## 5. CI/CD

### 🔴 CRITICAL 5.1: Không có CI/CD pipeline
**Vị trí**: Project root - thiếu `.github/workflows/` hoặc `.gitlab-ci.yml`  
**Vấn đề**: Deploy manual, không có automated testing/building  
**Rủi ro**: CRITICAL - Deploy code chưa test, human errors, inconsistent deploys

**Sửa**: GitHub Actions CI/CD
```yaml
# .github/workflows/ci.yml
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run migrate
      - run: npm test
      - run: npm run build
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploy to production"
```
**Lý do**: Automation, quality gate, fast feedback

---

### ❌ Lỗi 5.2: Không có Dockerfile cho production
**Vị trí**: Project root  
**Vấn đề**: `docker-compose.yml` chỉ cho local dev (Postgres/Redis), không có Dockerfile app  
**Rủi ro**: Deploy inconsistent, "works on my machine" issues

**Sửa**:
```dockerfile
# backend/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/index.js"]
```
**Lý do**: Containerization, reproducible builds

---

### ❌ Lỗi 5.3: Không có environment-specific configs
**Vị trí**: `.env.example` chỉ có 1 file  
**Vấn đề**: Không có `.env.production.example`, `.env.staging.example`  
**Rủi ro**: Config mismatch giữa environments

**Sửa**: Tạo env files cho từng env + document differences
```
backend/
  .env.example             # Local dev
  .env.production.example  # Production (strict rate limits, real DB)
  .env.staging.example     # Staging (looser rate limits, test DB)
```
**Lý do**: Environment parity, deployment safety

---

## 6. LOGGING & MONITORING

### 🔴 CRITICAL 6.1: Sử dụng console.log thay vì structured logger
**Vị trí**: 10+ locations trong `backend/src/`  
**Vấn đề**:
```typescript
console.log('✅ n8n workflow triggered'); // Không có context, timestamp, level
console.error('Database error:', err);    // Không có request ID, user ID
```
**Rủi ro**: CRITICAL production debugging nightmare - không filter được, không search, không alert

**Sửa**: Thay bằng Fastify logger (Pino)
```typescript
// Fastify đã có Pino built-in
fastify.log.info({ articleId: article.id, workflowId: 'xxx' }, 'n8n workflow triggered');
fastify.log.error({ err, userId: request.user.userId }, 'Database query failed');

// Production logs format JSON -> ELK/Datadog có thể parse
{"level":30,"time":1702419200000,"msg":"n8n workflow triggered","articleId":"uuid"}
```
**Lý do**: Production observability, debugging efficiency

---

### ❌ Lỗi 6.2: Không có centralized logging
**Vị trí**: Infrastructure  
**Vấn đề**: Logs chỉ ở stdout container, không ship đi đâu  
**Rủi ro**: Container restart = mất logs, không search được logs cũ

**Sửa**: Ship logs tới ELK Stack hoặc Datadog
```yaml
# docker-compose.yml (nếu dùng ELK stack local)
services:
  app:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: gsnake.backend
```
**Lý do**: Log retention, searchability, alerts

---

### ❌ Lỗi 6.3: Không có monitoring/metrics
**Vị trí**: Toàn bộ app  
**Vấn đề**: Không có Prometheus metrics, APM tracing  
**Rủi ro**: Không biết app performance (response time, error rate, CPU/memory)

**Sửa**: Add Prometheus metrics
```typescript
import promClient from 'prom-client';

const httpRequestDuration = new promClient.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code']
});

fastify.addHook('onResponse', async (request, reply) => {
    httpRequestDuration.labels(
        request.method,
        request.routerPath,
        reply.statusCode.toString()
    ).observe(reply.getResponseTime() / 1000);
});

// Expose metrics endpoint
fastify.get('/metrics', async () => promClient.register.metrics());
```
**Lý do**: Observability, SLA monitoring, capacity planning

---

### ❌ Lỗi 6.4: Không có health check endpoints đầy đủ
**Vị trí**: `backend/src/index.ts` line 96  
**Vấn đề**: `/health` chỉ check DB, không check Redis, n8n connectivity  
**Rủi ro**: Load balancer nghĩ service healthy nhưng Redis/n8n die

**Sửa**:
```typescript
fastify.get('/health', async () => {
    const checks = await Promise.allSettled([
        checkDatabaseHealth(),
        checkRedisHealth(),
        checkN8nHealth()
    ]);
    const allHealthy = checks.every(c => c.status === 'fulfilled' && c.value === true);
    return {
        status: allHealthy ? 'healthy' : 'degraded',
        checks: {
            database: checks[0].status === 'fulfilled' ? checks[0].value : false,
            redis: checks[1].status === 'fulfilled' ? checks[1].value : false,
            n8n: checks[2].status === 'fulfilled' ? checks[2].value : false
        }
    };
});
```
**Lý do**: Accurate health checks, prevent cascading failures

---

### ❌ Lỗi 6.5: Không có error tracking (Sentry)
**Vị trí**: Toàn bộ app  
**Vấn đề**: Errors chỉ log ra console, không track/group/alert  
**Rủi ro**: Production errors bị bỏ qua, không biết error rate

**Sửa**:
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({ dsn: process.env.SENTRY_DSN });

// Error handler
fastify.setErrorHandler((error, request, reply) => {
    Sentry.captureException(error, {
        user: { id: request.user?.userId },
        tags: { route: request.routerPath }
    });
    // ... existing error handling
});
```
**Lý do**: Error tracking, alerting, debugging với stack traces

---

## 7. TEST COVERAGE

### 🔴 CRITICAL 7.1: 0% test coverage
**Vị trí**: Toàn bộ project  
**Vấn đề**: Không có test files nào (chỉ Jest config trong package.json)  
**Rủi ro**: CRITICAL - Mọi code changes đều có thể break production, refactor nguy hiểm

**Sửa**: Viết tests theo tầng
```typescript
// backend/src/__tests__/unit/services/product.service.test.ts
import { ProductService } from '../../../services/product.service';
import productRepository from '../../../repositories/product.repository';

jest.mock('../../../repositories/product.repository');

describe('ProductService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('createProduct', () => {
        it('should create product with default values', async () => {
            const mockProduct = { id: 'uuid', title: 'Test' };
            (productRepository.create as jest.Mock).mockResolvedValue(mockProduct);
            
            const result = await productService.createProduct({
                title: 'Test',
                description: 'Test desc',
                seller_id: 'seller-uuid',
                type: 'workflow',
                is_free: true
            });
            
            expect(result).toEqual(mockProduct);
            expect(productRepository.create).toHaveBeenCalledWith(
                expect.objectContaining({
                    status: 'draft',
                    review_status: 'pending'
                })
            );
        });
    });
});

// Integration test
// backend/src/__tests__/integration/routes/product.routes.test.ts
import Fastify from 'fastify';
import productRoutes from '../../../routes/product.routes';

describe('Product Routes', () => {
    let app: any;
    beforeAll(async () => {
        app = Fastify();
        await app.register(productRoutes);
    });

    it('GET /products returns published products', async () => {
        const response = await app.inject({
            method: 'GET',
            url: '/products'
        });
        expect(response.statusCode).toBe(200);
        expect(response.json()).toHaveProperty('data');
    });
});
```
**Lý do**: Code quality, refactoring safety, regression prevention

---

### ❌ Lỗi 7.2: Không có E2E tests
**Vị trí**: Toàn project  
**Vấn đề**: User flows không được test (register -> login -> create product -> publish)  
**Rủi ro**: Integration bugs giữa frontend-backend

**Sửa**: Playwright E2E tests
```typescript
// frontend/e2e/product-flow.spec.ts
import { test, expect } from '@playwright/test';

test('seller can create and publish product', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name=email]', 'seller@test.com');
    await page.fill('[name=password]', 'password');
    await page.click('button[type=submit]');
    
    // Create product
    await page.goto('/seller/products/new');
    await page.fill('[name=title]', 'Test Product');
    await page.fill('[name=description]', 'Test description');
    await page.click('button:has-text("Create")');
    
    // Verify
    await expect(page.locator('.success-message')).toBeVisible();
});
```
**Lý do**: User flow validation, prevent regressions

---

### ❌ Lỗi 7.3: Không có test database
**Vị trí**: Backend tests (chưa tồn tại)  
**Vấn đề**: Nếu test connect tới dev DB = pollute data  
**Rủi ro**: Tests fail vì DB state, hoặc xóa dev data

**Sửa**: Test database + migrations
```typescript
// backend/src/__tests__/setup.ts
import { Pool } from 'pg';

let testPool: Pool;

beforeAll(async () => {
    testPool = new Pool({
        host: 'localhost',
        port: 5433,
        database: 'gsnake_test',
        user: 'test_user',
        password: 'test_pw'
    });
    // Run migrations
    await runMigrations(testPool);
});

afterEach(async () => {
    // Cleanup tables
    await testPool.query('TRUNCATE users, products CASCADE');
});

afterAll(async () => {
    await testPool.end();
});
```
**Lý do**: Test isolation, reproducible tests

---

## 8. TÀI LIỆU

### ❌ Lỗi 8.1: Không có API documentation (Swagger/OpenAPI)
**Vị trí**: Toàn bộ backend  
**Vấn đề**: Developers phải đọc code để biết API endpoints  
**Rủi ro**: Onboarding chậm, frontend-backend miscommunication

**Sửa**: Add Swagger
```typescript
// backend/package.json
"dependencies": {
    "@fastify/swagger": "^8.13.0",
    "@fastify/swagger-ui": "^2.0.1"
}

// backend/src/index.ts
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';

await fastify.register(swagger, {
    swagger: {
        info: {
            title: 'gsnake1102 API',
            version: '1.0.0'
        },
        schemes: ['http', 'https'],
        consumes: ['application/json'],
        produces: ['application/json']
    }
});

await fastify.register(swaggerUi, {
    routePrefix: '/docs'
});
```
**Lý do**: Developer experience, API discoverability

---

### ❌ Lỗi 8.2: README thiếu deployment instructions
**Vị trí**: `README.md`  
**Vấn đề**: Section "Build & Deploy" chỉ nói "Not included", không hướng dẫn  
**Rủi ro**: Deploy team không biết cách deploy, errors

**Sửa**: Thêm deployment guide trong README
**Lý do**: Deployment repeatability, onboarding

---

### ❌ Lỗi 8.3: Không có CHANGELOG.md
**Vị trí**: Project root  
**Vấn đề**: Không track changes giữa versions  
**Rủi ro**: Không biết breaking changes khi upgrade

**Sửa**: Tạo CHANGELOG.md theo Keep a Changelog format
**Lý do**: Change tracking, migration guides

---

## 9. CODE STRUCTURE

### ❌ Lỗi 9.1: Magic numbers/strings rải rác
**Vị trí**: Nhiều files  
**Vấn đề**:
```typescript
// product.service.ts
if (data.title.trim().length < 3) // Magic number 3
if (data.tags.length > 10)        // Magic number 10
```

**Sửa**: Extract constants
```typescript
// backend/src/config/constants.ts
export const PRODUCT_CONSTRAINTS = {
    TITLE_MIN_LENGTH: 3,
    TITLE_MAX_LENGTH: 500,
    DESCRIPTION_MIN_LENGTH: 10,
    MAX_TAGS: 10,
    MAX_FEATURES: 20
};

// Usage
if (data.title.trim().length < PRODUCT_CONSTRAINTS.TITLE_MIN_LENGTH)
```
**Lý do**: Maintainability, single source of truth

---

### ❌ Lỗi 9.2: Duplicate logic giữa frontend-backend
**Vị trí**: Frontend services manually convert camelCase ↔ snake_case  
**Vấn đề**: Backend đã có `db-mapper.ts` nhưng frontend tự convert lại  
**Rủi ro**: Inconsistency, bugs khi thêm field mới

**Sửa**: Backend trả về camelCase, frontend không cần convert
**Lý do**: DRY principle, consistency

---

## 10. FRONTEND ISSUES

### 🔴 CRITICAL 10.1: localStorage cho tokens = XSS risk
**Vị trí**: `frontend/src/shared/api/client.ts` lines 20, 37, 52  
**Vấn đề**:
```typescript
localStorage.getItem('token'); // Vulnerable to XSS
```
**Rủi ro**: XSS attack có thể đọc tokens từ localStorage

**Sửa**: Dùng httpOnly cookies
```typescript
// Backend: Set token trong httpOnly cookie thay vì trả về
reply.setCookie('access_token', token, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 15 * 60 // 15 phút
});

// Frontend: Không cần lưu token, browser tự gửi cookie
```
**Lý do**: OWASP A03:2021 - XSS protection

---

### ❌ Lỗi 10.2: Hardcoded API URL fallback
**Vị trí**: `frontend/src/shared/api/client.ts` line 4  
**Vấn đề**:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';
```
**Rủi ro**: Production build nếu thiếu env var sẽ gọi localhost, silent failure

**Sửa**: Fail fast nếu thiếu env
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_BASE_URL) {
    throw new Error('NEXT_PUBLIC_API_URL environment variable is required');
}
```
**Lý do**: Fail fast, prevent silent errors

---

### ❌ Lỗi 10.3: Không có error boundaries
**Vị trí**: Frontend React components  
**Vấn đề**: Component crashes sẽ crash toàn bộ app  
**Rủi ro**: Bad UX, white screen

**Sửa**: Add error boundaries
```typescript
// frontend/src/components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

class ErrorBoundary extends Component<{ children: ReactNode }> {
    state = { hasError: false };
    
    static getDerivedStateFromError() {
        return { hasError: true };
    }
    
    render() {
        if (this.state.hasError) {
            return <div>Đã có lỗi xảy ra. Vui lòng tải lại trang.</div>;
        }
        return this.props.children;
    }
}
```
**Lý do**: Graceful error handling

---

## TÓM TẮT MỨC ĐỘ ƯU TIÊN

### 🔴 CRITICAL (Sửa ngay - Security & Data Loss risks)
1. JWT secret yếu (2.1)
2. Console.log leak sensitive data trong production (2.2)
3. Không có CI/CD (5.1)
4. console.log thay vì structured logger (6.1)
5. 0% test coverage (7.1)
6. localStorage tokens = XSS risk (10.1)

### ⚠️ HIGH (Sửa trong sprint hiện tại)
1. SQL injection potential (2.3)
2. CORS quá lỏng (2.6)
3. Thiếu input sanitization (2.8)
4. N+1 queries (3.1)
5. Không có DB indexes (3.2)
6. Thiếu down migrations (4.1)
7. Không có Dockerfile production (5.2)

### ⚙️ MEDIUM (Sửa trong 1-2 sprints tới)
1. Dead code folders (1.2)
2. Không có API versioning (1.3)
3. Rate limiting cho upload (2.4)
4. File upload validation (2.5)
5. Connection pool config (3.3)
6. Thiếu DB constraints (4.2)
7. Không có monitoring (6.3)
8. Không có Swagger docs (8.1)

### 📝 LOW (Technical debt, sửa khi rảnh)
1. Separation of concerns (1.1)
2. Soft delete (4.4)
3. Magic numbers (9.1)
4. Duplicate logic frontend-backend (9.2)

---

## KHUYẾN NGHỊ TỔNG QUAN

1. **Ngay lập tức**: Fix 6 CRITICAL issues (tuần này)
2. **Sprint tiếp theo**: Implement CI/CD + tests + security hardening
3. **Roadmap 3 tháng**:
   - Tháng 1: Security + Testing (coverage >= 70%)
   - Tháng 2: Performance (caching, indexes, monitoring)
   - Tháng 3: DevOps (IaC, backups, DR plan)

4. **Quy trình mới**:
   - Mọi PR phải có tests
   - Security scan tự động (Snyk/SonarQube)
   - Code review mandatory
   - Staging environment deploy trước production

**Tổng số vấn đề**: 50+ issues  
**Estimate fix effort**: ~6-8 sprints (3-4 tháng) để đạt production-ready standard
