import pytest
from app.core.services.catalog_service import CatalogService
from app.infrastructure.database.models.offering import OfferingStatus

pytestmark = pytest.mark.integration

@pytest.mark.integration
@pytest.mark.orchestrator
async def test_get_offering_for_bot_v4(db, offering_v4, channel_web):
    """
    Test logic nạp dữ liệu hợp nhất Offering (Service Layer)
    Sử dụng fixture offering_v4 đã được refactor trong conftest.py
    """
    service = CatalogService(db)
    tenant_id = offering_v4.tenant_id
    offering_code = offering_v4.code
    
    # Thực hiện gọi service
    data = await service.get_offering_for_bot(tenant_id, offering_code, channel_web.code, domain_id=offering_v4.domain_id)
    
    # Kiểm tra tính toàn vẹn dữ liệu
    assert data is not None
    assert data["code"] == offering_code
    assert data["status"] == OfferingStatus.ACTIVE
    assert "price" in data
    assert "inventory" in data
    assert data["name"] == "Standard Offering Name"  # Lấy từ active version
