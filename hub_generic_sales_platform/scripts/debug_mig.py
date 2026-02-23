
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.database.base import Base

async def run_test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        from app.infrastructure.database.models import bot, knowledge, offering, runtime, tenant
        await conn.run_sync(Base.metadata.create_all)
    
    from tests.integration.services.test_migration_service import test_migration_lifecycle
    from app.infrastructure.database.models.tenant import Tenant
    
    async with async_session() as db:
        tenant = Tenant(id="t1", name="Tenant 1")
        db.add(tenant)
        await db.commit()
        
        try:
            await test_migration_lifecycle(db, tenant)
            print("SUCCESS")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
