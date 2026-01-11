"""
Seed Catalog Routing Data Script
Wrapper script để dễ gọi từ command line
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic_migrations.auto.seed_catalog_routing_data import seed_catalog_routing_data, clean_catalog_routing_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Catalog domain routing data")
    parser.add_argument("--clean", action="store_true", help="Clean all seeded Catalog data")
    args = parser.parse_args()
    
    if args.clean:
        print("\n🗑️  Đang xóa dữ liệu Catalog routing...")
        asyncio.run(clean_catalog_routing_data())
    else:
        print("\n🌱 Đang seed dữ liệu Catalog routing...")
        asyncio.run(seed_catalog_routing_data())
