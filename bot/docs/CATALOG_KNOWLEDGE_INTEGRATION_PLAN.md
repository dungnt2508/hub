# 📚 Plan Tích Hợp Knowledge Base Catalog vào Bot Service

**Mục tiêu:** Bot service có thể học và sử dụng knowledge base (products) từ catalog service để trả lời câu hỏi về sản phẩm, workflow, và tools.

**Ngày tạo:** 2025-01-XX  
**Status:** 📋 Planning

---

## 🎯 Tổng Quan

### Hiện Trạng

**Bot Service:**
- ✅ Multi-tenant architecture đã hoàn thành (Phase 1)
- ✅ Knowledge engine framework (`HRKnowledgeEngine`) nhưng chưa implement đầy đủ
- ✅ AI Provider với embedding và chat capabilities
- ✅ Router orchestrator để route messages đến domain phù hợp
- ❌ Chưa có knowledge base cho catalog domain
- ❌ Chưa có vector store để lưu trữ embeddings
- ❌ Chưa có RAG pipeline hoàn chỉnh

**Catalog Service:**
- ✅ Products table với đầy đủ metadata (title, description, tags, features, etc.)
- ✅ Full-text search indexes
- ✅ API endpoints: `GET /api/products` với filters
- ✅ Chat service với product recommendation (nhưng chỉ dùng LLM, chưa có vector search)

### Mục Tiêu

1. **Bot service có thể query knowledge base của catalog**
   - Tìm kiếm products theo semantic similarity
   - Trả lời câu hỏi về products, workflows, tools
   - Recommend products dựa trên user query

2. **Knowledge base được sync từ catalog**
   - Tự động sync products từ catalog service
   - Update khi có products mới/cập nhật
   - Tenant isolation (mỗi tenant có knowledge base riêng)

3. **RAG Pipeline hoàn chỉnh**
   - Embedding generation cho products
   - Vector store với tenant isolation
   - Retrieval + Generation với citations

---

## 🏗️ Kiến Trúc

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Catalog Service                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Products Database (PostgreSQL)                     │   │
│  │  - products table                                   │   │
│  │  - Full-text search indexes                         │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│                     │ API: GET /api/products                │
│                     │ (with filters, pagination)            │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      │ Webhook / Sync API
                      │
┌─────────────────────▼────────────────────────────────────────┐
│                    Bot Service                                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Catalog Knowledge Sync Service                     │   │
│  │  - Fetch products from catalog API                  │   │
│  │  - Generate embeddings                             │   │
│  │  - Store in vector DB                              │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  Vector Store (Qdrant/Pinecone/Weaviate)           │   │
│  │  - Collection per tenant                            │   │
│  │  - Product embeddings                               │   │
│  │  - Metadata filtering (tenant_id)                   │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  Catalog Knowledge Engine                            │   │
│  │  - RAG Pipeline                                      │   │
│  │  - Semantic search                                  │   │
│  │  - Answer generation                                │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  Router Orchestrator                                 │   │
│  │  - Route to catalog domain                          │   │
│  │  - Call Catalog Knowledge Engine                    │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. Knowledge Sync (Initial/Periodic)**
```
Catalog Service → Bot Service
  GET /api/products?status=published&review_status=approved
    ↓
  Bot Service: CatalogKnowledgeSyncService
    ↓
  Generate embeddings (AI Provider)
    ↓
  Store in Vector DB (tenant-scoped)
```

**2. Query Flow (Runtime)**
```
User: "Tôi cần workflow tự động gửi email"
    ↓
Router Orchestrator → Route to "catalog" domain
    ↓
Catalog Knowledge Engine
    ↓
1. Generate query embedding
2. Vector search (semantic similarity)
3. Retrieve top-K products
4. Generate answer with LLM (RAG)
5. Return answer + citations
```

---

## 📋 Implementation Plan

### Phase 1: Vector Store Setup & Infrastructure

**Mục tiêu:** Setup vector database và infrastructure cần thiết

#### 1.1 Chọn Vector Database

**Options:**
- **Qdrant** (Recommended): Self-hosted, open-source, good performance
- **Pinecone**: Managed service, easy setup
- **Weaviate**: Self-hosted, good for multi-tenant

**Decision:** Qdrant (self-hosted, cost-effective, good tenant isolation)

#### 1.2 Infrastructure Setup

**Files to create:**

1. **`bot/backend/infrastructure/vector_store.py`**
   ```python
   class VectorStore:
       async def create_collection(tenant_id: str)
       async def upsert_vectors(tenant_id: str, vectors: List[Vector])
       async def search(tenant_id: str, query_vector: List[float], top_k: int)
       async def delete_collection(tenant_id: str)
   ```

2. **`bot/backend/infrastructure/qdrant_client.py`**
   ```python
   class QdrantClient:
       # Wrapper for Qdrant Python client
       # Tenant isolation via collection names: "tenant_{tenant_id}_products"
   ```

3. **Update `bot/docker-compose.yml`**
   ```yaml
   qdrant:
     image: qdrant/qdrant:latest
     ports:
       - "6333:6333"
     volumes:
       - qdrant_data:/qdrant/storage
   ```

#### 1.3 Configuration

**Update `bot/backend/shared/config.py`:**
```python
# Vector Store
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
VECTOR_DIMENSION = 1536  # OpenAI embedding dimension
```

**Deliverables:**
- ✅ Vector store client implementation
- ✅ Docker compose với Qdrant
- ✅ Configuration variables
- ✅ Unit tests cho vector operations

**Timeline:** 2-3 days

---

### Phase 2: Catalog Knowledge Sync Service

**Mục tiêu:** Sync products từ catalog service vào vector store

#### 2.1 Catalog API Client

**File: `bot/backend/infrastructure/catalog_client.py`**
```python
class CatalogClient:
    async def get_products(
        tenant_id: str,
        status: str = "published",
        limit: int = 1000,
        offset: int = 0
    ) -> List[Product]
    
    async def get_product(product_id: str) -> Product
```

**Features:**
- HTTP client với retry logic
- Authentication (API key từ tenant config)
- Pagination support
- Error handling

#### 2.2 Knowledge Sync Service

**File: `bot/backend/knowledge/catalog_knowledge_sync.py`**
```python
class CatalogKnowledgeSyncService:
    async def sync_tenant_products(tenant_id: str) -> SyncResult
    async def sync_product(tenant_id: str, product: Product) -> bool
    async def delete_product(tenant_id: str, product_id: str) -> bool
    async def get_sync_status(tenant_id: str) -> SyncStatus
```

**Sync Process:**
1. Fetch products from catalog API
2. For each product:
   - Generate text representation (title + description + tags + features)
   - Generate embedding
   - Store in vector DB with metadata (product_id, tenant_id, etc.)
3. Track sync status (last_sync_at, product_count)

#### 2.3 Product Text Representation

**Strategy:**
```python
def build_product_text(product: Product) -> str:
    """
    Build searchable text from product data.
    
    Format:
    Title: {title}
    Description: {description}
    Tags: {tags.join(', ')}
    Features: {features.join(', ')}
    Type: {type}
    """
```

#### 2.4 Database Schema (Sync Tracking)

**Migration: `bot/backend/alembic_migrations/002_add_knowledge_sync_tables.py`**
```sql
CREATE TABLE knowledge_sync_status (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
    last_sync_at TIMESTAMP,
    product_count INTEGER DEFAULT 0,
    sync_status VARCHAR(50), -- 'syncing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_products (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    product_id UUID, -- Reference to catalog product
    vector_id TEXT, -- Qdrant vector ID
    title TEXT,
    description TEXT,
    synced_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, product_id)
);
```

**Deliverables:**
- ✅ Catalog API client
- ✅ Knowledge sync service
- ✅ Database schema cho sync tracking
- ✅ CLI command để sync manually
- ✅ Unit tests

**Timeline:** 3-4 days

# Sync knowledge base cho một tenant
python -m backend.scripts.sync_catalog_knowledge --tenant-id <tenant_id>

# List tất cả tenants
python -m backend.scripts.sync_catalog_knowledge --list-tenants

---

### Phase 3: Catalog Knowledge Engine

**Mục tiêu:** Implement RAG pipeline cho catalog domain

#### 3.1 Catalog Knowledge Engine

**File: `bot/backend/knowledge/catalog_knowledge_engine.py`**
```python
class CatalogKnowledgeEngine:
    async def answer(
        self, 
        request: KnowledgeRequest
    ) -> KnowledgeResponse:
        """
        RAG Pipeline:
        1. Generate query embedding
        2. Vector search (top-K products)
        3. Build context from retrieved products
        4. Generate answer with LLM
        5. Extract citations
        """
```

**RAG Prompt Template:**
```
You are a helpful assistant for a workflow marketplace.

Available products:
{retrieved_products_context}

User question: {question}

Answer the question based on the available products.
If no relevant products found, say so.
Include product titles and IDs in your answer.
```

#### 3.2 Product Retrieval

**File: `bot/backend/knowledge/catalog_retriever.py`**
```python
class CatalogRetriever:
    async def retrieve(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5
    ) -> List[RetrievedProduct]:
        """
        1. Generate query embedding
        2. Vector search in tenant collection
        3. Filter by similarity threshold
        4. Return products with scores
        """
```

#### 3.3 Response Formatting

**Format:**
```json
{
  "answer": "Dựa trên catalog, tôi tìm thấy các workflow sau phù hợp với nhu cầu của bạn...",
  "citations": ["product_123", "product_456"],
  "confidence": 0.85,
  "sources": [
    {
      "title": "Email Automation Workflow",
      "product_id": "product_123",
      "url": "https://catalog.com/products/product_123",
      "match_score": 0.92
    }
  ],
  "metadata": {
    "retrieval_method": "vector",
    "products_found": 3
  }
}
```

**Deliverables:**
- ✅ Catalog knowledge engine
- ✅ Product retriever
- ✅ RAG pipeline implementation
- ✅ Response formatting
- ✅ Unit tests

**Timeline:** 3-4 days

---

### Phase 4: Router Integration

**Mục tiêu:** Tích hợp catalog knowledge engine vào router

#### 4.1 Catalog Domain Handler

**File: `bot/backend/domain/catalog/entry_handler.py`**
```python
class CatalogEntryHandler:
    async def handle(
        self,
        request: DomainRequest
    ) -> DomainResponse:
        """
        1. Call Catalog Knowledge Engine
        2. Format response
        3. Return to router
        """
```

#### 4.2 Router Configuration

**Update `bot/config/intent_registry.yaml`:**
```yaml
catalog:
  domain: "catalog"
  intents:
    - "catalog.search"
    - "catalog.recommend"
    - "catalog.info"
  keywords:
    - "workflow"
    - "product"
    - "tool"
    - "marketplace"
    - "catalog"
```

#### 4.3 Intent Examples

**Add to intent store:**
- "Tôi cần workflow tự động gửi email" → `catalog.search`
- "Workflow nào phù hợp với tôi?" → `catalog.recommend`
- "Cho tôi xem thông tin về workflow X" → `catalog.info`

**Deliverables:**
- ✅ Catalog domain handler
- ✅ Router configuration
- ✅ Intent examples
- ✅ Integration tests

**Timeline:** 2-3 days

---

### Phase 5: API Endpoints & Webhooks

**Mục tiêu:** Expose APIs để quản lý knowledge base

#### 5.1 Admin API Endpoints

**File: `bot/backend/interface/admin_knowledge_api.py`**

**Endpoints:**
```python
# Sync knowledge base
POST /admin/tenants/{tenant_id}/knowledge/sync
  → Trigger manual sync

# Get sync status
GET /admin/tenants/{tenant_id}/knowledge/status
  → {last_sync_at, product_count, sync_status}

# Delete knowledge base
DELETE /admin/tenants/{tenant_id}/knowledge
  → Clear all products for tenant
```

#### 5.2 Webhook Handler (Optional)

**File: `bot/backend/interface/webhooks/catalog_webhook.py`**

**Webhook từ catalog service:**
```python
POST /webhooks/catalog/product-updated
  {
    "tenant_id": "...",
    "product_id": "...",
    "event": "created|updated|deleted"
  }
```

**Handler:**
- `created` → Sync product
- `updated` → Re-sync product
- `deleted` → Delete from vector store

#### 5.3 Scheduled Sync (Background Job)

**File: `bot/backend/scripts/sync_catalog_knowledge.py`**

**Cron job:**
- Run every hour
- Sync products for all active tenants
- Log sync results

**Deliverables:**
- ✅ Admin API endpoints
- ✅ Webhook handler (optional)
- ✅ Scheduled sync script
- ✅ API documentation

**Timeline:** 2-3 days

---

### Phase 6: Testing & Optimization

**Mục tiêu:** Đảm bảo chất lượng và performance

#### 6.1 Unit Tests

**Test files:**
- `bot/tests/unit/test_vector_store.py`
- `bot/tests/unit/test_catalog_sync.py`
- `bot/tests/unit/test_catalog_knowledge_engine.py`
- `bot/tests/unit/test_catalog_retriever.py`

#### 6.2 Integration Tests

**Test scenarios:**
1. Full sync flow (catalog → vector store)
2. Query flow (user question → answer)
3. Multi-tenant isolation
4. Error handling (catalog API down, vector store down)

#### 6.3 Performance Optimization

**Optimizations:**
- Batch embedding generation
- Caching query embeddings
- Index optimization trong vector store
- Connection pooling cho catalog API

#### 6.4 Monitoring

**Metrics to track:**
- Sync duration
- Query latency
- Vector search performance
- Error rates

**Deliverables:**
- ✅ Comprehensive test suite
- ✅ Performance benchmarks
- ✅ Monitoring dashboards
- ✅ Documentation

**Timeline:** 3-4 days

---

## 📊 Tổng Kết Timeline

| Phase | Tasks | Timeline | Dependencies |
|-------|-------|----------|--------------|
| Phase 1 | Vector Store Setup | 2-3 days | None |
| Phase 2 | Knowledge Sync Service | 3-4 days | Phase 1 |
| Phase 3 | Catalog Knowledge Engine | 3-4 days | Phase 1, Phase 2 |
| Phase 4 | Router Integration | 2-3 days | Phase 3 |
| Phase 5 | API Endpoints | 2-3 days | Phase 2 |
| Phase 6 | Testing & Optimization | 3-4 days | All phases |

**Total:** 15-21 days (3-4 weeks)

---

## 🔧 Technical Decisions

### 1. Vector Database: Qdrant

**Reasons:**
- Self-hosted (cost-effective)
- Good performance
- Easy tenant isolation (collections)
- Python SDK tốt

### 2. Embedding Model

**Decision:** Use existing AI Provider (LiteLLM/OpenAI)
- `text-embedding-3-small` (1536 dimensions)
- Hoặc `text-embedding-ada-002` (1536 dimensions)

### 3. Sync Strategy

**Initial:** Full sync (fetch all products)
**Incremental:** Webhook-based updates (optional)
**Periodic:** Scheduled sync every hour

### 4. Tenant Isolation

**Strategy:**
- Separate collections per tenant: `tenant_{tenant_id}_products`
- Metadata filtering: `tenant_id` in vector metadata
- Database: `tenant_id` foreign key

### 5. RAG Pipeline

**Retrieval:**
- Top-K = 5 products
- Similarity threshold = 0.7
- Re-ranking (optional, future)

**Generation:**
- Use existing AI Provider (LiteLLM)
- Temperature = 0.7
- Max tokens = 500

---

## 🚀 Deployment Checklist

### Pre-deployment

- [ ] Setup Qdrant instance (Docker/local)
- [ ] Configure Qdrant URL in environment
- [ ] Test catalog API connectivity
- [ ] Verify tenant API keys

### Deployment Steps

1. **Deploy infrastructure:**
   ```bash
   docker-compose up -d qdrant
   ```

2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Initial sync (per tenant):**
   ```bash
   python scripts/sync_catalog_knowledge.py --tenant-id <tenant_id>
   ```

4. **Verify:**
   - Check sync status API
   - Test query endpoint
   - Monitor logs

### Post-deployment

- [ ] Setup scheduled sync (cron)
- [ ] Configure monitoring alerts
- [ ] Document API endpoints
- [ ] Train support team

---

## 📝 API Documentation

### Admin API

#### Sync Knowledge Base

```http
POST /admin/tenants/{tenant_id}/knowledge/sync
Authorization: Bearer {admin_api_key}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "...",
    "products_synced": 150,
    "duration_seconds": 45.2,
    "status": "completed"
  }
}
```

#### Get Sync Status

```http
GET /admin/tenants/{tenant_id}/knowledge/status
Authorization: Bearer {admin_api_key}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "...",
    "last_sync_at": "2025-01-20T10:30:00Z",
    "product_count": 150,
    "sync_status": "completed",
    "error_message": null
  }
}
```

---

## 🔍 Future Enhancements

### Phase 7 (Future)

1. **Re-ranking:**
   - Use cross-encoder for better relevance
   - Re-rank top-K results

2. **Hybrid Search:**
   - Combine vector search + keyword search
   - Better for exact matches

3. **Product Updates:**
   - Real-time webhooks từ catalog
   - Incremental sync

4. **Analytics:**
   - Track query patterns
   - Product recommendation accuracy
   - User feedback

5. **Multi-language:**
   - Support Vietnamese + English
   - Language-specific embeddings

---

## 📚 References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

---

**Next Steps:**
1. Review và approve plan
2. Setup development environment
3. Start Phase 1 implementation


Các phase chính đã hoàn thành:
Phase 1: Vector Store Setup & Infrastructure
Phase 2: Catalog Knowledge Sync Service
Phase 3: Catalog Knowledge Engine
Phase 4: Router Integration
Phase 5: API Endpoints & Webhooks
Phase 6: Testing & Optimization

Run all tests:
  pytest bot/tests/
Run unit tests only:
  pytest bot/tests/unit/
Run integration tests only:
  pytest bot/tests/integration/
Run specific test file:
  pytest bot/tests/unit/test_catalog_retriever.py
