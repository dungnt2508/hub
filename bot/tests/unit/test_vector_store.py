"""
Unit tests for Vector Store operations
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from backend.infrastructure.vector_store import QdrantVectorStore, get_vector_store
from backend.infrastructure.qdrant_client import VectorPoint, SearchResult
from backend.shared.exceptions import ExternalServiceError


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = Mock()
    client.create_collection = AsyncMock(return_value=True)
    client.collection_exists = AsyncMock(return_value=True)
    client.upsert_vectors = AsyncMock(return_value=True)
    client.search = AsyncMock(return_value=[])
    client.delete_collection = AsyncMock(return_value=True)
    client.delete_points = AsyncMock(return_value=True)
    client.get_collection_info = AsyncMock(return_value=None)
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def vector_store(mock_qdrant_client):
    """Create vector store with mocked client"""
    return QdrantVectorStore(qdrant_client=mock_qdrant_client)


@pytest.mark.asyncio
async def test_create_collection(vector_store, mock_qdrant_client):
    """Test collection creation"""
    tenant_id = "test-tenant-123"
    
    result = await vector_store.create_collection(tenant_id)
    
    assert result is True
    mock_qdrant_client.create_collection.assert_called_once_with(tenant_id)


@pytest.mark.asyncio
async def test_upsert_vectors(vector_store, mock_qdrant_client):
    """Test vector upsert"""
    tenant_id = "test-tenant-123"
    vectors = [
        VectorPoint(
            id="vec-1",
            vector=[0.1, 0.2, 0.3] * 512,  # 1536 dims
            metadata={"product_id": "prod-1", "title": "Test Product"}
        ),
        VectorPoint(
            id="vec-2",
            vector=[0.4, 0.5, 0.6] * 512,
            metadata={"product_id": "prod-2", "title": "Another Product"}
        ),
    ]
    
    result = await vector_store.upsert_vectors(tenant_id, vectors)
    
    assert result is True
    mock_qdrant_client.upsert_vectors.assert_called_once()
    call_args = mock_qdrant_client.upsert_vectors.call_args
    assert call_args[0][0] == tenant_id
    assert len(call_args[0][1]) == 2


@pytest.mark.asyncio
async def test_search_vectors(vector_store, mock_qdrant_client):
    """Test vector search"""
    tenant_id = "test-tenant-123"
    query_vector = [0.1, 0.2, 0.3] * 512
    top_k = 5
    
    # Mock search results
    mock_results = [
        SearchResult(
            id="vec-1",
            score=0.95,
            metadata={"product_id": "prod-1", "title": "Test Product"}
        ),
        SearchResult(
            id="vec-2",
            score=0.87,
            metadata={"product_id": "prod-2", "title": "Another Product"}
        ),
    ]
    mock_qdrant_client.search.return_value = mock_results
    
    results = await vector_store.search(tenant_id, query_vector, top_k=top_k)
    
    assert len(results) == 2
    assert results[0].id == "vec-1"
    assert results[0].score == 0.95
    mock_qdrant_client.search.assert_called_once_with(
        tenant_id=tenant_id,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=None,
    )


@pytest.mark.asyncio
async def test_search_with_threshold(vector_store, mock_qdrant_client):
    """Test vector search with score threshold"""
    tenant_id = "test-tenant-123"
    query_vector = [0.1, 0.2, 0.3] * 512
    top_k = 5
    score_threshold = 0.7
    
    mock_results = [
        SearchResult(
            id="vec-1",
            score=0.95,
            metadata={"product_id": "prod-1"}
        ),
    ]
    mock_qdrant_client.search.return_value = mock_results
    
    results = await vector_store.search(
        tenant_id,
        query_vector,
        top_k=top_k,
        score_threshold=score_threshold
    )
    
    assert len(results) == 1
    mock_qdrant_client.search.assert_called_once_with(
        tenant_id=tenant_id,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=score_threshold,
    )


@pytest.mark.asyncio
async def test_delete_collection(vector_store, mock_qdrant_client):
    """Test collection deletion"""
    tenant_id = "test-tenant-123"
    
    result = await vector_store.delete_collection(tenant_id)
    
    assert result is True
    mock_qdrant_client.delete_collection.assert_called_once_with(tenant_id)


@pytest.mark.asyncio
async def test_delete_points(vector_store, mock_qdrant_client):
    """Test point deletion"""
    tenant_id = "test-tenant-123"
    point_ids = ["vec-1", "vec-2"]
    
    result = await vector_store.delete_points(tenant_id, point_ids)
    
    assert result is True
    mock_qdrant_client.delete_points.assert_called_once_with(tenant_id, point_ids)


@pytest.mark.asyncio
async def test_collection_exists(vector_store, mock_qdrant_client):
    """Test collection existence check"""
    tenant_id = "test-tenant-123"
    mock_qdrant_client.collection_exists.return_value = True
    
    result = await vector_store.collection_exists(tenant_id)
    
    assert result is True
    mock_qdrant_client.collection_exists.assert_called_once_with(tenant_id)


@pytest.mark.asyncio
async def test_get_collection_info(vector_store, mock_qdrant_client):
    """Test getting collection info"""
    tenant_id = "test-tenant-123"
    mock_info = {
        "name": "tenant_test-tenant-123_products",
        "points_count": 100,
        "vectors_count": 100,
        "config": {
            "vector_size": 1536,
            "distance": "Cosine",
        },
    }
    mock_qdrant_client.get_collection_info.return_value = mock_info
    
    info = await vector_store.get_collection_info(tenant_id)
    
    assert info == mock_info
    mock_qdrant_client.get_collection_info.assert_called_once_with(tenant_id)


@pytest.mark.asyncio
async def test_health_check(vector_store, mock_qdrant_client):
    """Test health check"""
    mock_qdrant_client.health_check.return_value = True
    
    result = await vector_store.health_check()
    
    assert result is True
    mock_qdrant_client.health_check.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_empty_list(vector_store, mock_qdrant_client):
    """Test upsert with empty list"""
    tenant_id = "test-tenant-123"
    
    result = await vector_store.upsert_vectors(tenant_id, [])
    
    assert result is True
    # Should not call client if empty
    mock_qdrant_client.upsert_vectors.assert_called_once()


@pytest.mark.asyncio
async def test_search_empty_collection(vector_store, mock_qdrant_client):
    """Test search in non-existent collection"""
    tenant_id = "test-tenant-123"
    query_vector = [0.1, 0.2, 0.3] * 512
    mock_qdrant_client.collection_exists.return_value = False
    mock_qdrant_client.search.return_value = []
    
    results = await vector_store.search(tenant_id, query_vector)
    
    assert results == []
    # Search should not be called if collection doesn't exist
    # (based on qdrant_client implementation)


@pytest.mark.asyncio
async def test_error_handling_create_collection(vector_store, mock_qdrant_client):
    """Test error handling in create_collection"""
    tenant_id = "test-tenant-123"
    mock_qdrant_client.create_collection.side_effect = Exception("Connection error")
    
    with pytest.raises(ExternalServiceError) as exc_info:
        await vector_store.create_collection(tenant_id)
    
    assert "Failed to create collection" in str(exc_info.value)


@pytest.mark.asyncio
async def test_error_handling_search(vector_store, mock_qdrant_client):
    """Test error handling in search"""
    tenant_id = "test-tenant-123"
    query_vector = [0.1, 0.2, 0.3] * 512
    mock_qdrant_client.search.side_effect = Exception("Search error")
    
    with pytest.raises(ExternalServiceError) as exc_info:
        await vector_store.search(tenant_id, query_vector)
    
    assert "Search failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_vector_store_singleton():
    """Test get_vector_store returns singleton"""
    # Reset global instance
    import backend.infrastructure.vector_store as vs_module
    vs_module._vector_store_instance = None
    
    store1 = get_vector_store()
    store2 = get_vector_store()
    
    # Should be same instance
    assert store1 is store2

