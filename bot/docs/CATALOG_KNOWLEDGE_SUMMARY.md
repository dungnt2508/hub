# 📚 Tóm Tắt: Tích Hợp Knowledge Base Catalog vào Bot Service

## 🎯 Mục Tiêu

Bot service có thể học và sử dụng knowledge base (products) từ catalog service để:
- Tìm kiếm products theo semantic similarity
- Trả lời câu hỏi về products, workflows, tools
- Recommend products dựa trên user query

## 🏗️ Kiến Trúc Tổng Quan

```
Catalog Service (Products DB)
    ↓ API Sync
Bot Service
    ↓ Embedding
Vector Store (Qdrant) - Tenant-scoped
    ↓ Retrieval
Catalog Knowledge Engine (RAG)
    ↓ Answer
User Response
```

## 📋 6 Phases Implementation

### Phase 1: Vector Store Setup (2-3 days)
- Setup Qdrant
- Vector store client
- Configuration

### Phase 2: Knowledge Sync Service (3-4 days)
- Catalog API client
- Sync service (fetch products → embeddings → vector store)
- Database schema cho sync tracking

### Phase 3: Catalog Knowledge Engine (3-4 days)
- RAG pipeline
- Product retriever
- Answer generation

### Phase 4: Router Integration (2-3 days)
- Catalog domain handler
- Router configuration
- Intent examples

### Phase 5: API Endpoints (2-3 days)
- Admin APIs (sync, status)
- Webhook handler (optional)
- Scheduled sync

### Phase 6: Testing & Optimization (3-4 days)
- Unit tests
- Integration tests
- Performance optimization

**Total: 15-21 days (3-4 weeks)**

## 🔧 Technical Stack

- **Vector DB:** Qdrant (self-hosted)
- **Embedding:** OpenAI `text-embedding-3-small` (1536 dims)
- **LLM:** Existing AI Provider (LiteLLM)
- **Tenant Isolation:** Separate collections per tenant

## 📊 Data Flow

**Sync Flow:**
```
Catalog API → Fetch Products → Generate Embeddings → Store in Qdrant
```

**Query Flow:**
```
User Query → Generate Embedding → Vector Search → RAG → Answer
```

## 🚀 Quick Start

1. **Setup Qdrant:**
   ```bash
   docker-compose up -d qdrant
   ```

2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Sync knowledge base:**
   ```bash
   python scripts/sync_catalog_knowledge.py --tenant-id <tenant_id>
   ```

4. **Test query:**
   ```bash
   curl -X POST /bot/message \
     -H "Authorization: Bearer <token>" \
     -d '{"message": "Tôi cần workflow tự động gửi email"}'
   ```

## 📝 Key Files

- `bot/backend/infrastructure/vector_store.py` - Vector store abstraction
- `bot/backend/infrastructure/qdrant_client.py` - Qdrant client
- `bot/backend/knowledge/catalog_knowledge_sync.py` - Sync service
- `bot/backend/knowledge/catalog_knowledge_engine.py` - RAG engine
- `bot/backend/knowledge/catalog_retriever.py` - Product retriever
- `bot/backend/domain/catalog/entry_handler.py` - Domain handler

## 🔍 Chi Tiết

Xem file đầy đủ: [`CATALOG_KNOWLEDGE_INTEGRATION_PLAN.md`](./CATALOG_KNOWLEDGE_INTEGRATION_PLAN.md)


