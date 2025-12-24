"""
Unit tests for Catalog Knowledge Sync Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.knowledge.catalog_knowledge_sync import (
    CatalogKnowledgeSyncService,
    SyncResult,
    SyncStatus,
)
from backend.infrastructure.catalog_client import CatalogProduct
from backend.shared.exceptions import ExternalServiceError


@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    db.fetchrow = AsyncMock()
    db.execute = AsyncMock()
    db.fetch = AsyncMock()
    return db


@pytest.fixture
def mock_catalog_client():
    """Mock catalog client"""
    client = Mock()
    client.get_all_products = AsyncMock(return_value=[])
    client.get_product = AsyncMock(return_value=None)
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
    store.delete_points = AsyncMock(return_value=True)
    return store


@pytest.fixture
def sample_product():
    """Sample product for testing"""
    return CatalogProduct(
        id="prod-123",
        seller_id="seller-456",
        title="Test Product",
        description="This is a test product",
        type="workflow",
        tags=["test", "automation"],
        features=["feature1", "feature2"],
        requirements=["req1"],
        is_free=True,
        status="published",
        review_status="approved",
    )


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
async def test_sync_tenant_products_empty(sync_service, mock_catalog_client, mock_db):
    """Test sync with no products"""
    tenant_id = "test-tenant-123"
    mock_catalog_client.get_all_products.return_value = []
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    assert result.status == "completed"
    assert result.products_synced == 0
    assert result.products_failed == 0
    assert result.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_sync_tenant_products_success(
    sync_service,
    mock_catalog_client,
    mock_ai_provider,
    mock_vector_store,
    sample_product,
):
    """Test successful sync"""
    tenant_id = "test-tenant-123"
    mock_catalog_client.get_all_products.return_value = [sample_product]
    
    result = await sync_service.sync_tenant_products(tenant_id, batch_size=10)
    
    assert result.status == "completed"
    assert result.products_synced == 1
    assert result.products_failed == 0
    assert result.tenant_id == tenant_id
    
    # Verify calls
    mock_vector_store.create_collection.assert_called_once_with(tenant_id)
    mock_ai_provider.embed.assert_called_once()
    mock_vector_store.upsert_vectors.assert_called_once()


@pytest.mark.asyncio
async def test_sync_tenant_products_batch(
    sync_service,
    mock_catalog_client,
    mock_ai_provider,
    mock_vector_store,
):
    """Test sync with batch processing"""
    tenant_id = "test-tenant-123"
    
    # Create multiple products
    products = [
        CatalogProduct(
            id=f"prod-{i}",
            seller_id="seller-1",
            title=f"Product {i}",
            description=f"Description {i}",
            type="workflow",
            tags=[],
            features=[],
            requirements=[],
        )
        for i in range(5)
    ]
    
    mock_catalog_client.get_all_products.return_value = products
    
    result = await sync_service.sync_tenant_products(tenant_id, batch_size=2)
    
    assert result.status == "completed"
    assert result.products_synced == 5
    assert result.products_failed == 0
    
    # Should call upsert multiple times (batch_size=2 means 3 batches)
    assert mock_vector_store.upsert_vectors.call_count == 3


@pytest.mark.asyncio
async def test_sync_tenant_products_embedding_failure(
    sync_service,
    mock_catalog_client,
    mock_ai_provider,
    sample_product,
):
    """Test sync with embedding generation failure"""
    tenant_id = "test-tenant-123"
    mock_catalog_client.get_all_products.return_value = [sample_product]
    mock_ai_provider.embed.side_effect = Exception("Embedding error")
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    # Should complete but with failures
    assert result.status in ["partial", "completed"]
    assert result.products_failed > 0


@pytest.mark.asyncio
async def test_sync_product_success(
    sync_service,
    mock_ai_provider,
    mock_vector_store,
    sample_product,
):
    """Test single product sync"""
    tenant_id = "test-tenant-123"
    
    result = await sync_service.sync_product(tenant_id, sample_product)
    
    assert result is True
    mock_ai_provider.embed.assert_called_once()
    mock_vector_store.upsert_vectors.assert_called_once()


@pytest.mark.asyncio
async def test_delete_product(sync_service, mock_vector_store, mock_db):
    """Test product deletion"""
    tenant_id = "test-tenant-123"
    product_id = "prod-123"
    
    result = await sync_service.delete_product(tenant_id, product_id)
    
    assert result is True
    mock_vector_store.delete_points.assert_called_once_with(tenant_id, [product_id])
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_sync_status(sync_service, mock_db):
    """Test getting sync status"""
    tenant_id = "test-tenant-123"
    
    # Mock database response
    mock_row = {
        'last_sync_at': datetime.now(),
        'product_count': 100,
        'sync_status': 'completed',
        'error_message': None,
    }
    mock_db.fetchrow.return_value = mock_row
    
    status = await sync_service.get_sync_status(tenant_id)
    
    assert status is not None
    assert status.tenant_id == tenant_id
    assert status.product_count == 100
    assert status.sync_status == 'completed'
    mock_db.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_sync_status_not_found(sync_service, mock_db):
    """Test getting sync status when not found"""
    tenant_id = "test-tenant-123"
    mock_db.fetchrow.return_value = None
    
    status = await sync_service.get_sync_status(tenant_id)
    
    assert status is None


@pytest.mark.asyncio
async def test_sync_tenant_products_catalog_error(
    sync_service,
    mock_catalog_client,
):
    """Test sync with catalog API error"""
    tenant_id = "test-tenant-123"
    mock_catalog_client.get_all_products.side_effect = ExternalServiceError("Catalog API error")
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    assert result.status == "failed"
    assert result.error_message is not None
    assert "Catalog API error" in result.error_message


@pytest.mark.asyncio
async def test_sync_tenant_products_vector_store_error(
    sync_service,
    mock_catalog_client,
    mock_vector_store,
    sample_product,
):
    """Test sync with vector store error"""
    tenant_id = "test-tenant-123"
    mock_catalog_client.get_all_products.return_value = [sample_product]
    mock_vector_store.upsert_vectors.side_effect = Exception("Vector store error")
    
    result = await sync_service.sync_tenant_products(tenant_id)
    
    # Should handle error gracefully
    assert result.status in ["failed", "partial"]
    assert result.products_failed > 0

