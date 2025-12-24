"""
Scheduled Sync Script - Sync knowledge base for all active tenants
Usage: Run as cron job or scheduled task
Example: python -m backend.scripts.scheduled_sync_catalog_knowledge
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
from backend.domain.tenant.tenant_service import TenantService
from backend.shared.logger import logger
import asyncpg


async def get_db_connection():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_password@localhost:5432/bot_db")
    
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(db_url)


async def sync_all_tenants(batch_size: int = 10):
    """Sync knowledge base for all active tenants"""
    print("=" * 60)
    print("Scheduled Knowledge Base Sync")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    db = await get_db_connection()
    
    try:
        # Get all tenants
        tenant_service = TenantService(db)
        tenants = await tenant_service.list_tenants(limit=1000)
        
        if not tenants:
            print("No tenants found")
            return
        
        print(f"\nFound {len(tenants)} tenants")
        
        # Sync each tenant
        sync_service = CatalogKnowledgeSyncService(db)
        
        total_synced = 0
        total_failed = 0
        results = []
        
        for tenant in tenants:
            tenant_id = tenant['id']
            tenant_name = tenant.get('name', 'Unknown')
            
            print(f"\n[{total_synced + total_failed + 1}/{len(tenants)}] Syncing tenant: {tenant_name} ({tenant_id})")
            
            try:
                result = await sync_service.sync_tenant_products(
                    tenant_id=tenant_id,
                    batch_size=batch_size,
                )
                
                if result.status == "completed":
                    total_synced += 1
                    print(f"  ✅ Success: {result.products_synced} products synced in {result.duration_seconds:.2f}s")
                elif result.status == "partial":
                    total_synced += 1
                    total_failed += 1
                    print(f"  ⚠️  Partial: {result.products_synced} synced, {result.products_failed} failed")
                else:
                    total_failed += 1
                    print(f"  ❌ Failed: {result.error_message}")
                
                results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": result.status,
                    "products_synced": result.products_synced,
                    "products_failed": result.products_failed,
                    "duration": result.duration_seconds,
                })
                
            except Exception as e:
                total_failed += 1
                print(f"  ❌ Error: {e}")
                logger.error(
                    f"Failed to sync tenant {tenant_id}: {e}",
                    exc_info=True,
                    extra={"tenant_id": tenant_id}
                )
                results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": "error",
                    "error": str(e),
                })
        
        # Summary
        print("\n" + "=" * 60)
        print("Sync Summary")
        print("=" * 60)
        print(f"Total tenants: {len(tenants)}")
        print(f"Successful: {total_synced}")
        print(f"Failed: {total_failed}")
        print(f"Completed at: {datetime.now().isoformat()}")
        
        # Log summary
        logger.info(
            f"Scheduled sync completed: {total_synced} successful, {total_failed} failed",
            extra={
                "total_tenants": len(tenants),
                "successful": total_synced,
                "failed": total_failed,
            }
        )
        
        return results
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Scheduled sync failed: {e}", exc_info=True)
        return None
    finally:
        await db.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scheduled sync of catalog knowledge base for all tenants"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing products (default: 10)",
    )
    
    args = parser.parse_args()
    
    try:
        results = asyncio.run(sync_all_tenants(batch_size=args.batch_size))
        sys.exit(0 if results else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

