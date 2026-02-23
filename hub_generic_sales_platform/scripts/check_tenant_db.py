import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, text
from app.infrastructure.database.engine import get_session_maker
from app.infrastructure.database.models.tenant import Tenant

async def check_tenant():
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Check all tenants
        stmt = select(Tenant)
        result = await session.execute(stmt)
        tenants = result.scalars().all()
        
        print("\n--- TENANTS IN DATABASE ---")
        if not tenants:
            print("No tenants found.")
        for t in tenants:
            print(f"ID: {t.id} | Name: {t.name} | Status: {t.status}")
        
        # Check specific ID 222
        stmt_222 = select(Tenant).where(Tenant.id == "222")
        res_222 = await session.execute(stmt_222)
        t_222 = res_222.scalar_one_or_none()
        
        if t_222:
            print(f"\nTenant 222 exists! Status: {t_222.status}")
        else:
            print(f"\nTenant 222 does NOT exist.")

if __name__ == "__main__":
    asyncio.run(check_tenant())
