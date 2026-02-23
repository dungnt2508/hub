"""Knowledge & Catalog Repository Interfaces - Uses domain entities (Clean Architecture)"""

from typing import Optional, List, Any
from abc import abstractmethod
from app.core.interfaces.repository import IRepository
from app.core.domain.knowledge import (
    TenantOffering, TenantOfferingVersion, TenantOfferingVariant, TenantVariantPrice,
    TenantInventoryItem, TenantInventoryLocation, TenantSalesChannel, TenantPriceList,
    TenantOfferingAttributeValue,
    BotFAQ, BotUseCase, BotComparison,
    KnowledgeDomain, DomainAttributeDefinition, TenantAttributeConfig
)


class IOfferingRepository(IRepository[TenantOffering]):
    """Interface cho Offering Repository"""
    
    @abstractmethod
    async def get_by_code(self, code: str, tenant_id: str, domain_id: Optional[str] = None) -> Optional[TenantOffering]:
        """Lấy offering theo code"""
        pass

    @abstractmethod
    async def get_active_offerings(self, tenant_id: str, domain_id: Optional[str] = None) -> List[TenantOffering]:
        """Lấy danh sách offering đang hoạt động"""
        pass


class IOfferingVersionRepository(IRepository[TenantOfferingVersion]):
    """Interface cho Offering Version Repository"""
    
    @abstractmethod
    async def get_active_version(self, offering_id: str, tenant_id: str) -> Optional[TenantOfferingVersion]:
        """Lấy phiên bản đang hoạt động của offering"""
        pass

    @abstractmethod
    async def get_latest_version(self, offering_id: str, tenant_id: str) -> Optional[TenantOfferingVersion]:
        """Lấy phiên bản mới nhất"""
        pass

    @abstractmethod
    async def semantic_search(
        self,
        tenant_id: str,
        query_vector: List[float],
        threshold: float = 0.8,
        limit: int = 5
    ) -> List[tuple[TenantOfferingVersion, float]]:
        """Tìm kiếm semantic"""
        pass


class IDomainAttributeDefinitionRepository(IRepository[DomainAttributeDefinition]):
    """Interface cho Domain Attribute Definition (ONTOLOGY)"""
    
    @abstractmethod
    async def get_by_key(self, key: str, domain_id: str) -> Optional[DomainAttributeDefinition]:
        """Lấy định nghĩa theo key và domain"""
        pass

    @abstractmethod
    async def get_by_domain(self, domain_id: str) -> List[DomainAttributeDefinition]:
        """Lấy tất cả định nghĩa của domain"""
        pass


class ITenantAttributeConfigRepository(IRepository[TenantAttributeConfig]):
    """Interface cho Tenant Attribute Config (OVERRIDE)"""
    
    @abstractmethod
    async def get_config(self, tenant_id: str, attribute_def_id: str) -> Optional[TenantAttributeConfig]:
        """Lấy override config"""
        pass

    @abstractmethod
    async def get_all_for_tenant(self, tenant_id: str, domain_id: Optional[str] = None) -> List[TenantAttributeConfig]:
        """Lấy toàn bộ config của tenant"""
        pass


class IOfferingAttributeValueRepository(IRepository[TenantOfferingAttributeValue]):
    """Interface cho Offering Attribute Value (INSTANCE)"""
    
    @abstractmethod
    async def get_by_version(self, version_id: str, tenant_id: str) -> List[TenantOfferingAttributeValue]:
        """Lấy giá trị theo version"""
        pass

    @abstractmethod
    async def get_by_version_and_key(self, version_id: str, key: str, tenant_id: str) -> Optional[TenantOfferingAttributeValue]:
        """Lấy theo key định nghĩa"""
        pass


class ISalesChannelRepository(IRepository[TenantSalesChannel]):
    """Interface cho Sales Channel Repository"""
    
    @abstractmethod
    async def get_by_code(self, code: str, tenant_id: str) -> Optional[TenantSalesChannel]:
        """Lấy kênh bán hàng theo code"""
        pass


class IPriceListRepository(IRepository[TenantPriceList]):
    """Interface cho Price List Repository"""
    
    @abstractmethod
    async def get_prices_for_offering(self, tenant_id: str, channel_code: str, offering_id: str) -> List[Any]:
        """Lấy giá của tất cả variants của một offering với fallback to default channel"""
        pass


class IInventoryRepository(IRepository[TenantInventoryItem]):
    """Interface cho Inventory Repository"""
    
    @abstractmethod
    async def get_stock_status(self, tenant_id: str, sku: str) -> Optional[dict]:
        """Lấy trạng thái tồn kho qua SKU"""
        pass

    @abstractmethod
    async def get_all_stock_status(self, tenant_id: str, bot_id: Optional[str] = None) -> List[dict]:
        """Lấy trạng thái toàn bộ"""
        pass


class IUseCaseRepository(IRepository[BotUseCase]):
    """Interface cho UseCase Repository"""
    
    @abstractmethod
    async def get_by_offering(self, offering_id: str, tenant_id: str) -> List[BotUseCase]:
        """Lấy UseCase theo offering"""
        pass
    
    @abstractmethod
    async def get_active(self, tenant_id: str, bot_id: Optional[str] = None) -> List[BotUseCase]:
        """Lấy UseCase đang hoạt động"""
        pass


class IFAQRepository(IRepository[BotFAQ]):
    """Interface cho FAQ Repository"""
    
    @abstractmethod
    async def search(self, tenant_id: str, query: str, limit: int = 10, bot_id: Optional[str] = None, domain_id: Optional[str] = None) -> List[BotFAQ]:
        """Tìm kiếm FAQ"""
        pass

    @abstractmethod
    async def semantic_search(
        self,
        tenant_id: str,
        query_vector: List[float],
        threshold: float = 0.8,
        limit: int = 5,
        bot_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> List[tuple[BotFAQ, float]]:
        """Tìm kiếm FAQ bằng vector similarity"""
        pass

    @abstractmethod
    async def get_active(self, tenant_id: str, bot_id: Optional[str] = None, domain_id: Optional[str] = None) -> List[BotFAQ]:
        """Lấy danh sách FAQ đang hoạt động"""
        pass


class IComparisonRepository(IRepository[BotComparison]):
    """Interface cho Comparison Repository"""
    
    @abstractmethod
    async def get_by_offerings(self, tenant_id: str, offering_ids: List[str]) -> List[BotComparison]:
        """Lấy dữ liệu so sánh"""
        pass


class IKnowledgeDomainRepository(IRepository[KnowledgeDomain]):
    """Interface cho Knowledge Domain Repository"""
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[KnowledgeDomain]:
        """Lấy domain theo code (GLOBAL scope)"""
        pass

