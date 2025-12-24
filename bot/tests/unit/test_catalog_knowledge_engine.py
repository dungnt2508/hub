"""
Unit tests for Catalog Knowledge Engine
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.knowledge.catalog_knowledge_engine import CatalogKnowledgeEngine
from backend.knowledge.catalog_retriever import CatalogRetriever, RetrievedProduct
from backend.schemas.knowledge_types import KnowledgeRequest, KnowledgeResponse, KnowledgeSource
from backend.infrastructure.ai_provider import AIProvider
from backend.shared.exceptions import ExternalServiceError


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
def sample_products():
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
def knowledge_engine(mock_retriever, mock_ai_provider):
    """Create knowledge engine with mocked dependencies"""
    return CatalogKnowledgeEngine(
        retriever=mock_retriever,
        ai_provider=mock_ai_provider,
    )


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
async def test_answer_with_products(
    knowledge_engine,
    mock_retriever,
    mock_ai_provider,
    knowledge_request,
    sample_products,
):
    """Test answer generation with retrieved products"""
    mock_retriever.retrieve.return_value = sample_products
    mock_ai_provider.chat.return_value = "Dựa trên catalog, tôi tìm thấy workflow Email Automation phù hợp với nhu cầu của bạn."
    
    response = await knowledge_engine.answer(knowledge_request)
    
    assert isinstance(response, KnowledgeResponse)
    assert response.answer is not None
    assert len(response.citations) == 2
    assert len(response.sources) == 2
    assert response.confidence > 0.0
    
    # Verify calls
    mock_retriever.retrieve.assert_called_once()
    mock_ai_provider.chat.assert_called_once()


@pytest.mark.asyncio
async def test_answer_no_products(
    knowledge_engine,
    mock_retriever,
    knowledge_request,
):
    """Test answer when no products found"""
    mock_retriever.retrieve.return_value = []
    
    response = await knowledge_engine.answer(knowledge_request)
    
    assert isinstance(response, KnowledgeResponse)
    assert "không tìm thấy" in response.answer.lower() or "not found" in response.answer.lower()
    assert len(response.citations) == 0
    assert response.confidence == 0.0
    assert response.metadata["products_found"] == 0


@pytest.mark.asyncio
async def test_answer_missing_tenant_id(knowledge_engine, mock_retriever):
    """Test answer when tenant_id is missing"""
    request = KnowledgeRequest(
        question="Test question",
        domain="catalog",
        context={},  # No tenant_id
        trace_id="trace-123",
    )
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await knowledge_engine.answer(request)


@pytest.mark.asyncio
async def test_build_products_context(knowledge_engine, sample_products):
    """Test products context building"""
    context = knowledge_engine._build_products_context(sample_products)
    
    assert "Email Automation Workflow" in context
    assert "prod-1" in context
    assert "CRM Sync Tool" in context
    assert "prod-2" in context


@pytest.mark.asyncio
async def test_extract_citations(knowledge_engine, sample_products):
    """Test citation extraction"""
    citations, sources = knowledge_engine._extract_citations(sample_products)
    
    assert len(citations) == 2
    assert citations[0] == "product_prod-1"
    assert citations[1] == "product_prod-2"
    
    assert len(sources) == 2
    assert sources[0].title == "Email Automation Workflow"
    assert sources[1].title == "CRM Sync Tool"


@pytest.mark.asyncio
async def test_calculate_confidence(knowledge_engine, sample_products):
    """Test confidence calculation"""
    confidence = knowledge_engine._calculate_confidence(sample_products)
    
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.0  # Should have some confidence with good matches


@pytest.mark.asyncio
async def test_calculate_confidence_empty(knowledge_engine):
    """Test confidence calculation with empty list"""
    confidence = knowledge_engine._calculate_confidence([])
    
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_calculate_confidence_single_product(knowledge_engine):
    """Test confidence with single product"""
    products = [
        RetrievedProduct(
            product_id="prod-1",
            title="Test",
            description="Test",
            score=0.75,
            metadata={},
        )
    ]
    
    confidence = knowledge_engine._calculate_confidence(products)
    
    assert confidence == 0.75  # Should match top score


@pytest.mark.asyncio
async def test_calculate_confidence_multiple_high_scores(knowledge_engine):
    """Test confidence boost with multiple high scores"""
    products = [
        RetrievedProduct(
            product_id=f"prod-{i}",
            title=f"Product {i}",
            description="Test",
            score=0.85,
            metadata={},
        )
        for i in range(3)
    ]
    
    confidence = knowledge_engine._calculate_confidence(products)
    
    # Should be boosted above 0.85
    assert confidence >= 0.85


@pytest.mark.asyncio
async def test_generate_answer(knowledge_engine, mock_ai_provider):
    """Test answer generation"""
    question = "What workflows are available?"
    products_context = "Product 1: Test workflow"
    
    answer = await knowledge_engine._generate_answer(question, products_context)
    
    assert answer is not None
    assert len(answer) > 0
    mock_ai_provider.chat.assert_called_once()
    
    # Check prompt format
    call_args = mock_ai_provider.chat.call_args
    messages = call_args[0][0]
    assert len(messages) == 2
    assert question in messages[1]["content"]
    assert products_context in messages[1]["content"]


@pytest.mark.asyncio
async def test_answer_retrieval_error(
    knowledge_engine,
    mock_retriever,
    knowledge_request,
):
    """Test error handling when retrieval fails"""
    mock_retriever.retrieve.side_effect = ExternalServiceError("Retrieval failed")
    
    with pytest.raises(ExternalServiceError):
        await knowledge_engine.answer(knowledge_request)


@pytest.mark.asyncio
async def test_answer_llm_error(
    knowledge_engine,
    mock_retriever,
    mock_ai_provider,
    knowledge_request,
    sample_products,
):
    """Test error handling when LLM fails"""
    mock_retriever.retrieve.return_value = sample_products
    mock_ai_provider.chat.side_effect = ExternalServiceError("LLM failed")
    
    with pytest.raises(ExternalServiceError):
        await knowledge_engine.answer(knowledge_request)


@pytest.mark.asyncio
async def test_answer_tenant_id_from_context(knowledge_engine, mock_retriever):
    """Test tenant_id extraction from context"""
    request = KnowledgeRequest(
        question="Test",
        domain="catalog",
        context={"tenant_id": "tenant-from-context"},
        trace_id="trace-123",
    )
    
    mock_retriever.retrieve.return_value = []
    
    await knowledge_engine.answer(request)
    
    # Verify tenant_id was extracted from context
    mock_retriever.retrieve.assert_called_once_with(
        tenant_id="tenant-from-context",
        query="Test",
        top_k=5,
    )


@pytest.mark.asyncio
async def test_answer_tenant_id_override(
    knowledge_engine,
    mock_retriever,
    knowledge_request,
):
    """Test tenant_id override"""
    mock_retriever.retrieve.return_value = []
    
    await knowledge_engine.answer(knowledge_request, tenant_id="override-tenant")
    
    # Verify override tenant_id was used
    mock_retriever.retrieve.assert_called_once_with(
        tenant_id="override-tenant",
        query=knowledge_request.question,
        top_k=5,
    )

