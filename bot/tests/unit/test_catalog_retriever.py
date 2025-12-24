"""
Unit tests for Catalog Retriever
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.knowledge.catalog_retriever import CatalogRetriever, RetrievedProduct
from backend.infrastructure.ai_provider import AIProvider
from backend.shared.exceptions import ExternalServiceError


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider"""
    provider = Mock(spec=AIProvider)
    provider.embed = AsyncMock(return_value=[0.1] * 1536)
    return provider


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = Mock()
    store.search = AsyncMock(return_value=[])
    return store


@pytest.fixture
def retriever(mock_ai_provider, mock_vector_store):
    """Create retriever with mocked dependencies"""
    with patch('backend.knowledge.catalog_retriever.get_vector_store', return_value=mock_vector_store):
        return CatalogRetriever(ai_provider=mock_ai_provider)


@pytest.mark.asyncio
async def test_retrieve_success(retriever, mock_ai_provider, mock_vector_store):
    """Test successful product retrieval"""
    tenant_id = "test-tenant-123"
    query = "Tôi cần workflow tự động gửi email"
    
    # Mock search results
    from backend.infrastructure.qdrant_client import SearchResult
    mock_results = [
        SearchResult(
            id="prod-1",
            score=0.92,
            metadata={
                "product_id": "prod-1",
                "title": "Email Automation Workflow",
                "description": "Automatically send emails",
            },
        ),
        SearchResult(
            id="prod-2",
            score=0.85,
            metadata={
                "product_id": "prod-2",
                "title": "CRM Sync Tool",
                "description": "Sync data between CRM systems",
            },
        ),
    ]
    mock_vector_store.search.return_value = mock_results
    
    results = await retriever.retrieve(tenant_id, query, top_k=5)
    
    assert len(results) == 2
    assert results[0].product_id == "prod-1"
    assert results[0].score == 0.92
    assert results[0].title == "Email Automation Workflow"
    
    # Verify calls
    mock_ai_provider.embed.assert_called_once_with(query)
    mock_vector_store.search.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_with_threshold(retriever, mock_vector_store):
    """Test retrieval with custom score threshold"""
    tenant_id = "test-tenant-123"
    query = "Test query"
    score_threshold = 0.8
    
    mock_vector_store.search.return_value = []
    
    await retriever.retrieve(tenant_id, query, top_k=5, score_threshold=score_threshold)
    
    # Verify threshold was passed to search
    call_args = mock_vector_store.search.call_args
    assert call_args[1]["score_threshold"] == score_threshold


@pytest.mark.asyncio
async def test_retrieve_empty_results(retriever, mock_vector_store):
    """Test retrieval with no results"""
    tenant_id = "test-tenant-123"
    query = "Nonexistent product"
    
    mock_vector_store.search.return_value = []
    
    results = await retriever.retrieve(tenant_id, query)
    
    assert len(results) == 0


@pytest.mark.asyncio
async def test_retrieve_with_context(retriever, mock_vector_store):
    """Test retrieval with conversation context"""
    tenant_id = "test-tenant-123"
    query = "Tôi cần workflow"
    context = ["Tôi muốn tự động hóa công việc", "Có thể giúp tôi tìm workflow không?"]
    
    mock_vector_store.search.return_value = []
    
    await retriever.retrieve_with_context(tenant_id, query, context)
    
    # Verify enriched query was used
    call_args = mock_vector_store.search.call_args
    # The query embedding should have been generated with context
    assert call_args is not None


@pytest.mark.asyncio
async def test_retrieve_embedding_error(retriever, mock_ai_provider):
    """Test error handling when embedding generation fails"""
    tenant_id = "test-tenant-123"
    query = "Test query"
    
    mock_ai_provider.embed.side_effect = Exception("Embedding error")
    
    with pytest.raises(ExternalServiceError) as exc_info:
        await retriever.retrieve(tenant_id, query)
    
    assert "Product retrieval failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_vector_search_error(retriever, mock_vector_store):
    """Test error handling when vector search fails"""
    tenant_id = "test-tenant-123"
    query = "Test query"
    
    mock_vector_store.search.side_effect = Exception("Vector search error")
    
    with pytest.raises(ExternalServiceError) as exc_info:
        await retriever.retrieve(tenant_id, query)
    
    assert "Product retrieval failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_invalid_metadata(retriever, mock_vector_store):
    """Test handling of invalid metadata in search results"""
    tenant_id = "test-tenant-123"
    query = "Test query"
    
    from backend.infrastructure.qdrant_client import SearchResult
    
    # Result with missing metadata
    mock_results = [
        SearchResult(
            id="prod-1",
            score=0.9,
            metadata={},  # Missing title, description
        ),
    ]
    mock_vector_store.search.return_value = mock_results
    
    results = await retriever.retrieve(tenant_id, query)
    
    # Should still return results, but with default values
    assert len(results) == 1
    assert results[0].product_id == "prod-1"
    assert results[0].title == "Unknown"


@pytest.mark.asyncio
async def test_retrieve_default_threshold(retriever):
    """Test default similarity threshold"""
    assert retriever.similarity_threshold == 0.7


@pytest.mark.asyncio
async def test_retrieve_custom_threshold():
    """Test custom similarity threshold"""
    retriever = CatalogRetriever(similarity_threshold=0.85)
    assert retriever.similarity_threshold == 0.85

