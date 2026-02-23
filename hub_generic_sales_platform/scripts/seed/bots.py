import uuid
from sqlalchemy import select
from app.infrastructure.database.models import Bot, BotVersion, BotCapability, BotChannelConfig

async def seed_bots(db, tenant_id, domain_map, cap_map):
    print("Seeding Bots & Versions...")
    
    bots_to_create = [
        # {
        #     "code": "iris-jewelry-ai",
        #     "name": "Chuyên gia Trang sức Iris",
        #     "domain": "jewelry",
        #     "caps": ["offering_search", "offering_comparison", "offering_inventory_check"]
        # },
        # {
        #     "code": "iris-finance-ai",
        #     "name": "Trợ lý Tài chính Doanh nghiệp",
        #     "domain": "finance",
        #     "caps": ["policy_lookup", "transaction_analysis"]
        # },
        # {
        #     "code": "iris-accounting-ai",
        #     "name": "Chuyên viên Kế toán & Thuế",
        #     "domain": "accounting",
        #     "caps": ["policy_lookup", "transaction_analysis"]
        # },
        # {
        #     "code": "iris-hr-ai",
        #     "name": "Trợ lý Nhân sự & Phúc lợi",
        #     "domain": "hr",
        #     "caps": ["policy_lookup"]
        # },
        # {
        #     "code": "iris-market-ai",
        #     "name": "Chuyên gia Phân tích Thị trường",
        #     "domain": "market_analysis",
        #     "caps": ["market_data_realtime", "strategic_analysis", "policy_lookup"]
        # },
        {
            "code": "iris-food-ai",
            "name": "Trợ lý Vận hành F&B",
            "domain": "food_beverage",
            "caps": ["offering_search", "offering_inventory_check", "policy_lookup"]
        },
        {
            "code": "iris-property-ai",
            "name": "Chuyên gia Bất động sản",
            "domain": "real_estate",
            "caps": ["offering_search", "offering_comparison", "policy_lookup"]
        },
        {
            "code": "iris-edu-ai",
            "name": "Trợ lý Tuyển sinh Ivy",
            "domain": "education",
            "caps": ["assessment_test", "offering_search", "policy_lookup"]
        },
        {
            "code": "iris-fin-ai",
            "name": "Chuyên gia Tài chính F888",
            "domain": "finance",
            "caps": ["credit_scoring", "policy_lookup"]
        },
        {
            "code": "iris-auto-ai",
            "name": "Chuyên gia Định giá Xe",
            "domain": "used_car",
            "caps": ["trade_in_valuation", "offering_search", "offering_comparison"]
        }
    ]

    bot_id_map = {}

    for b_data in bots_to_create:
        domain_id = domain_map.get(b_data["domain"])
        if not domain_id: continue

        res = await db.execute(select(Bot).where(
            Bot.tenant_id == tenant_id,
            Bot.code == b_data["code"]
        ))
        bot = res.scalar_one_or_none()
        if not bot:
            bot = Bot(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                domain_id=domain_id,
                code=b_data["code"],
                name=b_data["name"]
            )
            db.add(bot)
            await db.flush()
            print(f"Created Bot Instance: {b_data['code']}")
        
        bot_id = str(bot.id)
        bot_id_map[b_data["domain"]] = bot_id

        # Bot Version & Capabilities
        res = await db.execute(select(BotVersion).where(
            BotVersion.bot_id == bot_id,
            BotVersion.version == 1
        ))
        v1 = res.scalar_one_or_none()
        if not v1:
            v1 = BotVersion(
                id=str(uuid.uuid4()),
                bot_id=bot_id,
                version=1,
                is_active=True
            )
            db.add(v1)
            await db.flush()
            
            # Add specific capabilities
            for cap_code in b_data["caps"]:
                cap_id = cap_map.get(cap_code)
                if cap_id:
                    db.add(BotCapability(bot_version_id=v1.id, capability_id=cap_id))
            
            db.add(BotChannelConfig(
                bot_version_id=v1.id,
                channel_code="webchat",
                config={"theme": "premium", "welcome_msg": f"Chào mừng bạn đến với {b_data['name']}!"}
            ))
            print(f"Created {b_data['code']} v1 with {len(b_data['caps'])} capabilities")
        
    return bot_id_map
