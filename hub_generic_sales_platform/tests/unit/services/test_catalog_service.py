"""Unit tests for CatalogService"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.services.catalog_service import CatalogService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_offering_for_bot_success():
    """Test successful offering retrieval for bot"""
    
    # Mock database session
    mock_db = AsyncMock()
    service = CatalogService(mock_db)
    
    # Mock offering
    mock_offering = MagicMock()
    mock_offering.id = "off_123"
    mock_offering.code = "LAPTOP_X1"
    mock_offering.status = "active"
    mock_offering.domain_id = "dom_1"
    
    # Mock version
    mock_version = MagicMock()
    mock_version.id = "ver_123"
    mock_version.name = "Laptop X1 Pro"
    mock_version.description = "High-performance laptop"
    mock_version.version = 1
    
    # Mock repositories
    service.offering_repo.get_by_code = AsyncMock(return_value=mock_offering)
    service.version_repo.get_active_version = AsyncMock(return_value=mock_version)
    service.price_repo.get_effective_prices = AsyncMock(return_value=[])
    service.attr_val_repo.get_by_version = AsyncMock(return_value=[])
    service.attr_resolver.resolve_attributes = AsyncMock(return_value=[])
    
    # Mock variant query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Execute
    result = await service.get_offering_for_bot(
        tenant_id="tenant_1",
        offering_code="LAPTOP_X1",
        channel_code="WEB"
    )
    
    # Assertions
    assert result is not None
    assert result["code"] == "LAPTOP_X1"
    assert result["name"] == "Laptop X1 Pro"
    assert result["version"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_offering_for_bot_inactive():
    """Test returns None for inactive offering"""
    
    mock_db = AsyncMock()
    service = CatalogService(mock_db)
    
    mock_offering = MagicMock()
    mock_offering.status = "inactive"  # Inactive
    
    service.offering_repo.get_by_code = AsyncMock(return_value=mock_offering)
    
    result = await service.get_offering_for_bot(
        tenant_id="tenant_1",
        offering_code="INACTIVE_PROD"
    )
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_version():
    """Test publishing an offering version"""
    
    mock_db = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_db.begin.return_value = mock_ctx
    service = CatalogService(mock_db)
    
    mock_offering = MagicMock()
    mock_offering.id = "off_123"
    mock_offering.status = "draft"
    
    mock_target_version = MagicMock()
    mock_target_version.offering_id = "off_123"
    mock_target_version.version = 2
    mock_target_version.status = "draft"
    
    mock_old_active = MagicMock()
    mock_old_active.status = "active"
    
    service.offering_repo.get = AsyncMock(return_value=mock_offering)
    
    # Mock version queries
    # First execute: get target version
    target_result = MagicMock()
    target_result.scalar_one_or_none.return_value = mock_target_version
    
    # Second execute: get currently active versions
    active_result = MagicMock()
    active_result.scalars.return_value.all.return_value = [mock_old_active]
    
    mock_db.execute = AsyncMock()
    mock_db.execute.side_effect = [target_result, active_result]
    mock_db.commit = AsyncMock()
    
    # Execute
    result = await service.publish_version(
        offering_id="off_123",
        version_number=2,
        tenant_id="tenant_1"
    )
    
    # Verify
    assert result is True
    assert mock_target_version.status == "active"
    assert mock_old_active.status == "archived"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_draft_version():
    """Test creating a draft version by copying from latest"""
    
    mock_db = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_db.begin.return_value = mock_ctx
    mock_db.flush = AsyncMock(return_value=None)
    service = CatalogService(mock_db)
    
    mock_offering = MagicMock()
    mock_offering.id = "off_123"
    
    mock_latest_version = MagicMock()
    mock_latest_version.id = "ver_1"
    mock_latest_version.version = 1
    mock_latest_version.name = "Offering V1"
    mock_latest_version.description = "First version"
    
    mock_attr = MagicMock()
    mock_attr.attribute_def_id = "attr_1"
    mock_attr.value_text = "Test"
    
    service.offering_repo.get = AsyncMock(return_value=mock_offering)
    service.version_repo.get_latest_version = AsyncMock(return_value=mock_latest_version)
    service.attr_val_repo.get_by_version = AsyncMock(return_value=[mock_attr])
    
    # Execute
    result = await service.create_draft_version(
        offering_id="off_123",
        tenant_id="tenant_1"
    )
    
    # Verify
    mock_db.add.assert_called()
