"""
CLI script to create a new tenant in bot database
Usage: python -m backend.scripts.create_tenant --name <tenant_name> [--site-id <site_id>] [--origins <origin1,origin2>]
"""
import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.domain.tenant.tenant_service import TenantService
from backend.shared.logger import logger
from backend.schemas.multi_tenant_types import PlanType
import asyncpg


async def get_db_connection():
    """Get database connection"""
    # Get DATABASE_URL from environment
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_pw@localhost:5432/bot_db")
    
    # Parse DATABASE_URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(db_url)


async def create_tenant(
    name: str,
    site_id: str = None,
    origins: list = None,
    plan: str = PlanType.BASIC,
):
    """Create tenant in database"""
    print("=" * 60)
    print(f"Creating Tenant: {name}")
    print("=" * 60)
    
    if not origins:
        origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "*"  # Allow all origins in development
        ]
    
    db = None
    try:
        db = await get_db_connection()
        tenant_service = TenantService(db)
        
        result = await tenant_service.create_tenant(
            name=name,
            site_id=site_id,
            web_embed_origins=origins,
            plan=plan,
        )
        
        print(f"\n✅ Tenant created successfully!")
        print(f"   Tenant ID: {result['tenant_id']}")
        print(f"   Name: {result['name']}")
        print(f"   Site ID: {result.get('site_id', 'N/A')}")
        print(f"   API Key: {result['api_key']}")
        print(f"   Plan: {result['plan']}")
        print(f"   Web Embed Origins: {origins}")
        print(f"\n💡 Use this site_id in frontend: {result.get('site_id', name)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            await db.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Create a new tenant in bot database"
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Tenant name (must be unique, e.g., 'n8n-market')",
    )
    parser.add_argument(
        "--site-id",
        type=str,
        default=None,
        help="Site ID (optional, will be auto-generated if not provided)",
    )
    parser.add_argument(
        "--origins",
        type=str,
        default=None,
        help="Comma-separated list of allowed origins (default: http://localhost:3000,http://localhost:3001,*)",
    )
    parser.add_argument(
        "--plan",
        type=str,
        choices=["basic", "professional", "enterprise"],
        default="basic",
        help="Tenant plan (default: basic)",
    )
    
    args = parser.parse_args()
    
    origins = None
    if args.origins:
        origins = [o.strip() for o in args.origins.split(",")]
    
    try:
        success = asyncio.run(create_tenant(
            name=args.name,
            site_id=args.site_id,
            origins=origins,
            plan=args.plan,
        ))
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
