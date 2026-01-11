"""
Seed DBA Routing Data Script
Wrapper script để dễ gọi từ command line

Usage:
    python seed_dba_routing_data.py
    python seed_dba_routing_data.py --clean
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic_migrations.auto.seed_dba_routing_data import seed_dba_data, clean_dba_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed DBA domain routing data")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean (delete) all seeded DBA data"
    )
    args = parser.parse_args()
    
    if args.clean:
        print("\n🗑️  Đang xóa dữ liệu DBA routing...")
        asyncio.run(clean_dba_data())
    else:
        print("\n🌱 Đang seed dữ liệu DBA routing...")
        asyncio.run(seed_dba_data())
