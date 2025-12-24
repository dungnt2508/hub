"""
CLI script to sync catalog knowledge base
Usage: python -m backend.scripts.sync_catalog_knowledge --tenant-id <tenant_id>
"""
import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
from backend.domain.tenant.tenant_service import TenantService
from backend.shared.config import config
from backend.shared.logger import logger
import asyncpg


async def get_db_connection():
    """Get database connection"""
    # Get DATABASE_URL from environment
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_password@localhost:5432/bot_db")
    
    # Parse DATABASE_URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(db_url)


async def sync_tenant(tenant_id: str, batch_size: int = 10):
    """Sync knowledge base for a tenant"""
    print("=" * 60)
    print(f"Syncing Knowledge Base for Tenant: {tenant_id}")
    print("=" * 60)
    
    # Get database connection
    db = await get_db_connection()
    
    try:
        # Verify tenant exists
        tenant_service = TenantService(db)
        tenant_config = await tenant_service.get_tenant_config(tenant_id)
        
        if not tenant_config:
            print(f"❌ Tenant not found: {tenant_id}")
            return False
        
        print(f"✅ Tenant found: {tenant_config.name}")
        
        # Get current sync status
        sync_service = CatalogKnowledgeSyncService(db)
        current_status = await sync_service.get_sync_status(tenant_id)
        
        if current_status:
            print(f"\n📊 Current Status:")
            print(f"   - Last sync: {current_status.last_sync_at}")
            print(f"   - Products synced: {current_status.product_count}")
            print(f"   - Status: {current_status.sync_status}")
            if current_status.error_message:
                print(f"   - Error: {current_status.error_message}")
        
        # Confirm sync
        print(f"\n🚀 Starting sync...")
        
        # Run sync
        result = await sync_service.sync_tenant_products(
            tenant_id=tenant_id,
            batch_size=batch_size,
        )
        
        # Print results
        print(f"\n{'=' * 60}")
        print(f"Sync Results")
        print(f"{'=' * 60}")
        print(f"Status: {result.status}")
        print(f"Products synced: {result.products_synced}")
        print(f"Products failed: {result.products_failed}")
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        
        if result.error_message:
            print(f"\n⚠️  Error: {result.error_message}")
        
        if result.status == "completed":
            print(f"\n✅ Sync completed successfully!")
            return True
        elif result.status == "partial":
            print(f"\n⚠️  Sync completed with some failures")
            return True
        else:
            print(f"\n❌ Sync failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.close()


async def list_tenants():
    """List all tenants"""
    print("=" * 60)
    print("Available Tenants")
    print("=" * 60)
    
    db = await get_db_connection()
    
    try:
        tenant_service = TenantService(db)
        tenants = await tenant_service.list_tenants(limit=100)
        
        if not tenants:
            print("No tenants found")
            return
        
        for tenant in tenants:
            print(f"\n- {tenant['name']}")
            print(f"  ID: {tenant['id']}")
            print(f"  Plan: {tenant.get('plan', 'N/A')}")
            print(f"  Created: {tenant.get('created_at', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Sync catalog knowledge base for tenant"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Tenant ID to sync",
    )
    parser.add_argument(
        "--list-tenants",
        action="store_true",
        help="List all available tenants",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing products (default: 10)",
    )
    
    args = parser.parse_args()
    
    try:
        if args.list_tenants:
            success = asyncio.run(list_tenants())
        elif args.tenant_id:
            success = asyncio.run(sync_tenant(args.tenant_id, args.batch_size))
            sys.exit(0 if success else 1)
        else:
            parser.print_help()
            sys.exit(1)
            
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

