# I. Infrastructure Layer (Outermost – Tech)
- Đây là nơi duy nhất được chứa kỹ thuật:
```
    FastAPI / NestJS
    PostgreSQL
    Redis
    Kafka/RabbitMQ
    Azure Blob
    Grafana
    Docker/K8s
    Logging (Loki/Elastic)
    Secrets (Vault/KeyVault)
```
- Không một dòng nghiệp vụ nằm ở đây.
# II. Giải thích thêm
- Infrastructure Layer là đáy hệ thống. Chỉ chứa kỹ thuật. Không chứa nghiệp vụ. Không chứa điều phối. Không chứa rule. Không biết domain tồn tại như thế nào, chỉ phục vụ domain qua interface ở Application Layer.

## Nội dung hạ tầng:
### 1.Database implementation
    - Repository interface ở Application Layer bắt buộc được implement ở đây.
    - SQL, ORM, migration, schema, transaction manager nằm đây.
    - Domain không biết Postgres hay SQL Server.
    - Application chỉ gọi ITicketRepository.
    - Thực thi là TicketRepositoryPostgresImpl nằm trong hạ tầng.

### 2.External API client
    - SAP, SharePoint, Graph API, n8n API, Email Gateway.
    - Tất cả HTTP client, retry, timeout, token refresh nằm tại đây.
    - Domain không được gọi HTTP.
    - Application chỉ gọi port interface.
    - Hạ tầng implement port này bằng HTTP thật.
### 3.Message Broker
    - Kafka, RabbitMQ.
    - Publisher và subscriber nằm ở đây.
    - Domain chỉ phát Domain Event (object trong bộ nhớ).
    - Hạ tầng publish ra broker.
    - Không đưa Kafka logic vào domain hoặc application.
### 4.Cache Layer
    - Redis, Memcached.
    - Cache adapter nằm đây.
    - Use-case chỉ gọi ICachePort.get() hoặc ICachePort.set().
    - Domain không biết cache là gì.
### 5.File Storage
    - S3, Azure Blob, Minio.
    - Upload/download, presigned URL nằm ở đây.
    - Application chỉ gọi port IFileStoragePort.
    - Domain không được động vào file.

### 6.LLM Client / Embedding Engine
    - OpenAI, Azure OpenAI, local model, pgvector.
    - Tất cả model config, embedding, RAG pipeline nằm ở đây.
    - Application chỉ gọi ILlmPort.
    - Domain không xử lý văn bản tự nhiên.
### 7.Logging / Observability / Metrics
    - Prometheus, Loki, OpenTelemetry.
    - Không đặt log của hạ tầng vào domain.
    - Hạ tầng log mọi thứ kỹ thuật, không log logic nghiệp vụ.

### 8.Security / Secrets
    - JWT signing, API Key encryption, KeyVault/Vault.
    - Domain không bao giờ chứa secret hoặc key.
    - Tất cả nằm tại hạ tầng.
### 9.Framework Binding
    - FastAPI, NestJS, Express, scheduling, cron, background jobs.
    - Domain không được import framework.

## Nguyên tắc:
    - Hạ tầng không đẩy logic nghiệp vụ vào.
    - Hạ tầng implement các port do Application Layer định nghĩa.
    - Domain không phụ thuộc hạ tầng.
    - Hạ tầng phụ thuộc domain thông qua interface.
    - Thay đổi công nghệ không phá domain.
    - Hạ tầng chỉ là công cụ. Domain mới là hệ thống.