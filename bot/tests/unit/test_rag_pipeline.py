"""
Unit Tests for RAG Pipeline components
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import List

from backend.knowledge.document_chunker import DocumentChunker, DocumentChunk
from backend.knowledge.knowledge_ingester import KnowledgeIngester
from backend.knowledge.rag_orchestrator import RAGOrchestrator, RetrievedDocument
from backend.infrastructure.ai_provider import AIProvider
from backend.infrastructure.vector_store import QdrantVectorStore
from backend.infrastructure.qdrant_client import VectorPoint, SearchResult


class TestDocumentChunker:
    """Test DocumentChunker class"""
    
    @pytest.fixture
    def chunker(self):
        return DocumentChunker(chunk_size=500, chunk_overlap=100)
    
    def test_chunk_text_basic(self, chunker):
        """Test basic text chunking"""
        text = "This is a test. " * 100  # ~1600 characters
        
        chunks = chunker.chunk_text(
            text=text,
            source="test.txt",
            page=1,
        )
        
        assert len(chunks) > 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.source == "test.txt" for c in chunks)
        assert all(c.page == 1 for c in chunks)
    
    def test_chunk_text_empty(self, chunker):
        """Test chunking empty text"""
        chunks = chunker.chunk_text("", source="empty.txt")
        
        assert len(chunks) == 0
    
    def test_chunk_text_with_metadata(self, chunker):
        """Test chunking with metadata"""
        text = "Sample text. " * 50
        metadata = {"type": "policy", "domain": "hr"}
        
        chunks = chunker.chunk_text(
            text=text,
            source="policy.txt",
            metadata=metadata,
        )
        
        assert all(c.metadata == metadata for c in chunks)
    
    def test_chunk_documents(self, chunker):
        """Test chunking multiple documents"""
        documents = [
            {
                "content": "Document 1 content. " * 30,
                "source": "doc1.txt",
            },
            {
                "content": "Document 2 content. " * 30,
                "source": "doc2.txt",
            },
        ]
        
        chunks = chunker.chunk_documents(documents)
        
        assert len(chunks) > 0
        assert any(c.source == "doc1.txt" for c in chunks)
        assert any(c.source == "doc2.txt" for c in chunks)
    
    def test_semantic_split_preserves_meaning(self, chunker):
        """Test that semantic splitting preserves content meaning"""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        
        chunks = chunker._semantic_split(text)
        
        # All original content should be in chunks
        combined = " ".join(chunks)
        assert "Paragraph 1" in combined
        assert "Paragraph 2" in combined
        assert "Paragraph 3" in combined


class TestKnowledgeIngester:
    """Test KnowledgeIngester class"""
    
    @pytest.fixture
    def mock_vector_store(self):
        store = AsyncMock(spec=QdrantVectorStore)
        store.collection_exists = AsyncMock(return_value=True)
        store.upsert_vectors = AsyncMock(return_value=True)
        return store
    
    @pytest.fixture
    def mock_ai_provider(self):
        provider = AsyncMock(spec=AIProvider)
        provider.embed = AsyncMock(return_value=[0.1] * 1536)  # Mock embedding
        return provider
    
    @pytest.fixture
    def ingester(self, mock_vector_store, mock_ai_provider):
        return KnowledgeIngester(
            vector_store=mock_vector_store,
            ai_provider=mock_ai_provider,
        )
    
    @pytest.mark.asyncio
    async def test_ingest_documents_success(self, ingester, mock_vector_store):
        """Test successful document ingestion"""
        documents = [
            {
                "content": "Test policy document. " * 50,
                "source": "policy.txt",
                "page": 1,
            }
        ]
        
        result = await ingester.ingest_documents(
            documents=documents,
            tenant_id="test-tenant",
            domain="hr",
        )
        
        assert result["status"] == "success"
        assert result["chunk_count"] > 0
        mock_vector_store.upsert_vectors.assert_called()
    
    @pytest.mark.asyncio
    async def test_ingest_documents_create_collection(self, ingester, mock_vector_store):
        """Test collection creation if not exists"""
        mock_vector_store.collection_exists = AsyncMock(return_value=False)
        
        documents = [
            {"content": "Test content. " * 50, "source": "test.txt"}
        ]
        
        result = await ingester.ingest_documents(
            documents=documents,
            tenant_id="test-tenant",
            domain="hr",
        )
        
        assert result["status"] == "success"
        mock_vector_store.create_collection.assert_called()
    
    @pytest.mark.asyncio
    async def test_ingest_documents_empty(self, ingester):
        """Test ingesting empty document"""
        documents = []
        
        result = await ingester.ingest_documents(
            documents=documents,
            tenant_id="test-tenant",
            domain="hr",
        )
        
        assert result["status"] == "success"
        assert result["chunk_count"] == 0


class TestRAGOrchestrator:
    """Test RAGOrchestrator class"""
    
    @pytest.fixture
    def mock_vector_store(self):
        store = AsyncMock(spec=QdrantVectorStore)
        return store
    
    @pytest.fixture
    def mock_ai_provider(self):
        provider = AsyncMock(spec=AIProvider)
        provider.embed = AsyncMock(return_value=[0.1] * 1536)
        provider.chat = AsyncMock(return_value="Test answer")
        return provider
    
    @pytest.fixture
    def orchestrator(self, mock_vector_store, mock_ai_provider):
        return RAGOrchestrator(
            vector_store=mock_vector_store,
            ai_provider=mock_ai_provider,
            top_k=5,
        )
    
    @pytest.mark.asyncio
    async def test_answer_question_success(self, orchestrator, mock_vector_store):
        """Test successful question answering"""
        # Mock retrieved documents
        mock_search_results = [
            Mock(
                id="doc1",
                score=0.9,
                metadata={
                    "content": "Test content for doc1",
                    "source": "policy1.txt",
                    "domain": "hr",
                }
            )
        ]
        mock_vector_store.search = AsyncMock(return_value=mock_search_results)
        
        result = await orchestrator.answer_question(
            question="What is the leave policy?",
            tenant_id="test-tenant",
            domain="hr",
        )
        
        assert result["answer"] == "Test answer"
        assert result["confidence"] > 0
        assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_answer_question_no_results(self, orchestrator, mock_vector_store):
        """Test question answering with no results"""
        mock_vector_store.search = AsyncMock(return_value=[])
        
        result = await orchestrator.answer_question(
            question="Unknown question?",
            tenant_id="test-tenant",
        )
        
        assert result["confidence"] == 0.0
        assert len(result["sources"]) == 0
        assert "không tìm thấy" in result["answer"]
    
    def test_build_context(self, orchestrator):
        """Test context building"""
        docs = [
            RetrievedDocument(
                id="doc1",
                content="This is document 1 content",
                source="doc1.txt",
                score=0.95,
                metadata={"page": 1},
            ),
            RetrievedDocument(
                id="doc2",
                content="This is document 2 content",
                source="doc2.txt",
                score=0.85,
                metadata={"page": 2},
            ),
        ]
        
        context = orchestrator._build_context(docs)
        
        assert "Document 1" in context
        assert "Document 2" in context
        assert "0.95" in context
        assert "0.85" in context
    
    def test_extract_sources(self, orchestrator):
        """Test source extraction"""
        docs = [
            RetrievedDocument(
                id="doc1",
                content="Content 1",
                source="source1.txt",
                score=0.9,
                metadata={"page": 1},
            )
        ]
        
        sources = orchestrator._extract_sources(docs)
        
        assert len(sources) == 1
        assert sources[0]["source"] == "source1.txt"
        assert sources[0]["score"] == 0.9
    
    def test_calculate_confidence(self, orchestrator):
        """Test confidence calculation"""
        # Test with high-quality matches
        docs_good = [
            RetrievedDocument("id1", "content", "source", 0.95, {}),
            RetrievedDocument("id2", "content", "source", 0.85, {}),
            RetrievedDocument("id3", "content", "source", 0.80, {}),
        ]
        
        confidence_good = orchestrator._calculate_confidence(docs_good)
        assert confidence_good > 0.9
        
        # Test with low-quality matches
        docs_poor = [
            RetrievedDocument("id1", "content", "source", 0.55, {}),
        ]
        
        confidence_poor = orchestrator._calculate_confidence(docs_poor)
        assert confidence_poor < 0.6
        
        # Test with empty list
        confidence_empty = orchestrator._calculate_confidence([])
        assert confidence_empty == 0.0


@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test RAG pipeline end-to-end"""
    # Mock AI provider
    ai_provider = AsyncMock(spec=AIProvider)
    ai_provider.embed = AsyncMock(return_value=[0.1] * 1536)
    ai_provider.chat = AsyncMock(return_value="Generated answer based on context")
    
    # Mock vector store
    vector_store = AsyncMock(spec=QdrantVectorStore)
    vector_store.search = AsyncMock(return_value=[
        Mock(
            id="doc1",
            score=0.92,
            metadata={
                "content": "Leave policy allows 12 days per year",
                "source": "policy.txt",
                "domain": "hr",
            }
        )
    ])
    
    # Create orchestrator
    orchestrator = RAGOrchestrator(
        vector_store=vector_store,
        ai_provider=ai_provider,
    )
    
    # Test answering question
    result = await orchestrator.answer_question(
        question="How many leave days are allowed?",
        tenant_id="tenant1",
        domain="hr",
    )
    
    # Verify results
    assert "answer" in result
    assert result["confidence"] > 0.8
    assert len(result["sources"]) == 1
    assert result["metadata"]["retrieval_method"] == "vector"

