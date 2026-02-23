"""
Unified Seed Data Script for Iris Hub V4 (Modular Refactor).
Orchestrates seeding across Tenants, Blueprint, Ontology, Bots, and Knowledge Base.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.infrastructure.database.engine import get_session_maker
from scripts.seed.tenants import seed_tenants
from scripts.seed.blueprint import seed_blueprint
from scripts.seed.ontology import seed_ontology
from scripts.seed.bots import seed_bots
from scripts.seed.knowledge import seed_knowledge
from scripts.seed.channels import seed_channels

async def main():
    print("Starting Iris Hub V4 Modular Seeding...")
    session_maker = get_session_maker()
    
    async with session_maker() as db:
        try:
            # 1. Tenants & Users
            tenant_ids = await seed_tenants(db)
            
            # 2. Blueprint (Capabilities & Domains)
            domain_map, cap_map = await seed_blueprint(db)
            
            for key, tenant_id in tenant_ids.items():
                print(f"\n--- Seeding for Tenant: {key} ({tenant_id}) ---")
                
                # 3. Ontology (Attribute Definitions & Configs)
                full_attr_map = await seed_ontology(db, tenant_id, domain_map)
                
                # 4. Bots & Versions
                bot_id_map = await seed_bots(db, tenant_id, domain_map, cap_map)
                
                # 5. Knowledge Base (Products, FAQs, Guardrails)
                await seed_knowledge(db, tenant_id, bot_id_map, domain_map, full_attr_map, tenant_key=key)
                
                # 5.5. Sales Channels (AFTER Knowledge to ensure price_list exists)
                await seed_channels(db, tenant_id)
            
            await db.commit()
            print("\nGlobal Seeding completed successfully!")
            print("Tenant IDs:", tenant_ids)

        except Exception as e:
            await db.rollback()
            print(f"Error during seeding: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
