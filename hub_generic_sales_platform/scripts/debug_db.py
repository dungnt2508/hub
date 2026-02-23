import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.infrastructure.database.engine import get_session_maker
from app.infrastructure.database.models import Tenant, Bot, RuntimeTurn

async def main():
    print("--- Database Inspection ---")
    session_maker = get_session_maker()
    async with session_maker() as db:
        # Tenants
        print("\n--- Tenants ---")
        res = await db.execute(select(Tenant))
        tenants = res.scalars().all()
        for t in tenants:
            print(f"ID: {t.id} | Name: {t.name}")
            
        # Turns
        print("\n--- Conversation Turns (Latest Session) ---")
        # Get latest session ID
        session_stmt = select(RuntimeTurn.session_id).order_by(RuntimeTurn.created_at.desc()).limit(1)
        session_res = await db.execute(session_stmt)
        sid = session_res.scalar_one_or_none()
        if sid:
            print(f"Turns for Session {sid}:")
            stmt = select(RuntimeTurn).where(RuntimeTurn.session_id == sid).order_by(RuntimeTurn.created_at.asc())
            res = await db.execute(stmt)
            turns = res.scalars().all()
            for i, t in enumerate(turns):
                print(f"{i+1}. [{t.speaker}] {t.message[:50]}...")
        else:
            print("No sessions found with turns.")

if __name__ == "__main__":
    asyncio.run(main())
