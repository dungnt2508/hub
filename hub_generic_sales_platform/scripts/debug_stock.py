import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.engine import get_session_maker
from sqlalchemy import text

async def check():
    print("Checking database inventory data...")
    session_maker = get_session_maker()
    async with session_maker() as db:
        try:
            # 1. Check tenants
            res = await db.execute(text("SELECT id, name FROM tenant"))
            tenants = res.fetchall()
            print(f"Tenants in DB: {tenants}")
            
            res = await db.execute(text("SELECT email, tenant_id FROM user_account"))
            users = res.fetchall()
            print(f"Users in DB: {users}")
            
            res = await db.execute(text("SELECT count(*) FROM inventory_item"))
            print(f"Inventory Items: {res.scalar()}")
            
            res = await db.execute(text("SELECT count(*) FROM product_variant"))
            print(f"Variants: {res.scalar()}")
            
            # 3. Check specific match
            res = await db.execute(text("SELECT id, tenant_id, variant_id, stock_qty FROM inventory_item"))
            ii_rows = res.fetchall()
            print(f"Inventory Items detail:")
            for r in ii_rows:
                print(f"  - ID: {r.id}, Tenant: {r.tenant_id}, VariantID: {r.variant_id}, Qty: {r.stock_qty}")
                
            res = await db.execute(text("SELECT id, tenant_id, sku FROM product_variant"))
            pv_rows = res.fetchall()
            print(f"Variants detail:")
            for r in pv_rows:
                print(f"  - PV ID: {r.id}, Tenant: {r.tenant_id}, SKU: {r.sku}")
                
            # 2. Check view (Final result)
            res = await db.execute(text("SELECT * FROM inventory_status_view"))
            rows = res.fetchall()
            print(f"View content:")
            for row in rows:
                print(f"  - Tenant: {row.tenant_id}, SKU: {row.sku}, Qty: {row.aggregate_qty}, Status: {row.stock_status}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
