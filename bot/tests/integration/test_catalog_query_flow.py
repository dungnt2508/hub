"""
Integration tests for catalog query flow
Tests the full flow: User Query → Retrieval → RAG → Answer
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.knowledge.catalog_knowledge_engine import CatalogKnowledgeEngine
from backend.knowledge.catalog_retriever import CatalogRetriever, RetrievedProduct
from backend.schemas.knowledge_types import KnowledgeRequest, KnowledgeResponse
from backend.infrastructure.ai_provider import AIProvider


@pytest.fixture
def mock_retriever():
    """Mock catalog retriever"""
    retriever = Mock(spec=CatalogRetriever)
    retriever.retrieve = AsyncMock(return_value=[])
    return retriever


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider"""
    provider = Mock(spec=AIProvider)
    provider.chat = AsyncMock(return_value="This is a test answer")
    provider.embed = AsyncMock(return_value=[0.1] * 1536)
    return provider


@pytest.fixture
def knowledge_engine(mock_retriever, mock_ai_provider):
    """Create knowledge engine with mocked dependencies"""
    return CatalogKnowledgeEngine(
        retriever=mock_retriever,
        ai_provider=mock_ai_provider,
    )


@pytest.fixture
def sample_retrieved_products():
    """Sample retrieved products"""
    return [
        RetrievedProduct(
            product_id="prod-1",
            title="Email Automation Workflow",
            description="Automatically send emails based on triggers",
            score=0.92,
            metadata={
                "tags": ["email", "automation"],
                "features": ["gmail", "outlook"],
            },
        ),
        RetrievedProduct(
            product_id="prod-2",
            title="CRM Sync Tool",
            description="Sync data between CRM systems",
            score=0.85,
            metadata={
                "tags": ["crm", "sync"],
                "features": ["salesforce", "hubspot"],
            },
        ),
    ]


@pytest.fixture
def knowledge_request():
    """Sample knowledge request"""
    return KnowledgeRequest(
        question="Tôi cần workflow tự động gửi email",
        domain="catalog",
        context={"tenant_id": "test-tenant-123"},
        trace_id="trace-123",
    )


@pytest.mark.asyncio
async def test_full_query_flow(
    knowledge_engine,
    mock_retriever,
    mock_ai_provider,
    knowledge_request,
    sample_retrieved_products,
):
    """Test full query flow: retrieve → generate → format"""
    tenant_id = "test-tenant-123"
    
    # Setup mocks
    mock_retriever.retrieve.return_value = sample_retrieved_products
    mock_ai_provider.chat.return_value = (
        "Dựa trên catalog, tôi tìm thấy workflow Email Automation phù hợp với nhu cầu của bạn. "
        "Workflow này cho phép tự động gửi email dựa trên các trigger."
    )
    
    # Execute query
    response = await knowledge_engine.answer(knowledge_request, tenant_id=tenant_id)
    
    # Verify response
    assert isinstance(response, KnowledgeResponse)
    assert response.answer is not None
    assert len(response.citations) == 2
    assert len(response.sources) == 2
    assert response.confidence > 0.0
    
    # Verify flow
    mock_retriever.retrieve.assert_called_once_with(
        tenant_id=tenant_id,
        query=knowledge_request.question,
        top_k=5,
    )
    mock_ai_provider.chat.assert_called_once()


@pytest.mark.asyncio
async def test_query_no_results(
    knowledge_engine,
    mock_retriever,
    knowledge_request,
):
    """Test query flow when no products found"""
    tenant_id = "test-tenant-123"
    mock_retriever.retrieve.return_value = []
    
    response = await knowledge_engine.answer(knowledge_request, tenant_id=tenant_id)
    
    assert isinstance(response, KnowledgeResponse)
    assert "không tìm thấy" in response.answer.lower() or "not found" in response.answer.lower()
    assert len(response.citations) == 0
    assert response.confidence == 0.0


@pytest.mark.asyncio
async def test_query_llm_generation_error(
    knowledge_engine,
    mock_retriever,
    mock_ai_provider,
    knowledge_request,
    sample_retrieved_products,
):
    """Test query flow when LLM generation fails"""
    tenant_id = "test-tenant-123"
    
    mock_retriever.retrieve.return_value = sample_retrieved_products
    mock_ai_provider.chat.side_effect = Exception("LLM error")
    
    with pytest.raises(Exception):
        await knowledge_engine.answer(knowledge_request, tenant_id=tenant_id)


@pytest.mark.asyncio
async def test_query_confidence_calculation(
    knowledge_engine,
    sample_retrieved_products,
):
    """Test confidence calculation based on retrieval scores"""
    # High scores
    high_score_products = [
        RetrievedProduct(
            product_id="prod-1",
            title="Product 1",
            description="Description",
            score=0.95,
            metadata={},
        ),
        RetrievedProduct(
            product_id="prod-2",
            title="Product 2",
            description="Description",
            score=0.90,
            metadata={},
        ),
        RetrievedProduct(
            product_id="prod-3",
            title="Product 3",
            description="Description",
            score=0.85,
            metadata={},
        ),
    ]
    
    confidence = knowledge_engine._calculate_confidence(high_score_products)
    
    # Should be boosted above top score due to multiple good matches
    assert confidence >= 0.90


@pytest.mark.asyncio
async def test_citations_extraction(
    knowledge_engine,
    sample_retrieved_products,
):
    """Test citation extraction from retrieved products"""
    citations, sources = knowledge_engine._extract_citations(sample_retrieved_products)
    
    assert len(citations) == 2
    assert citations[0] == "product_prod-1"
    assert citations[1] == "product_prod-2"
    
    assert len(sources) == 2
    assert sources[0].title == "Email Automation Workflow"
    assert sources[1].title == "CRM Sync Tool"


@pytest.mark.asyncio
async def test_products_context_building(
    knowledge_engine,
    sample_retrieved_products,
):
    """Test products context building for LLM"""
    context = knowledge_engine._build_products_context(sample_retrieved_products)
    
    assert "Email Automation Workflow" in context
    assert "prod-1" in context
    assert "CRM Sync Tool" in context
    assert "prod-2" in context
    assert "0.92" in context  # Score
    assert "0.85" in context  # Score

