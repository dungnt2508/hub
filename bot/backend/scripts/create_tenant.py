#!/usr/bin/env python3
"""
Script để tạo tenant và site_id mapping

Usage:
    python create_tenant.py \
        --name "GSNAKE Catalog" \
        --site-id "catalog-001" \
        --origins "https://gsnake.com,https://www.gsnake.com" \
        --plan "professional"

Hoặc chạy interactive:
    python create_tenant.py
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.backend.domain.tenant.tenant_service import TenantService
from bot.backend.schemas.multi_tenant_types import PlanType
from bot.backend.infrastructure.database_client import database_client
from bot.backend.shared.logger import logger


async def create_tenant_interactive():
    """Interactive mode để tạo tenant"""
    print("\n" + "="*60)
    print("🤖 Tạo Tenant và Site ID cho Bot Service")
    print("="*60 + "\n")
    
    # Get inputs
    name = input("Tên tenant (ví dụ: GSNAKE Catalog): ").strip()
    if not name:
        print("❌ Tên tenant không được để trống")
        return
    
    site_id = input("Site ID (ví dụ: catalog-001): ").strip()
    if not site_id:
        print("❌ Site ID không được để trống")
        return
    
    print("\nNhập danh sách origins (mỗi origin một dòng, Enter để kết thúc):")
    origins = []
    while True:
        origin = input("  Origin: ").strip()
        if not origin:
            break
        origins.append(origin)
    
    if not origins:
        print("❌ Phải có ít nhất một origin")
        return
    
    print("\nChọn plan:")
    print("  1. basic (20 req/min, 1000 req/hour)")
    print("  2. professional (100 req/min, 5000 req/hour)")
    print("  3. enterprise (1000 req/min, 100000 req/hour)")
    plan_choice = input("Chọn (1-3, mặc định: 1): ").strip() or "1"
    
    plan_map = {
        "1": PlanType.BASIC,
        "2": PlanType.PROFESSIONAL,
        "3": PlanType.ENTERPRISE,
    }
    plan = plan_map.get(plan_choice, PlanType.BASIC)
    
    telegram = input("\nBật Telegram bot? (y/N): ").strip().lower() == "y"
    teams = input("Bật Teams bot? (y/N): ").strip().lower() == "y"
    
    # Create tenant
    await create_tenant(name, site_id, origins, plan, telegram, teams)


async def create_tenant(
    name: str,
    site_id: str,
    origins: list,
    plan: str = PlanType.BASIC,
    telegram_enabled: bool = False,
    teams_enabled: bool = False,
):
    """Tạo tenant với các tham số"""
    try:
        # Initialize database connection if not already connected
        if not database_client.pool:
            print("🔄 Đang kết nối database...")
            await database_client.connect()
        
        if not database_client.pool:
            print("❌ Database connection chưa được khởi tạo")
            print("   Hãy đảm bảo database đã chạy và config đúng")
            print("   Kiểm tra DATABASE_URL environment variable")
            return
        
        async with database_client.pool.acquire() as conn:
            tenant_service = TenantService(conn)
            
            print(f"\n🔄 Đang tạo tenant...")
            print(f"   Name: {name}")
            print(f"   Site ID: {site_id}")
            print(f"   Origins: {', '.join(origins)}")
            print(f"   Plan: {plan}")
            
            result = await tenant_service.create_tenant(
                name=name,
                site_id=site_id,
                web_embed_origins=origins,
                plan=plan,
                telegram_enabled=telegram_enabled,
                teams_enabled=teams_enabled,
            )
            
            if result.get("success"):
                data = result["data"]
                print("\n" + "="*60)
                print("✅ Tenant đã được tạo thành công!")
                print("="*60)
                print(f"\n📋 Thông tin tenant:")
                print(f"   Tenant ID: {data['tenant_id']}")
                print(f"   Site ID: {data['site_id']}")
                print(f"   Name: {data['name']}")
                print(f"   Plan: {data['plan']}")
                print(f"\n🔑 Credentials:")
                print(f"   API Key: {data['api_key']}")
                print(f"   JWT Secret: {data['jwt_secret']}")
                print(f"\n⚠️  LƯU Ý: Lưu JWT Secret cẩn thận, không được tiết lộ!")
                print(f"\n📝 Sử dụng trong frontend:")
                print(f"   NEXT_PUBLIC_BOT_SITE_ID={site_id}")
                print(f"   NEXT_PUBLIC_BOT_API_URL=http://localhost:8386")
                print("\n" + "="*60 + "\n")
            else:
                print(f"\n❌ Lỗi: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"Error creating tenant: {e}", exc_info=True)
        print(f"\n❌ Lỗi khi tạo tenant: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Tạo tenant và site_id mapping cho bot service"
    )
    parser.add_argument("--name", help="Tên tenant (ví dụ: GSNAKE Catalog)")
    parser.add_argument("--site-id", dest="site_id", help="Site ID (ví dụ: catalog-001)")
    parser.add_argument(
        "--origins",
        help="Danh sách origins, phân cách bởi dấu phẩy (ví dụ: https://gsnake.com,https://www.gsnake.com)"
    )
    parser.add_argument(
        "--plan",
        choices=["basic", "professional", "enterprise"],
        default="basic",
        help="Rate limit plan (default: basic)"
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Bật Telegram bot"
    )
    parser.add_argument(
        "--teams",
        action="store_true",
        help="Bật Teams bot"
    )
    
    args = parser.parse_args()
    
    # Check if running in interactive mode
    if not args.name or not args.site_id:
        asyncio.run(create_tenant_interactive())
    else:
        # Parse origins
        if not args.origins:
            print("❌ --origins là bắt buộc")
            sys.exit(1)
        
        origins = [o.strip() for o in args.origins.split(",") if o.strip()]
        if not origins:
            print("❌ Phải có ít nhất một origin")
            sys.exit(1)
        
        # Map plan
        plan_map = {
            "basic": PlanType.BASIC,
            "professional": PlanType.PROFESSIONAL,
            "enterprise": PlanType.ENTERPRISE,
        }
        plan = plan_map.get(args.plan, PlanType.BASIC)
        
        asyncio.run(create_tenant(
            name=args.name,
            site_id=args.site_id,
            origins=origins,
            plan=plan,
            telegram_enabled=args.telegram,
            teams_enabled=args.teams,
        ))


if __name__ == "__main__":
    main()

