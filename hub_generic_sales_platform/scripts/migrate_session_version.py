import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.infrastructure.database.engine import get_engine

async def migrate():
    engine = get_engine()
    print(f"Connecting to database...")
    try:
        async with engine.begin() as conn:
            print("Adding version column to runtime_session table...")
            await conn.execute(text("ALTER TABLE runtime_session ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 0"))
            print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
