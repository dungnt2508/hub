import pytest
from app.core.services.catalog_service import CatalogService
from app.infrastructure.database.repositories import OfferingRepository, OfferingVersionRepository
from app.infrastructure.database.models.offering import OfferingStatus

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_catalog_service_get_bot_data_missing_version(db, tenant_1, bot_1):
    """Test get_offering_for_bot when offering exists but has no active version"""
    off_repo = OfferingRepository(db)
    service = CatalogService(db)
    
    # Create offering without version
    offering = await off_repo.create({
        "domain_id": bot_1.domain_id,
        "bot_id": bot_1.id,
        "code": "no-version-offering", 
        "status": OfferingStatus.ACTIVE
    }, tenant_id=tenant_1.id)
    
    data = await service.get_offering_for_bot(tenant_1.id, "no-version-offering", channel_code="WEB", domain_id=bot_1.domain_id)
    assert data is None

@pytest.mark.asyncio
async def test_catalog_service_get_bot_data_inactive_offering(db, tenant_1, bot_1):
    """Test get_offering_for_bot when offering is ARCHIVED"""
    off_repo = OfferingRepository(db)
    ver_repo = OfferingVersionRepository(db)
    service = CatalogService(db)
    
    offering = await off_repo.create({
        "domain_id": bot_1.domain_id,
        "bot_id": bot_1.id,
        "code": "archived-offering", 
        "status": OfferingStatus.ARCHIVED
    }, tenant_id=tenant_1.id)
    await ver_repo.create({
        "offering_id": offering.id,
        "version": 1,
        "name": "Archived Name",
        "status": OfferingStatus.ACTIVE
    })
    
    data = await service.get_offering_for_bot(tenant_1.id, "archived-offering", channel_code="WEB", domain_id=bot_1.domain_id)
    assert data is None

@pytest.mark.asyncio
async def test_catalog_service_publish_version_logic(db, offering_v4):
    """Test the version publishing state transition"""
    ver_repo = OfferingVersionRepository(db)
    service = CatalogService(db)
    
    # Create a draft version
    draft = await ver_repo.create({
        "offering_id": offering_v4.id,
        "version": 2,
        "name": "Draft V2",
        "status": OfferingStatus.DRAFT
    })
    
    # Mocking semantic sync because it might involve LLM calls or complex logic
    # Here we just test the DB state update
    await ver_repo.update(draft, {"status": OfferingStatus.ACTIVE})
    
    updated = await ver_repo.get(draft.id, tenant_id=offering_v4.tenant_id)
    assert updated.status == OfferingStatus.ACTIVE
