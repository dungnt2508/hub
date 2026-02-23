from sqlalchemy import select
from app.infrastructure.database.models import DomainAttributeDefinition, TenantAttributeConfig, AttributeValueType, AttributeScope

async def seed_ontology(db, tenant_id, domain_map):
    print("Seeding Ontology (Attributes & Definitions)...")
    
    # All attribute definitions across domains
    all_attr_defs = {
        "jewelry": [
            {"key": "clarity", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Độ tinh khiết"},
            {"key": "carat_weight", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.VARIANT, "label": "Trọng lượng (Carat)"},
            {"key": "material", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Chất liệu"},
        ],
        "finance": [
            {"key": "currency", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Loại tiền tệ"},
            {"key": "risk_level", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Mức độ rủi ro"},
        ],
        "accounting": [
            {"key": "tax_code", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Mã số thuế"},
            {"key": "account_category", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Phân loại hộ kinh doanh"},
        ],
        "hr": [
            {"key": "department", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Phòng ban"},
            {"key": "employment_type", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Hình thức lao động"},
        ],
        "market_analysis": [
            {"key": "ticker", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Mã niêm yết (Ticker)"},
            {"key": "exchange", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Sàn giao dịch"},
            {"key": "sector", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Lĩnh vực/Ngành"},
            {"key": "gold_type", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Loại vàng"},
            {"key": "brand", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Thương hiệu"},
        ],
        "food_beverage": [
            {"key": "size", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Kích thước"},
            {"key": "sugar_level", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Mức đường"},
            {"key": "ice_level", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Mức đá"},
            {"key": "topping", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Topping"},
        ],
        "real_estate": [
            {"key": "direction", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Hướng nhà"},
            {"key": "bedrooms", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.OFFERING, "label": "Số phòng ngủ"},
            {"key": "bathrooms", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.OFFERING, "label": "Số toilet"},
            {"key": "area", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.OFFERING, "label": "Diện tích (m2)"},
            {"key": "legal_status", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Pháp lý"},
        ],
        "education": [
            {"key": "level", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Trình độ đầu vào"},
            {"key": "target", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Mục tiêu đầu ra"},
            {"key": "duration", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Thời lượng"},
            {"key": "schedule", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Lịch học"},
        ],
        "used_car": [
            {"key": "odo", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.OFFERING, "label": "ODO (km)"},
            {"key": "year", "value_type": AttributeValueType.NUMBER, "scope": AttributeScope.OFFERING, "label": "Năm sản xuất"},
            {"key": "color", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.VARIANT, "label": "Màu sắc"},
            {"key": "origin", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Xuất xứ"},
            {"key": "owner_history", "value_type": AttributeValueType.TEXT, "scope": AttributeScope.OFFERING, "label": "Lịch sử chủ xe"},
        ]
    }

    full_attr_map = {} # domain -> {key -> id}

    for domain_code, attrs in all_attr_defs.items():
        domain_id = domain_map.get(domain_code)
        if not domain_id: continue
        
        domain_attr_map = {}
        for ad in attrs:
            # 1. Create definition
            res = await db.execute(select(DomainAttributeDefinition).where(
                DomainAttributeDefinition.domain_id == domain_id,
                DomainAttributeDefinition.key == ad["key"]
            ))
            item = res.scalar_one_or_none()
            if not item:
                item = DomainAttributeDefinition(
                    domain_id=domain_id, 
                    key=ad["key"], 
                    value_type=ad["value_type"], 
                    scope=ad["scope"]
                )
                db.add(item)
                await db.flush()
            
            attr_id = str(item.id)
            domain_attr_map[ad["key"]] = attr_id

            # 2. Configure for tenant
            res = await db.execute(select(TenantAttributeConfig).where(
                TenantAttributeConfig.tenant_id == tenant_id,
                TenantAttributeConfig.attribute_def_id == attr_id
            ))
            if not res.scalar_one_or_none():
                db.add(TenantAttributeConfig(
                    tenant_id=tenant_id,
                    attribute_def_id=attr_id,
                    label=ad["label"],
                    display_order=10,
                    is_required=False,
                    ui_config={"placeholder": f"Nhập {ad['label']}..."}
                ))
        
        full_attr_map[domain_code] = domain_attr_map
        print(f"Seeding ontology for domain: {domain_code}")
            
    return full_attr_map
