
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.engine import get_session_maker
from app.infrastructure.database.models.offering import TenantSalesChannel, TenantPriceList

async def debug_mappings():
    session_maker = get_session_maker()
    async with session_maker() as db:
        print("--- Sales Channels ---")
        ch_stmt = select(TenantSalesChannel)
        channels = (await db.execute(ch_stmt)).scalars().all()
        for ch in channels:
            print(f"ID: {ch.id}, Code: {ch.code}, Name: {ch.name}")

        print("\n--- Price Lists ---")
        pl_stmt = select(TenantPriceList)
        price_lists = (await db.execute(pl_stmt)).scalars().all()
        for pl in price_lists:
            print(f"ID: {pl.id}, Code: {pl.code}, ChannelID: {pl.channel_id}")

if __name__ == "__main__":
    asyncio.run(debug_mappings())
