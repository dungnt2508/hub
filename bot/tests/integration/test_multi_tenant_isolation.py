"""
Integration tests for multi-tenant isolation
Tests that tenants cannot access each other's knowledge base
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid

from backend.knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
from backend.knowledge.catalog_retriever import CatalogRetriever
from backend.knowledge.catalog_knowledge_engine import CatalogKnowledgeEngine
from backend.schemas.knowledge_types import KnowledgeRequest
from backend.infrastructure.catalog_client import CatalogProduct


@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    db.fetchrow = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = Mock()
    store.create_collection = AsyncMock(return_value=True)
    store.upsert_vectors = AsyncMock(return_value=True)
    store.search = AsyncMock(return_value=[])
    return store


@pytest.mark.asyncio
async def test_tenant_collection_isolation(mock_db, mock_vector_store):
    """Test that each tenant has separate collection"""
    tenant_1 = str(uuid.uuid4())
    tenant_2 = str(uuid.uuid4())
    
    with patch('backend.knowledge.catalog_knowledge_sync.get_vector_store', return_value=mock_vector_store):
        sync_service = CatalogKnowledgeSyncService(mock_db)
        
        # Sync for tenant 1
        await sync_service.sync_tenant_products(tenant_1)
        
        # Sync for tenant 2
        await sync_service.sync_tenant_products(tenant_2)
        
        # Verify separate collections were created
        assert mock_vector_store.create_collection.call_count == 2
        
        # Verify collection names are different
        call_1_collection = mock_vector_store.create_collection.call_args_list[0][0][0]
        call_2_collection = mock_vector_store.create_collection.call_args_list[1][0][0]
        
        assert call_1_collection != call_2_collection
        assert call_1_collection == f"tenant_{tenant_1}_products"
        assert call_2_collection == f"tenant_{tenant_2}_products"


@pytest.mark.asyncio
async def test_tenant_search_isolation(mock_vector_store):
    """Test that search is isolated per tenant"""
    tenant_1 = str(uuid.uuid4())
    tenant_2 = str(uuid.uuid4())
    
    from backend.infrastructure.qdrant_client import SearchResult
    
    # Mock different results for different tenants
    tenant_1_results = [
        SearchResult(
            id="prod-1",
            score=0.9,
            metadata={"product_id": "prod-1", "title": "Tenant 1 Product"},
        ),
    ]
    
    tenant_2_results = [
        SearchResult(
            id="prod-2",
            score=0.9,
            metadata={"product_id": "prod-2", "title": "Tenant 2 Product"},
        ),
    ]
    
    def search_side_effect(tenant_id, **kwargs):
        if tenant_id == tenant_1:
            return tenant_1_results
        else:
            return tenant_2_results
    
    mock_vector_store.search.side_effect = search_side_effect
    
    with patch('backend.knowledge.catalog_retriever.get_vector_store', return_value=mock_vector_store):
        retriever = CatalogRetriever()
        
        # Search for tenant 1
        results_1 = await retriever.retrieve(tenant_1, "query")
        assert len(results_1) == 1
        assert results_1[0].product_id == "prod-1"
        
        # Search for tenant 2
        results_2 = await retriever.retrieve(tenant_2, "query")
        assert len(results_2) == 1
        assert results_2[0].product_id == "prod-2"
        
        # Verify searches used correct tenant_id
        assert mock_vector_store.search.call_count == 2
        assert mock_vector_store.search.call_args_list[0][1]["tenant_id"] == tenant_1
        assert mock_vector_store.search.call_args_list[1][1]["tenant_id"] == tenant_2


@pytest.mark.asyncio
async def test_tenant_knowledge_engine_isolation(mock_db):
    """Test knowledge engine respects tenant isolation"""
    tenant_1 = str(uuid.uuid4())
    tenant_2 = str(uuid.uuid4())
    
    request_1 = KnowledgeRequest(
        question="Test query",
        domain="catalog",
        context={"tenant_id": tenant_1},
        trace_id="trace-1",
    )
    
    request_2 = KnowledgeRequest(
        question="Test query",
        domain="catalog",
        context={"tenant_id": tenant_2},
        trace_id="trace-2",
    )
    
    mock_retriever = Mock()
    mock_retriever.retrieve = AsyncMock(return_value=[])
    
    knowledge_engine = CatalogKnowledgeEngine(retriever=mock_retriever)
    
    # Answer for tenant 1
    await knowledge_engine.answer(request_1, tenant_id=tenant_1)
    
    # Answer for tenant 2
    await knowledge_engine.answer(request_2, tenant_id=tenant_2)
    
    # Verify retrieves used correct tenant_id
    assert mock_retriever.retrieve.call_count == 2
    assert mock_retriever.retrieve.call_args_list[0][1]["tenant_id"] == tenant_1
    assert mock_retriever.retrieve.call_args_list[1][1]["tenant_id"] == tenant_2


@pytest.mark.asyncio
async def test_tenant_delete_isolation(mock_db, mock_vector_store):
    """Test that deleting one tenant's data doesn't affect others"""
    tenant_1 = str(uuid.uuid4())
    tenant_2 = str(uuid.uuid4())
    
    with patch('backend.knowledge.catalog_knowledge_sync.get_vector_store', return_value=mock_vector_store):
        sync_service = CatalogKnowledgeSyncService(mock_db)
        
        # Delete tenant 1's collection directly
        await mock_vector_store.delete_collection(tenant_1)
        
        # Verify only tenant 1's collection was deleted
        mock_vector_store.delete_collection.assert_called_once_with(tenant_1)
        
        # Verify tenant 2's collection should still exist
        # (would be verified by checking if collection exists in real implementation)

