from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.offering import (
    TenantOffering as OfferingModel,
    TenantOfferingVersion as VersionModel,
    TenantOfferingAttributeValue as AttributeValueModel,
    TenantOfferingVariant as VariantModel,
    OfferingStatus
)
from app.infrastructure.database.models.knowledge import (
    DomainAttributeDefinition as AttributeDefModel, 
    TenantAttributeConfig as AttributeConfigModel
)

# Domain Entities
from app.core import domain
from app.core.interfaces.knowledge_repo import IOfferingRepository, IOfferingVersionRepository


class OfferingRepository(BaseRepository[OfferingModel], IOfferingRepository):
    """Offering repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(OfferingModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantOffering]:
        """Get offering with mandatory tenant isolation"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(OfferingModel).where(
            and_(OfferingModel.id == id, OfferingModel.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOffering.model_validate(db_obj) if db_obj else None

    async def get_by_code(self, code: str, tenant_id: str, domain_id: Optional[str] = None) -> Optional[domain.TenantOffering]:
        """Lấy offering theo code, tenant"""
        stmt = select(OfferingModel).where(
            OfferingModel.code == code, 
            OfferingModel.tenant_id == tenant_id
        )
        if domain_id:
            stmt = stmt.where(OfferingModel.domain_id == domain_id)
            
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOffering.model_validate(db_obj) if db_obj else None
    
    async def get_active_offerings(self, tenant_id: str, domain_id: Optional[str] = None) -> List[domain.TenantOffering]:
        """Lấy tất cả offering đang hoạt động của thiết bị"""
        stmt = select(OfferingModel).where(
            OfferingModel.tenant_id == tenant_id, 
            OfferingModel.status == OfferingStatus.ACTIVE
        )
        if domain_id:
            stmt = stmt.where(OfferingModel.domain_id == domain_id)
            
        result = await self.db.execute(stmt)
        return [domain.TenantOffering.model_validate(obj) for obj in result.scalars().all()]


class OfferingVersionRepository(BaseRepository[VersionModel], IOfferingVersionRepository):
    """Offering version repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(VersionModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantOfferingVersion]:
        """Get version with mandatory tenant isolation (via join)"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(VersionModel).join(OfferingModel).where(
            VersionModel.id == id,
            OfferingModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOfferingVersion.model_validate(db_obj) if db_obj else None

    async def get_active_version(self, offering_id: str, tenant_id: str) -> Optional[domain.TenantOfferingVersion]:
        """Lấy phiên bản đang hoạt động của offering với tenant isolation check"""
        stmt = select(VersionModel).join(OfferingModel).where(
            VersionModel.offering_id == offering_id,
            VersionModel.status == OfferingStatus.ACTIVE,
            OfferingModel.tenant_id == tenant_id
        ).order_by(VersionModel.version.desc())
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOfferingVersion.model_validate(db_obj) if db_obj else None

    async def get_latest_version(self, offering_id: str, tenant_id: str) -> Optional[domain.TenantOfferingVersion]:
        """Lấy phiên bản mới nhất (bất kể status) của offering với tenant isolation check"""
        stmt = select(VersionModel).join(OfferingModel).where(
            VersionModel.offering_id == offering_id,
            OfferingModel.tenant_id == tenant_id
        ).order_by(VersionModel.version.desc())
        result = await self.db.execute(stmt)
        db_obj = result.scalars().first()
        return domain.TenantOfferingVersion.model_validate(db_obj) if db_obj else None

    async def semantic_search(
        self,
        tenant_id: str,
        query_vector: List[float],
        threshold: float = 0.8,
        limit: int = 5
    ) -> List[tuple[domain.TenantOfferingVersion, float]]:
        """
        Tìm kiếm Offering semantically qua phiên bản Active.
        """
        distance_limit = 1.0 - threshold
        
        if self.db.bind.dialect.name == "postgresql":
            stmt = select(
                VersionModel, 
                (1.0 - VersionModel.embedding.cosine_distance(query_vector)).label("similarity")
            ).join(OfferingModel).where(
                OfferingModel.tenant_id == tenant_id,
                VersionModel.status == OfferingStatus.ACTIVE,
                VersionModel.embedding.cosine_distance(query_vector) <= distance_limit
            ).order_by(VersionModel.embedding.cosine_distance(query_vector)).limit(limit)
            
            result = await self.db.execute(stmt)
            return [(domain.TenantOfferingVersion.model_validate(r[0]), float(r[1])) for r in result.all()]
        else:
            from app.core.shared.math_utils import cosine_similarity
            stmt = select(VersionModel).join(OfferingModel).where(
                OfferingModel.tenant_id == tenant_id,
                VersionModel.status == OfferingStatus.ACTIVE,
                VersionModel.embedding != None
            )
            result = await self.db.execute(stmt)
            versions = result.scalars().all()
            
            scored = []
            for v in versions:
                sim = cosine_similarity(query_vector, v.embedding)
                if sim >= threshold:
                    scored.append((domain.TenantOfferingVersion.model_validate(v), sim))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]


class OfferingAttributeRepository(BaseRepository[AttributeValueModel]):
    """Offering attribute value repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AttributeValueModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantOfferingAttributeValue]:
        """Get attribute value with mandatory tenant isolation (via complex join)"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.model.__name__}")
            
        stmt = select(AttributeValueModel).join(
            VersionModel, AttributeValueModel.offering_version_id == VersionModel.id
        ).join(
            OfferingModel, VersionModel.offering_id == OfferingModel.id
        ).options(
            selectinload(AttributeValueModel.definition)
        ).where(
            AttributeValueModel.id == id,
            OfferingModel.tenant_id == tenant_id
        )
        
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOfferingAttributeValue.model_validate(db_obj) if db_obj else None

    async def get_by_version(self, version_id: str, tenant_id: str) -> List[domain.TenantOfferingAttributeValue]:
        """Lấy tất cả thuộc tính của một phiên bản offering với tenant isolation check"""
        stmt = select(AttributeValueModel).join(
            VersionModel, AttributeValueModel.offering_version_id == VersionModel.id
        ).join(
            OfferingModel, VersionModel.offering_id == OfferingModel.id
        ).where(
            AttributeValueModel.offering_version_id == version_id,
            OfferingModel.tenant_id == tenant_id
        ).options(joinedload(AttributeValueModel.definition))
        
        result = await self.db.execute(stmt)
        return [domain.TenantOfferingAttributeValue.model_validate(obj) for obj in result.scalars().all()]


class OfferingVariantRepository(BaseRepository[VariantModel]):
    """Offering variant repository with Domain Mapping"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(VariantModel, db)
    
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantOfferingVariant]:
        db_obj = await super().get(id, tenant_id)
        return domain.TenantOfferingVariant.model_validate(db_obj) if db_obj else None

    async def get_by_sku(self, sku: str, tenant_id: str) -> Optional[domain.TenantOfferingVariant]:
        """Lấy variant theo SKU"""
        stmt = select(VariantModel).where(
            VariantModel.sku == sku,
            VariantModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return domain.TenantOfferingVariant.model_validate(db_obj) if db_obj else None
