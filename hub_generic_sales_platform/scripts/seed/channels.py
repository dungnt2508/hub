"""
Seed Sales Channels and link Price Lists
"""
import uuid
from sqlalchemy import select
from app.infrastructure.database.models.offering import TenantSalesChannel, TenantPriceList

async def seed_channels(db, tenant_id):
    print("Seeding Sales Channels...")
    
    print(f"Using tenant_id: {tenant_id}")
    
    # Channel definitions
    channels_data = [
        {"code": "WEB", "name": "Web Channel"},
        {"code": "ZALO", "name": "Zalo API"},
        {"code": "FACEBOOK", "name": "Facebook Messenger"},
    ]
    
    channel_map = {}
    for ch_data in channels_data:
        # Check if channel exists
        result = await db.execute(
            select(TenantSalesChannel).where(
                TenantSalesChannel.code == ch_data["code"],
                TenantSalesChannel.tenant_id == tenant_id
            )
        )
        channel = result.scalar_one_or_none()
        
        if not channel:
            channel = TenantSalesChannel(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                code=ch_data["code"],
                name=ch_data["name"],
                is_active=True
            )
            db.add(channel)
            await db.flush()
            print(f"✅ Created channel: {ch_data['code']}")
        else:
            print(f"ℹ️  Channel already exists: {ch_data['code']}")
        
        channel_map[ch_data["code"]] = str(channel.id)
    
    return channel_map
