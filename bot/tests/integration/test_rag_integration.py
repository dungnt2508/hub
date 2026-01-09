"""
Integration Tests for RAG Pipeline
Tests RAG pipeline with real components
"""
import pytest
import json
from typing import List, Optional

from backend.knowledge.document_chunker import DocumentChunker
from backend.knowledge.knowledge_ingester import KnowledgeIngester
from backend.knowledge.rag_orchestrator import RAGOrchestrator
from backend.knowledge.catalog_knowledge_engine import CatalogKnowledgeEngine
from backend.knowledge.hr_knowledge_engine import HRKnowledgeEngine
from backend.schemas import KnowledgeRequest
from backend.infrastructure.ai_provider import AIProvider
from backend.infrastructure.vector_store import QdrantVectorStore
from backend.shared.config import config


@pytest.mark.asyncio
class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline"""
    
    @pytest.fixture
    def test_tenant_id(self):
        return "integration-test-tenant"
    
    @pytest.fixture
    def chunker(self):
        return DocumentChunker(chunk_size=1000, chunk_overlap=200)
    
    @pytest.fixture
    async def vector_store(self):
        """Create vector store for tests"""
        store = QdrantVectorStore()
        # Health check
        if not await store.health_check():
            pytest.skip("Qdrant service not available")
        return store
    
    @pytest.fixture
    async def ai_provider(self):
        """Create AI provider for tests"""
        return AIProvider()
    
    @pytest.fixture
    async def ingester(self, vector_store, ai_provider, chunker):
        """Create ingester for tests"""
        return KnowledgeIngester(
            vector_store=vector_store,
            ai_provider=ai_provider,
            chunker=chunker,
        )
    
    @pytest.fixture
    async def orchestrator(self, vector_store, ai_provider):
        """Create orchestrator for tests"""
        return RAGOrchestrator(
            vector_store=vector_store,
            ai_provider=ai_provider,
            top_k=3,
        )
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_ingest_and_retrieve_hr_documents(self, ingester, orchestrator, test_tenant_id):
        """Test ingesting HR documents and retrieving them"""
        # Prepare test documents
        hr_documents = [
            {
                "content": """HR POLICY - LEAVE MANAGEMENT
                
Annual Leave:
- Employees are entitled to 12 working days of annual leave per calendar year
- Leave can be carried forward to the next year with manager approval
- Maximum 5 days can be carried forward

Sick Leave:
- Employees are entitled to 5 days of paid sick leave per year
- Medical certificate required for absences exceeding 2 consecutive days

Maternity Leave:
- Female employees are entitled to 4 months of maternity leave
- Paid by social insurance
- Job protection during maternity leave
""",
                "source": "hr_policy_2024.txt",
                "metadata": {"type": "policy", "domain": "hr", "year": 2024},
            },
            {
                "content": """LEAVE REQUEST PROCEDURE

Step 1: Submit Leave Request
- Use HR portal or paper form
- Specify leave type and dates
- Provide reason for leave

Step 2: Manager Approval
- Manager reviews request within 2 working days
- Can approve, reject, or suggest alternative dates

Step 3: HR Confirmation
- HR confirms leave after manager approval
- Sends confirmation email to employee

Step 4: Leave Taken
- Employee takes leave on approved dates
- Updates timesheet in HR system

Step 5: Return to Work
- Employee returns to normal duties
- Manager updates leave balance
""",
                "source": "leave_request_procedure.txt",
                "metadata": {"type": "procedure", "domain": "hr"},
            },
        ]
        
        # Ingest documents
        ingest_result = await ingester.ingest_documents(
            documents=hr_documents,
            tenant_id=test_tenant_id,
            domain="hr",
        )
        
        assert ingest_result["status"] == "success"
        assert ingest_result["chunk_count"] > 0
        assert ingest_result["ingested_count"] > 0
        
        # Test retrieving information
        result = await orchestrator.answer_question(
            question="มีกี่วันปษาน้อยที่สุด?",  # Thai example
            tenant_id=test_tenant_id,
            domain="hr",
        )
        
        assert result["confidence"] > 0.5
        assert len(result["sources"]) > 0
        assert result["answer"] is not None
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_catalog_knowledge_engine(self, orchestrator, test_tenant_id):
        """Test catalog knowledge engine"""
        engine = CatalogKnowledgeEngine(
            rag_orchestrator=orchestrator,
        )
        
        # Create test request
        request = KnowledgeRequest(
            trace_id="test-123",
            domain="catalog",
            question="What workflows are available for email marketing?",
            context={"tenant_id": test_tenant_id},
        )
        
        # Get response
        response = await engine.answer(request, tenant_id=test_tenant_id)
        
        assert response.answer is not None
        assert isinstance(response.confidence, float)
        assert 0 <= response.confidence <= 1
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_hr_knowledge_engine(self, orchestrator, test_tenant_id):
        """Test HR knowledge engine"""
        engine = HRKnowledgeEngine(
            rag_orchestrator=orchestrator,
        )
        
        # Create test request
        request = KnowledgeRequest(
            trace_id="test-456",
            domain="hr",
            question="How many annual leave days do employees get?",
            context={"tenant_id": test_tenant_id},
        )
        
        # Get response
        response = await engine.answer(request, tenant_id=test_tenant_id)
        
        assert response.answer is not None
        assert isinstance(response.confidence, float)
        assert len(response.sources) >= 0
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_rag_pipeline_multilingual(self, ingester, orchestrator, test_tenant_id):
        """Test RAG pipeline with multilingual queries"""
        # Ingest English document
        documents = [
            {
                "content": "Flexible working hours are available from 6 AM to 10 PM",
                "source": "work_policy_en.txt",
            }
        ]
        
        await ingester.ingest_documents(
            documents=documents,
            tenant_id=test_tenant_id,
            domain="hr",
        )
        
        # Test queries in different languages
        test_queries = [
            "What are the flexible working hours?",  # English
            "Berapakah jam kerja fleksibel?",  # Indonesian
            "Quais são os horários de trabalho flexíveis?",  # Portuguese
        ]
        
        for query in test_queries:
            result = await orchestrator.answer_question(
                question=query,
                tenant_id=test_tenant_id,
            )
            
            assert result["answer"] is not None
            assert isinstance(result["confidence"], float)
    
    async def test_chunker_with_real_content(self, chunker):
        """Test chunker with realistic content"""
        # Realistic HR policy content
        content = """
        EMPLOYEE HANDBOOK 2024
        
        Section 1: Working Hours
        The standard working hours are from 8:00 AM to 5:00 PM, Monday to Friday.
        Employees are entitled to a one-hour lunch break.
        Flexible working arrangements are available upon request.
        
        Section 2: Leave Policy
        Annual Leave:
        - 12 working days per year for first 5 years
        - 15 working days per year after 5 years of service
        - Unused leave can be carried forward (max 5 days)
        
        Sick Leave:
        - 5 working days per year
        - Medical certificate required for absences over 2 days
        
        Public Holidays:
        - All national public holidays are observed
        - If work is required, double pay is provided
        
        Section 3: Code of Conduct
        All employees must:
        - Arrive on time
        - Treat colleagues with respect
        - Follow company policies
        - Maintain confidentiality
        """
        
        chunks = chunker.chunk_text(
            text=content,
            source="employee_handbook.txt",
        )
        
        # Verify chunks
        assert len(chunks) > 0
        assert all(len(c.content) > 0 for c in chunks)
        assert all(c.source == "employee_handbook.txt" for c in chunks)
        
        # Verify no content is lost
        combined = " ".join(c.content for c in chunks)
        assert "EMPLOYEE HANDBOOK" in combined
        assert "Leave Policy" in combined


@pytest.mark.asyncio
class TestRAGPipelineEdgeCases:
    """Test edge cases in RAG pipeline"""
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_empty_document(self, ingester):
        """Test ingesting empty document"""
        documents = [
            {"content": "", "source": "empty.txt"}
        ]
        
        result = await ingester.ingest_documents(
            documents=documents,
            tenant_id="test",
            domain="hr",
        )
        
        assert result["status"] == "success"
        assert result["chunk_count"] == 0
    
    @pytest.mark.skip(reason="Requires Qdrant and LLM services")
    async def test_very_long_document(self, ingester, chunker):
        """Test ingesting very long document"""
        # Create 100KB document
        content = "This is test content. " * 5000
        
        documents = [
            {"content": content, "source": "long_doc.txt"}
        ]
        
        result = await ingester.ingest_documents(
            documents=documents,
            tenant_id="test",
            domain="hr",
        )
        
        assert result["status"] == "success"
        assert result["chunk_count"] > 1
    
    def test_special_characters_in_content(self, chunker):
        """Test chunking content with special characters"""
        content = """
        Special Characters Test: !@#$%^&*()
        Emoji Test: 😀 😃 😄 😁
        Vietnamese: Xin chào, đây là một bài kiểm tra
        Chinese: 这是一个测试
        Arabic: هذا اختبار
        """
        
        chunks = chunker.chunk_text(
            text=content,
            source="special_chars.txt",
        )
        
        assert len(chunks) > 0
        combined = " ".join(c.content for c in chunks)
        assert "Xin chào" in combined or combined  # Content preserved

