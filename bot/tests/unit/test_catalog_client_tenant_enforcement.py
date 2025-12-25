"""
Unit tests for Catalog Client Tenant ID Enforcement
Task 4.4: Security tests for tenant_id enforcement
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from backend.infrastructure.catalog_client import CatalogClient, ExternalServiceError


class TestCatalogClientTenantIDEnforcement:
    """Test that catalog client enforces tenant_id requirement"""
    
    @pytest.fixture
    def catalog_client(self):
        """Create catalog client instance"""
        return CatalogClient(base_url="http://localhost:8385")
    
    @pytest.mark.asyncio
    async def test_get_products_rejects_none_tenant_id(self, catalog_client):
        """Test that get_products rejects None tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_products(tenant_id=None)
    
    @pytest.mark.asyncio
    async def test_get_products_rejects_empty_tenant_id(self, catalog_client):
        """Test that get_products rejects empty tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_products(tenant_id="")
        
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_products(tenant_id="   ")
    
    @pytest.mark.asyncio
    async def test_get_products_includes_tenant_id_in_params(self, catalog_client):
        """Test that get_products includes tenant_id in request params"""
        tenant_id = "00000000-0000-0000-0000-000000000001"
        
        with patch.object(catalog_client, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={
                "success": True,
                "data": {
                    "products": [],
                    "total": 0,
                    "limit": 100,
                    "offset": 0
                }
            })
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            await catalog_client.get_products(
                tenant_id=tenant_id,
                status="published",
                limit=50
            )
            
            # Verify tenant_id was included in params
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "params" in call_args.kwargs
            assert call_args.kwargs["params"]["tenant_id"] == tenant_id
    
    @pytest.mark.asyncio
    async def test_get_all_products_rejects_none_tenant_id(self, catalog_client):
        """Test that get_all_products rejects None tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_all_products(tenant_id=None)
    
    @pytest.mark.asyncio
    async def test_get_all_products_rejects_empty_tenant_id(self, catalog_client):
        """Test that get_all_products rejects empty tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_all_products(tenant_id="")
    
    @pytest.mark.asyncio
    async def test_get_all_products_passes_tenant_id_to_get_products(self, catalog_client):
        """Test that get_all_products passes tenant_id to get_products"""
        tenant_id = "00000000-0000-0000-0000-000000000001"
        
        with patch.object(catalog_client, 'get_products') as mock_get_products:
            mock_response = MagicMock()
            mock_response.products = []
            mock_response.total = 0
            mock_get_products.return_value = mock_response
            
            await catalog_client.get_all_products(tenant_id=tenant_id)
            
            # Verify get_products was called with tenant_id
            mock_get_products.assert_called()
            # Check that tenant_id was passed in all calls
            for call in mock_get_products.call_args_list:
                assert call.kwargs.get("tenant_id") == tenant_id
    
    @pytest.mark.asyncio
    async def test_get_product_rejects_none_tenant_id(self, catalog_client):
        """Test that get_product rejects None tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_product("product-id", tenant_id=None)
    
    @pytest.mark.asyncio
    async def test_get_product_rejects_empty_tenant_id(self, catalog_client):
        """Test that get_product rejects empty tenant_id"""
        with pytest.raises(ValueError, match="tenant_id is required"):
            await catalog_client.get_product("product-id", tenant_id="")
    
    @pytest.mark.asyncio
    async def test_get_product_includes_tenant_id_in_params(self, catalog_client):
        """Test that get_product includes tenant_id in request params"""
        product_id = "00000000-0000-0000-0000-000000000002"
        tenant_id = "00000000-0000-0000-0000-000000000001"
        
        with patch.object(catalog_client, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={
                "success": True,
                "data": {
                    "id": product_id,
                    "title": "Test Product",
                    "tenantId": tenant_id,
                }
            })
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            await catalog_client.get_product(product_id, tenant_id=tenant_id)
            
            # Verify tenant_id was included in params
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "params" in call_args.kwargs
            assert call_args.kwargs["params"]["tenant_id"] == tenant_id


class TestCatalogClientCallSites:
    """Test that all call sites pass tenant_id"""
    
    @pytest.mark.asyncio
    async def test_catalog_knowledge_sync_passes_tenant_id(self):
        """Test that catalog_knowledge_sync passes tenant_id"""
        from backend.knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
        from unittest.mock import MagicMock, AsyncMock, patch
        
        mock_db = MagicMock()
        mock_catalog_client = MagicMock()
        mock_catalog_client.get_all_products = AsyncMock(return_value=[])
        
        with patch('backend.knowledge.catalog_knowledge_sync.CatalogClient') as mock_client_class:
            mock_client_class.return_value = mock_catalog_client
            
            service = CatalogKnowledgeSyncService(mock_db, catalog_client=mock_catalog_client)
            tenant_id = "00000000-0000-0000-0000-000000000001"
            
            # This will call get_all_products
            await service.sync_knowledge(tenant_id, batch_size=10)
            
            # Verify tenant_id was passed
            mock_catalog_client.get_all_products.assert_called()
            call_args = mock_catalog_client.get_all_products.call_args
            assert call_args.kwargs.get("tenant_id") == tenant_id
    
    @pytest.mark.asyncio
    async def test_catalog_webhook_passes_tenant_id(self):
        """Test that catalog_webhook passes tenant_id to get_product"""
        from backend.interface.webhooks.catalog_webhook import CatalogWebhookHandler
        from unittest.mock import MagicMock, AsyncMock, patch
        
        mock_db = MagicMock()
        mock_catalog_client = MagicMock()
        mock_product = MagicMock()
        mock_product.status = "published"
        mock_product.review_status = "approved"
        mock_catalog_client.get_product = AsyncMock(return_value=mock_product)
        
        with patch('backend.interface.webhooks.catalog_webhook.CatalogClient') as mock_client_class:
            mock_client_class.return_value = mock_catalog_client
            
            handler = CatalogWebhookHandler(mock_db)
            handler.catalog_client = mock_catalog_client
            
            tenant_id = "00000000-0000-0000-0000-000000000001"
            product_id = "00000000-0000-0000-0000-000000000002"
            
            # This will call get_product
            await handler.handle_product_event(tenant_id, "created", product_id)
            
            # Verify tenant_id was passed
            mock_catalog_client.get_product.assert_called_once()
            call_args = mock_catalog_client.get_product.call_args
            assert call_args.args[0] == product_id
            assert call_args.kwargs.get("tenant_id") == tenant_id

