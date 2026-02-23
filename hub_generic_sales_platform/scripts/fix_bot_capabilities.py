import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.engine import get_session_maker
from app.infrastructure.database.models import Bot, BotVersion, SystemCapability, BotCapability

async def main():
    print("--- Adding 'offering_details' capability to 'iris-auto-ai' ---")
    session_maker = get_session_maker()
    async with session_maker() as db:
        # 1. Get the bot
        res = await db.execute(select(Bot).where(Bot.code == 'iris-auto-ai'))
        bot = res.scalar_one_or_none()
        if not bot:
            print("Error: Bot 'iris-auto-ai' not found.")
            return

        print(f"Found Bot: {bot.name} (ID: {bot.id})")

        # 2. Get the active version
        res = await db.execute(select(BotVersion).where(BotVersion.bot_id == bot.id, BotVersion.is_active == True))
        version = res.scalar_one_or_none()
        if not version:
            print("Error: Active version not found.")
            return
            
        print(f"Active Version: {version.version} (ID: {version.id})")

        # 3. Get or Create 'offering_details' capability
        res = await db.execute(select(SystemCapability).where(SystemCapability.code == 'offering_details'))
        cap = res.scalar_one_or_none()
        if not cap:
            print("Capability 'offering_details' not found in SystemCapability. Creating it...")
            cap = SystemCapability(
                code="offering_details",
                name="Offering Details",
                description="View detailed information about an offering"
            )
            db.add(cap)
            await db.flush()
        
        print(f"Capability: {cap.name} (ID: {cap.id})")

        # 4. Assign capability to bot version
        # Check if already assigned
        res = await db.execute(select(BotCapability).where(
            BotCapability.bot_version_id == version.id,
            BotCapability.capability_id == cap.id
        ))
        if res.scalar_one_or_none():
            print("Capability already assigned.")
        else:
            link = BotCapability(bot_version_id=version.id, capability_id=cap.id)
            db.add(link)
            await db.commit()
            print("Successfully assigned 'offering_details' capability to 'iris-auto-ai'.")

if __name__ == "__main__":
    asyncio.run(main())
