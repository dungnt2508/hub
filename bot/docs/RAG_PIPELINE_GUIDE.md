# 🎯 RAG Pipeline Guide - Hub Bot Phase 3

**Ngày cập nhật**: 8 Tháng 1, 2025  
**Trạng thái**: ✅ Phase 3 Complete  
**Thành phần chính**: Knowledge Ingestion, RAG Orchestration, LLM Integration

---

## 📋 Tổng quan

**RAG (Retrieval-Augmented Generation)** Pipeline là trái tim của hệ thống Q&A. Nó cho phép bot trả lời các câu hỏi dựa trên kiến thức được lưu trữ trong vector database.

### 🎯 Mục tiêu
- ✅ Nhập documents vào vector store (Qdrant)
- ✅ Trích xuất tài liệu liên quan từ vector store
- ✅ Sử dụng LLM để sinh câu trả lời dựa trên context
- ✅ Đồng bộ dữ liệu catalog tự động
- ✅ Hỗ trợ đa ngôn ngữ (Vietnamese, English, etc.)

---

## 🏗️ Kiến trúc RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input (Knowledge Request)                                       │
│         ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 1: Document Ingestion                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Split documents into chunks                           │   │
│  │ • Generate embeddings for each chunk                    │   │
│  │ • Store in Qdrant vector store                          │   │
│  │                                                          │   │
│  │ Components:                                              │   │
│  │ - DocumentChunker: Chia documents thành chunks          │   │
│  │ - KnowledgeIngester: Xử lý nhập dữ liệu                │   │
│  │ - CatalogKnowledgeSyncService: Sync from catalog API   │   │
│  └─────────────────────────────────────────────────────────┘   │
│         ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 2: Question Processing & Retrieval                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Embed user question                                   │   │
│  │ • Search similar vectors in Qdrant                      │   │
│  │ • Retrieve top-k relevant documents                     │   │
│  │                                                          │   │
│  │ Component: RAGOrchestrator                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│         ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 3: Context Building                                │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Format retrieved documents as context                 │   │
│  │ • Build prompt with question + context                  │   │
│  │ • Prepare for LLM                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│         ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 4: Answer Generation                               │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Call LLM with context                                 │   │
│  │ • Generate answer in Vietnamese                         │   │
│  │ • Extract sources and citations                         │   │
│  │                                                          │   │
│  │ Component: AIProvider (LiteLLM/OpenAI)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│         ↓                                                         │
│  Output (Knowledge Response)                                     │
│                                                                  │
│  {                                                               │
│    "answer": "...",                                              │
│    "sources": [...],                                             │
│    "confidence": 0.92,                                           │
│    "metadata": {...}                                             │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### 1️⃣ **DocumentChunker** (`document_chunker.py`)

Chia documents thành chunks để embedding.

```python
from backend.knowledge import DocumentChunker

# Initialize
chunker = DocumentChunker(
    chunk_size=1000,      # Max 1000 characters per chunk
    chunk_overlap=200,    # 200 chars overlap between chunks
)

# Chunk single document
chunks = chunker.chunk_text(
    text="Long document text...",
    source="policy.txt",
    page=1,
    metadata={"type": "policy"}
)

# Chunk multiple documents
all_chunks = chunker.chunk_documents([
    {"content": "Doc 1...", "source": "doc1.txt"},
    {"content": "Doc 2...", "source": "doc2.txt"},
])
```

**Features**:
- ✅ Semantic splitting (paragraphs → sentences → fixed size)
- ✅ Chunk overlap để tránh mất context
- ✅ Metadata preservation
- ✅ Unicode support (Vietnamese, etc.)

---

### 2️⃣ **KnowledgeIngester** (`knowledge_ingester.py`)

Nhập documents vào vector store.

```python
from backend.knowledge import KnowledgeIngester

ingester = KnowledgeIngester()

# Ingest documents
result = await ingester.ingest_documents(
    documents=[
        {
            "content": "HR Policy...",
            "source": "policy.txt",
            "metadata": {"domain": "hr"}
        }
    ],
    tenant_id="tenant-123",
    domain="hr",
)

# Check result
print(result)  # {
#   "status": "success",
#   "ingested_count": 5,
#   "chunk_count": 15,
#   "failed_count": 0,
# }

# Ingest from file
result = await ingester.ingest_from_file(
    file_path="/path/to/policy.txt",
    tenant_id="tenant-123",
    domain="hr",
)
```

**Pipeline**:
1. Split documents → chunks
2. Embed chunks (LiteLLM/OpenAI)
3. Upsert to Qdrant
4. Track ingestion history

---

### 3️⃣ **RAGOrchestrator** (`rag_orchestrator.py`)

Điều phối RAG pipeline cho việc trả lời câu hỏi.

```python
from backend.knowledge import RAGOrchestrator

orchestrator = RAGOrchestrator(
    top_k=5,                    # Retrieve top 5 documents
    score_threshold=0.5,        # Min similarity score
)

# Answer question
result = await orchestrator.answer_question(
    question="What is the leave policy?",
    tenant_id="tenant-123",
    domain="hr",
)

# Result structure
{
    "answer": "Employees are entitled to 12 days of annual leave...",
    "sources": [
        {
            "id": "doc_1",
            "source": "hr_policy.txt",
            "score": 0.92,
            "excerpt": "..."
        }
    ],
    "confidence": 0.89,
    "metadata": {
        "retrieval_method": "vector",
        "retrieved_count": 5,
        "top_score": 0.92
    }
}
```

**Pipeline**:
1. Embed question
2. Search Qdrant
3. Build context
4. Generate answer with LLM
5. Extract sources

---

### 4️⃣ **HRKnowledgeEngine** (`hr_knowledge_engine.py`)

RAG engine cho HR domain.

```python
from backend.knowledge import HRKnowledgeEngine
from backend.schemas import KnowledgeRequest

engine = HRKnowledgeEngine()

# Answer HR question
request = KnowledgeRequest(
    trace_id="trace-123",
    domain="hr",
    question="How many leave days do employees get?",
    context={"tenant_id": "tenant-123"}
)

response = await engine.answer(request)
# Returns: KnowledgeResponse with answer, sources, confidence
```

---

### 5️⃣ **CatalogKnowledgeEngine** (`catalog_knowledge_engine.py`)

RAG engine cho Catalog domain - **đã hoàn thiện**.

```python
from backend.knowledge import CatalogKnowledgeEngine

engine = CatalogKnowledgeEngine()

request = KnowledgeRequest(
    trace_id="trace-456",
    domain="catalog",
    question="What workflows are available for email?",
    context={"tenant_id": "tenant-123"}
)

response = await engine.answer(request, tenant_id="tenant-123")
```

---

### 6️⃣ **CatalogKnowledgeSyncService** (Cập nhật)

Đồng bộ catalog products từ Catalog Service.

```python
from backend.knowledge import CatalogKnowledgeSyncService

sync_service = CatalogKnowledgeSyncService(
    db_connection=db,
    catalog_client=catalog_client,
)

# Sync all products for tenant
result = await sync_service.sync_tenant_products(
    tenant_id="tenant-123",
    batch_size=10,
)

# Sync single product
success = await sync_service.sync_product(
    tenant_id="tenant-123",
    product=product,
)

# Delete product
success = await sync_service.delete_product(
    tenant_id="tenant-123",
    product_id="product-123",
)
```

---

### 7️⃣ **KnowledgeSyncScheduler** (`knowledge_sync_scheduler.py`)

Scheduler cho periodic knowledge sync.

```python
from backend.knowledge import get_scheduler

scheduler = get_scheduler()

# Start scheduler (runs in background)
await scheduler.start()

# Trigger immediate sync
result = await scheduler.sync_now(tenant_id="tenant-123")

# Stop scheduler
await scheduler.stop()
```

---

## 🔌 Integration Points

### FastAPI Setup

```python
# In main.py or api.py

from backend.knowledge import get_scheduler

# Startup event
@app.on_event("startup")
async def startup():
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("Knowledge sync scheduler started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    scheduler = get_scheduler()
    await scheduler.stop()
    logger.info("Knowledge sync scheduler stopped")

# API endpoint: Trigger knowledge sync
@router.post("/admin/knowledge/sync/{tenant_id}")
async def trigger_knowledge_sync(tenant_id: str):
    scheduler = get_scheduler()
    result = await scheduler.sync_now(tenant_id)
    return result

# API endpoint: Answer knowledge question
@router.post("/api/knowledge/answer")
async def answer_knowledge_question(request: KnowledgeRequest):
    if request.domain == "hr":
        engine = HRKnowledgeEngine()
    elif request.domain == "catalog":
        engine = CatalogKnowledgeEngine()
    else:
        raise ValueError(f"Unknown domain: {request.domain}")
    
    response = await engine.answer(request)
    return response
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/test_rag_pipeline.py -v

# Test specific components
pytest tests/unit/test_rag_pipeline.py::TestDocumentChunker -v
pytest tests/unit/test_rag_pipeline.py::TestKnowledgeIngester -v
pytest tests/unit/test_rag_pipeline.py::TestRAGOrchestrator -v
```

### Integration Tests

```bash
# Run integration tests (requires Qdrant + LLM)
pytest tests/integration/test_rag_integration.py -v -m "not skip"

# Note: Skipped by default - enable Qdrant and LLM services first
```

---

## 🚀 Deployment Checklist

### Prerequisites

✅ **Qdrant Vector Database** (docker-compose.infra.yml)
- URL: `http://localhost:6333`
- Collections: `tenant_{tenant_id}_products`

✅ **LLM Services**
- LiteLLM (primary): `LITELLM_API_BASE` env var
- OpenAI (fallback): `OPENAI_API_KEY` env var

✅ **Catalog Service**
- API endpoint: `CATALOG_API_BASE` env var

### Environment Variables

```bash
# Vector Store
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional

# LLM Providers
LITELLM_API_BASE=http://litellm-proxy:8000
LITELLM_API_KEY=your-api-key
LITELLM_CHAT_MODEL=gpt-3.5-turbo
LITELLM_EMBEDDING_MODEL=text-embedding-3-small

OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Sync Configuration
KNOWLEDGE_SYNC_INTERVAL_HOURS=24
```

### Database Migrations

```sql
-- Create sync status table
CREATE TABLE knowledge_sync_status (
    tenant_id UUID PRIMARY KEY,
    sync_status VARCHAR(50),
    product_count INT,
    last_sync_at TIMESTAMP,
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create knowledge products tracking
CREATE TABLE knowledge_products (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    vector_id VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    synced_at TIMESTAMP,
    UNIQUE(tenant_id, product_id)
);
```

---

## 📊 Performance Metrics

### Target Metrics

| Metric | Target | Critical |
|--------|--------|----------|
| Retrieval latency | < 100ms | < 500ms |
| LLM response | < 2s | < 5s |
| End-to-end | < 3s | < 10s |
| Embedding accuracy | > 90% | > 80% |
| Confidence score | 0.7-0.95 | > 0.5 |

### Monitoring

```python
# Monitor retrieval performance
from backend.knowledge import PerformanceMonitor

monitor = get_performance_monitor()

# Log metrics
metrics = monitor.get_metrics()
# {
#     "total_queries": 1250,
#     "avg_retrieval_time": 85,
#     "cache_hit_rate": 0.68,
#     "embedding_cost": "$12.34"
# }
```

---

## 🔧 Troubleshooting

### Issue: Low retrieval accuracy

**Solutions**:
1. Increase chunk size (better context)
2. Reduce chunk overlap if redundant
3. Improve embedding model
4. Check document quality/format

### Issue: Slow responses

**Solutions**:
1. Enable query caching
2. Increase batch embedding size
3. Use better LLM model
4. Optimize Qdrant indexing

### Issue: High costs

**Solutions**:
1. Use LiteLLM for cost-effective routing
2. Implement query caching
3. Batch embeddings
4. Use smaller embedding model

### Issue: Multi-language support

**Solutions**:
1. Use multilingual embedding model
2. Test with non-English queries
3. Adjust prompt templates for language
4. Use language-aware chunking

---

## 📚 API Reference

### KnowledgeRequest

```python
class KnowledgeRequest(BaseModel):
    trace_id: str                      # Request trace ID
    domain: str                        # "hr" or "catalog"
    question: str                      # User question
    context: Optional[Dict] = None     # Additional context
```

### KnowledgeResponse

```python
class KnowledgeResponse(BaseModel):
    answer: str                        # Generated answer
    citations: List[str] = []          # Citation IDs
    confidence: float                  # 0.0 - 1.0
    sources: List[KnowledgeSource] = [] # Source documents
    metadata: Dict[str, Any] = {}      # Additional metadata
```

---

## 🎓 Usage Examples

### Example 1: Ingest HR Policies

```python
# Load HR documents
hr_documents = [
    {
        "content": open("policy_2024.pdf").read(),
        "source": "policy_2024.pdf",
        "metadata": {"year": 2024}
    }
]

# Ingest
ingester = KnowledgeIngester()
result = await ingester.ingest_documents(
    documents=hr_documents,
    tenant_id="tenant-123",
    domain="hr",
)

print(f"Ingested {result['ingested_count']} documents")
```

### Example 2: Answer HR Question

```python
# Create engine
engine = HRKnowledgeEngine()

# Create request
request = KnowledgeRequest(
    trace_id="req-001",
    domain="hr",
    question="Nhân viên được nghỉ bao nhiêu ngày phép?",
    context={"user_id": "user-123"}
)

# Get answer
response = await engine.answer(request, tenant_id="tenant-123")

print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence:.1%}")
print(f"Sources: {[s.title for s in response.sources]}")
```

### Example 3: Monitor Sync Status

```python
# Check sync status
sync_service = CatalogKnowledgeSyncService(db, catalog_client)
status = await sync_service.get_sync_status("tenant-123")

print(f"Status: {status.sync_status}")
print(f"Last sync: {status.last_sync_at}")
print(f"Products: {status.product_count}")
```

---

## 📖 Additional Resources

- [Phase 1: Router Foundation](./plan/IMPLEMENTATION_PLAN_DETAILED.md)
- [Phase 2: Domain Engines](./plan/IMPLEMENTATION_PLAN_DETAILED.md)
- [RAG Architecture](./ARCHITECTURE_DIAGRAMS.md)
- [Qdrant Documentation](https://qdrant.tech/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

## ✅ Phase 3 Completion Status

- ✅ Document Chunker implemented
- ✅ Knowledge Ingester implemented
- ✅ RAG Orchestrator implemented
- ✅ HR Knowledge Engine completed
- ✅ Catalog Knowledge Engine updated
- ✅ Knowledge Sync Service implemented
- ✅ Sync Scheduler implemented
- ✅ Unit tests created
- ✅ Integration tests created
- ✅ Documentation complete

**Status**: 🎉 PHASE 3 COMPLETE - Ready for Phase 4 (Production)

---

## 🚀 Next Steps

### Phase 4: Production Ready (Week 4-5)

1. **Monitoring & Observability**
   - Prometheus metrics for RAG pipeline
   - Grafana dashboards
   - Alert rules

2. **Admin Panel Enhancement**
   - Knowledge management UI
   - Sync status monitoring
   - Document upload interface

3. **API Documentation**
   - OpenAPI/Swagger specs
   - Integration guides
   - Error code documentation

4. **Performance Optimization**
   - Query result caching
   - Batch embedding
   - Vector index optimization

5. **Security & Compliance**
   - Data encryption
   - Access control
   - Audit logging

---

**Generated**: 8 January 2025  
**Version**: 1.0.0

