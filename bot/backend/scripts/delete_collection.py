"""
CLI script to delete Qdrant collection for a tenant
Usage: python -m backend.scripts.delete_collection --tenant-id <tenant_id>
"""
import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.qdrant_client import QdrantClient
from backend.shared.logger import logger


async def delete_collection(tenant_id: str):
    """Delete collection for a tenant"""
    print("=" * 60)
    print(f"Deleting Collection for Tenant: {tenant_id}")
    print("=" * 60)
    
    try:
        client = QdrantClient()
        
        # Check if collection exists
        exists = await client.collection_exists(tenant_id)
        if not exists:
            print(f"⚠️  Collection does not exist for tenant: {tenant_id}")
            return False
        
        # Delete collection
        print(f"🗑️  Deleting collection...")
        result = await client.delete_collection(tenant_id)
        
        if result:
            print(f"✅ Collection deleted successfully!")
            return True
        else:
            print(f"❌ Failed to delete collection")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Delete Qdrant collection for tenant"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        required=True,
        help="Tenant ID to delete collection for",
    )
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(delete_collection(args.tenant_id))
        sys.exit(0 if success else 1)
            
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
