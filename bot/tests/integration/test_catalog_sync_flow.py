"""
Integration tests for catalog sync flow
Tests the full flow: Catalog API → Embeddings → Vector Store
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid

from backend.knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService, SyncResult
from backend.infrastructure.catalog_client import CatalogClient, CatalogProduct
from backend.shared.exceptions import ExternalServiceError


@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    db.fetchrow = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_catalog_client():
    """Mock catalog client"""
    client = Mock(spec=CatalogClient)
    client.get_all_products = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider"""
    provider = Mock()
    provider.embed = AsyncMock(return_value=[0.1] * 1536)
    return provider


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = Mock()
    store.create_collection = AsyncMock(return_value=True)
    store.upsert_vectors = AsyncMock(return_value=True)
    return store


@pytest.fixture
def sample_products():
    """Sample products for testing"""
    return [
        CatalogProduct(
            id=str(uuid.uuid4()),
            seller_id="seller-1",
            title="Email Automation Workflow",
            description="Automatically send emails based on triggers",
            type="workflow",
            tags=["email", "automation"],
            features=["gmail", "outlook"],
            requirements=[],
            status="published",
            review_status="approved",
        ),
        CatalogProduct(
            id=str(uuid.uuid4()),
            seller_id="seller-1",
            title="CRM Sync Tool",
            description="Sync data between CRM systems",
            type="tool",
            tags=["crm", "sync"],
            features=["salesforce", "hubspot"],
            requirements=[],
            status="published",
            review_status="approved",
        ),
    ]


@pytest.fixture
def sync_service(mock_db, mock_catalog_client, mock_ai_provider, mock_vector_store):
    """Create sync service with mocked dependencies"""
    with patch('backend.knowledge.catalog_knowledge_sync.get_vector_store', return_value=mock_vector_store):
        service = CatalogKnowledgeSyncService(
            db_connection=mock_db,
            catalog_client=mock_catalog_client,
            ai_provider=mock_ai_provider,
        )
        return service


@pytest.mark.asyncio
async def test_full_sync_flow(
    sync_service,
    mock_catalog_client,
    mock_ai_provider,
    mock_vector_store,
    mock_db,
    sample_products,
):
    """Test full sync flow from catalog to vector store"""
    tenant_id = str(uuid.uuid4())
    
    # Setup mocks
    mock_catalog_client.get_all_products.return_value = sample_products
    
    # Mock database operations
    mock_db.execute = AsyncMock()  # For knowledge_products insert
    
    # Run sync
    result = await sync_service.sync_tenant_products(tenant_id, batch_size=10)
    
    # Verify results
    assert result.status == "completed"
    assert result.products_synced == 2
    assert result.products_failed == 0
    
    # Verify calls
    mock_catalog_client.get_all_products.assert_called_once()
    mock_vector_store.create_collection.assert_called_once_with(tenant_id)
    assert mock_ai_provider.embed.call_count == 2  # One per product
    mock_vector_store.upsert_vectors.assert_called_once()


@pytest.mark.asyncio
async def test_sync_with_batch_processing(
    sync_service,
    mock_catalog_client,
    mock_vector_store,
    mock_ai_provider,
    mock_db,
):
    """Test sync with batch processing"""
    tenant_id = str(uuid.uuid4())
    
    # Create 15 products (will be processed in batches of 10)
    products = [
        CatalogProduct(
            id=str(uuid.uuid4()),
            seller_id="seller-1",
            title=f"Product {i}",
            description=f"Description {i}",
            type="workflow",
            tags=[],
            features=[],
            requirements=[],
            status="published",
            review_status="approved",
        )
        for i in range(15)
    ]
    
    mock_catalog_client.get_all_products.return_value = products
    mock_db.execute = AsyncMock()
    
    result = await sync_service.sync_tenant_products(tenant_id, batch_size=10)
    
    assert result.products_synced == 15
    # Should call upsert twice (batch 1: 10, batch 2: 5)
    assert mock_vector_store.upsert_vectors.call_count == 2


@pytest.mark.asyncio
async def test_sync_handles_embedding_failure(
    sync_service,
    mock_catalog_client,
    mock_ai_provider,
    mock_vector_store,
    sample_products,
):
    """Test sync handles embedding generation failures gracefully"""
    tenant_id = str(uuid.uuid4())
    
    mock_catalog_client.get_all_products.return_value = sample_products
    
    # Make first embedding succeed, second fail
    call_count = 0
    def embed_side_effect(text):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("Embedding error")
        return [0.1] * 1536
    
    mock_ai_provider.embed.side_effect = embed_side_effect
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    # Should complete with partial failure
    assert result.status in ["completed", "partial"]
    assert result.products_synced == 1
    assert result.products_failed == 1


@pytest.mark.asyncio
async def test_sync_handles_catalog_api_error(
    sync_service,
    mock_catalog_client,
):
    """Test sync handles catalog API errors"""
    tenant_id = str(uuid.uuid4())
    
    mock_catalog_client.get_all_products.side_effect = ExternalServiceError("Catalog API error")
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    assert result.status == "failed"
    assert "Catalog API error" in result.error_message


@pytest.mark.asyncio
async def test_sync_handles_vector_store_error(
    sync_service,
    mock_catalog_client,
    mock_vector_store,
    sample_products,
):
    """Test sync handles vector store errors"""
    tenant_id = str(uuid.uuid4())
    
    mock_catalog_client.get_all_products.return_value = sample_products
    mock_vector_store.upsert_vectors.side_effect = Exception("Vector store error")
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    assert result.status in ["failed", "partial"]
    assert result.products_failed > 0


@pytest.mark.asyncio
async def test_sync_status_tracking(
    sync_service,
    mock_db,
):
    """Test sync status is properly tracked"""
    tenant_id = str(uuid.uuid4())
    
    # Mock sync status query
    mock_db.fetchrow.return_value = {
        'last_sync_at': None,
        'product_count': 100,
        'sync_status': 'completed',
        'error_message': None,
    }
    
    status = await sync_service.get_sync_status(tenant_id)
    
    assert status is not None
    assert status.product_count == 100
    assert status.sync_status == 'completed'

