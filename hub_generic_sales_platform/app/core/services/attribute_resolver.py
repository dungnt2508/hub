"""
Attribute Resolver Service - Resolves attribute definitions with tenant-specific configs
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import TenantAttributeConfigRepository
from app.infrastructure.database.models.offering import TenantOfferingAttributeValue
from app.infrastructure.database.models.knowledge import DomainAttributeDefinition, TenantAttributeConfig


class AttributeResolverService:
    """Service để resolve attributes với tenant-specific configs (label, is_display, display_order)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repo = TenantAttributeConfigRepository(db)
    
    async def resolve_attributes(
        self,
        tenant_id: str,
        attribute_values: List[TenantOfferingAttributeValue],
        filter_display_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Resolve attribute values với tenant-specific configs.
        
        Args:
            tenant_id: Tenant ID
            attribute_values: List of TenantProductAttributeValue
            filter_display_only: Nếu True, chỉ trả về attributes có is_display=True
        
        Returns:
            List of resolved attributes với format:
            {
                "id": str,
                "key": str,              # from definition
                "label": str,            # from tenant_config or definition.key
                "value": Any,            # resolved value
                "value_type": str,
                "is_display": bool,
                "display_order": int,
                "is_searchable": bool
            }
        """
        if not attribute_values:
            return []
        
        # Lấy tất cả configs cho tenant (batch load)
        attr_def_ids = [av.attribute_def_id for av in attribute_values if av.definition]
        configs_map = {}
        if attr_def_ids:
            # Load configs theo batch
            for attr_def_id in attr_def_ids:
                config = await self.config_repo.get_config(tenant_id, attr_def_id)
                if config:
                    configs_map[attr_def_id] = config
        
        resolved = []
        for av in attribute_values:
            if not av.definition:
                continue
            
            config = configs_map.get(av.attribute_def_id)
            
            # Resolve value
            value = av.value_text
            if av.value_number is not None:
                value = float(av.value_number)
            elif av.value_bool is not None:
                value = av.value_bool
            elif av.value_json is not None:
                value = av.value_json
            
            # Resolve label (tenant config hoặc fallback definition.key)
            label = config.label if config and config.label else av.definition.key
            
            # Resolve display flags
            is_display = config.is_display if config else True  # Default True nếu không có config
            display_order = config.display_order if config else 0
            is_searchable = config.is_searchable if config else False
            
            # Filter theo is_display nếu cần
            if filter_display_only and not is_display:
                continue
            
            resolved.append({
                "id": av.id,
                "offering_version_id": av.offering_version_id,
                "attribute_def_id": av.attribute_def_id,
                "key": av.definition.key,
                "label": label,
                "value": value,
                "value_type": av.definition.value_type,
                "is_display": is_display,
                "display_order": display_order,
                "is_searchable": is_searchable
            })
        
        # Sort theo display_order
        resolved.sort(key=lambda x: x["display_order"])
        return resolved
