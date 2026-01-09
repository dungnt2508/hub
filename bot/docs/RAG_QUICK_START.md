"""
RAG Pipeline Quick Start - Getting started in 5 minutes
"""

# Phase 3: RAG Pipeline Quick Start Guide 🚀

## 1️⃣ Prerequisites

### Start Infrastructure Services

```bash
# Start Qdrant, PostgreSQL, Redis
cd infra
docker-compose -f docker-compose.infra.yml up -d

# Verify Qdrant is running
curl http://localhost:6333/health
# Should return: {"status":"ok"}
```

### Environment Variables

```bash
# Copy and update .env
cp bot/env.example bot/.env

# Key variables for RAG:
QDRANT_URL=http://qdrant:6333
LITELLM_API_BASE=http://localhost:8000  # Or your LiteLLM server
OPENAI_API_KEY=sk-your-key              # For fallback
```

---

## 2️⃣ Quick Test: Ingest & Retrieve

### Step 1: Create ingestion script

```python
# bot/examples/quick_start_rag.py

import asyncio
from backend.knowledge import DocumentChunker, KnowledgeIngester
from backend.infrastructure.vector_store import QdrantVectorStore
from backend.infrastructure.ai_provider import AIProvider

async def main():
    # Initialize components
    ingester = KnowledgeIngester()
    
    # Sample HR documents
    documents = [
        {
            "content": """
            LEAVE POLICY 2024
            
            Annual Leave:
            - Employees are entitled to 12 working days of annual leave
            - Leave can be carried forward with manager approval
            
            Sick Leave:
            - 5 working days per year
            - Medical certificate required for >2 days
            
            Maternity Leave:
            - 4 months paid leave
            - Job protection guaranteed
            """,
            "source": "hr_policy_2024.txt",
            "metadata": {"type": "policy", "domain": "hr"}
        }
    ]
    
    # Ingest documents
    print("📥 Ingesting documents...")
    result = await ingester.ingest_documents(
        documents=documents,
        tenant_id="demo-tenant",
        domain="hr",
    )
    
    print(f"✅ Ingested {result['ingested_count']} documents")
    print(f"   Chunks created: {result['chunk_count']}")
    
    # Test retrieval
    from backend.knowledge import RAGOrchestrator
    
    orchestrator = RAGOrchestrator()
    
    print("\n🔍 Testing retrieval...")
    answer_result = await orchestrator.answer_question(
        question="How many annual leave days do employees get?",
        tenant_id="demo-tenant",
        domain="hr",
    )
    
    print(f"\n📝 Answer: {answer_result['answer']}")
    print(f"🎯 Confidence: {answer_result['confidence']:.1%}")
    print(f"📚 Sources found: {len(answer_result['sources'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Run it

```bash
cd bot
python -m examples.quick_start_rag

# Expected output:
# 📥 Ingesting documents...
# ✅ Ingested 1 documents
#    Chunks created: 3
# 
# 🔍 Testing retrieval...
# 
# 📝 Answer: Employees are entitled to 12 working days of annual leave per year...
# 🎯 Confidence: 92.0%
# 📚 Sources found: 1
```

---

## 3️⃣ Core Usage Patterns

### Pattern 1: Simple Document Ingestion

```python
from backend.knowledge import KnowledgeIngester

ingester = KnowledgeIngester()

# Ingest from text
await ingester.ingest_documents(
    documents=[
        {"content": "Policy text...", "source": "policy.txt"}
    ],
    tenant_id="tenant-123",
    domain="hr",
)

# Ingest from file
await ingester.ingest_from_file(
    file_path="policy_2024.pdf",
    tenant_id="tenant-123",
    domain="hr",
)
```

### Pattern 2: Answer Questions

```python
from backend.knowledge import HRKnowledgeEngine
from backend.schemas import KnowledgeRequest

engine = HRKnowledgeEngine()

request = KnowledgeRequest(
    trace_id="req-123",
    domain="hr",
    question="What is the leave policy?",
    context={"tenant_id": "tenant-123"}
)

response = await engine.answer(request)
print(response.answer)
print(f"Confidence: {response.confidence:.0%}")
```

### Pattern 3: Sync Catalog Products

```python
from backend.knowledge import CatalogKnowledgeSyncService

sync_service = CatalogKnowledgeSyncService(db, catalog_client)

# Full sync
result = await sync_service.sync_tenant_products("tenant-123")
print(f"✅ Synced {result.products_synced} products")

# Single product
await sync_service.sync_product("tenant-123", product)

# Check status
status = await sync_service.get_sync_status("tenant-123")
print(f"Last sync: {status.last_sync_at}")
```

---

## 4️⃣ API Endpoints (FastAPI)

### Add to your FastAPI app:

```python
# backend/interface/knowledge_api.py

from fastapi import APIRouter, HTTPException
from backend.knowledge import HRKnowledgeEngine, CatalogKnowledgeEngine
from backend.knowledge import get_scheduler
from backend.schemas import KnowledgeRequest, KnowledgeResponse

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# Answer knowledge question
@router.post("/answer", response_model=KnowledgeResponse)
async def answer_question(request: KnowledgeRequest):
    try:
        if request.domain == "hr":
            engine = HRKnowledgeEngine()
        elif request.domain == "catalog":
            engine = CatalogKnowledgeEngine()
        else:
            raise ValueError(f"Unknown domain: {request.domain}")
        
        response = await engine.answer(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trigger knowledge sync
@router.post("/sync/{tenant_id}")
async def trigger_sync(tenant_id: str):
    scheduler = get_scheduler()
    result = await scheduler.sync_now(tenant_id)
    return result

# Add to main app
app.include_router(router)
```

### Test endpoints:

```bash
# Answer question
curl -X POST http://localhost:8000/api/knowledge/answer \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "test-123",
    "domain": "hr",
    "question": "How many annual leave days?",
    "context": {"tenant_id": "tenant-123"}
  }'

# Trigger sync
curl -X POST http://localhost:8000/api/knowledge/sync/tenant-123
```

---

## 5️⃣ Running Tests

### Unit Tests

```bash
# All RAG tests
pytest tests/unit/test_rag_pipeline.py -v

# Specific test
pytest tests/unit/test_rag_pipeline.py::TestRAGOrchestrator::test_answer_question_success -v

# With coverage
pytest tests/unit/test_rag_pipeline.py --cov=backend.knowledge --cov-report=html
```

### Integration Tests

```bash
# Requires Qdrant + LLM running
# Most tests are skipped - unskip for full testing
pytest tests/integration/test_rag_integration.py -v -m "not skip"
```

---

## 6️⃣ Common Tasks

### Upload HR Policies

```python
import asyncio
from backend.knowledge import KnowledgeIngester
from pathlib import Path

async def upload_policies():
    ingester = KnowledgeIngester()
    
    # Get all PDF files
    policy_dir = Path("policies")
    for policy_file in policy_dir.glob("*.pdf"):
        print(f"Uploading {policy_file}...")
        
        await ingester.ingest_from_file(
            file_path=str(policy_file),
            tenant_id="tenant-123",
            domain="hr",
        )
    
    print("✅ All policies uploaded")

asyncio.run(upload_policies())
```

### Monitor Sync Status

```python
from backend.knowledge import CatalogKnowledgeSyncService

sync_service = CatalogKnowledgeSyncService(db, catalog_client)

# Check status
status = await sync_service.get_sync_status("tenant-123")

if status:
    print(f"✅ Last sync: {status.last_sync_at}")
    print(f"   Status: {status.sync_status}")
    print(f"   Products: {status.product_count}")
    if status.error_message:
        print(f"   Error: {status.error_message}")
```

### Clear and Re-sync Knowledge

```python
# Delete collection
vector_store = QdrantVectorStore()
await vector_store.delete_collection("tenant-123")

# Re-ingest
ingester = KnowledgeIngester()
await ingester.ingest_documents(documents, "tenant-123", "hr")
```

---

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in environment:
export LOG_LEVEL=DEBUG
```

### Check Qdrant Collections

```python
from backend.infrastructure.vector_store import QdrantVectorStore

store = QdrantVectorStore()

# Get collection info
info = await store.get_collection_info("tenant-123")
print(f"Points: {info['points_count']}")
print(f"Vector size: {info['config']['vector_size']}")

# Health check
health = await store.health_check()
print(f"Qdrant healthy: {health}")
```

### Test Embedding Quality

```python
from backend.infrastructure.ai_provider import AIProvider

provider = AIProvider()

# Test embedding
embedding = await provider.embed("Test text")
print(f"Embedding dimension: {len(embedding)}")
print(f"Sample values: {embedding[:5]}")

# Should be 1536 for text-embedding-3-small
```

---

## 📊 Monitoring

### Key Metrics to Track

1. **Retrieval Performance**
   - Retrieval latency (target: < 100ms)
   - Top-k hit rate
   - Cache hit rate

2. **Quality Metrics**
   - Answer confidence (target: > 0.7)
   - User satisfaction
   - Accuracy of answers

3. **Cost Metrics**
   - Embedding cost per document
   - LLM cost per query
   - Total monthly spend

---

## 🚀 Next Steps

1. **Test with your data**
   ```bash
   # Upload your own documents
   python examples/upload_documents.py
   ```

2. **Integrate with your API**
   - Add endpoints to your FastAPI app
   - Test with real questions

3. **Monitor and optimize**
   - Check latency metrics
   - Adjust parameters
   - Scale if needed

4. **Deploy to production**
   - Follow Phase 4 checklist
   - Set up monitoring
   - Plan capacity

---

## 📚 More Resources

- Full guide: [RAG_PIPELINE_GUIDE.md](./RAG_PIPELINE_GUIDE.md)
- Implementation plan: [IMPLEMENTATION_PLAN_DETAILED.md](./plan/IMPLEMENTATION_PLAN_DETAILED.md)
- API reference: See KnowledgeResponse schema

---

**Ready to go?** 🎉 Try the quick test above!

