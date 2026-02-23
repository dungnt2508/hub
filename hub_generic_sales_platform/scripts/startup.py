#!/usr/bin/env python3
"""
Startup script for IRIS Hub
Tự động chạy migration trước khi start backend
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from sqlalchemy import create_engine, text

# Determine absolute project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for encoding
os.environ["PYTHONUTF8"] = "1"

from app.core.config.settings import get_settings
settings = get_settings()

async def wait_for_database(max_retries=30, delay=5):
    """Chờ database sẵn sàng"""

    # Debug: Print database URL
    print(f"📡 Database URL: {settings.database_url}")
    print(f"📡 Sync URL: {settings.sync_url}")
    
    for attempt in range(max_retries):
        try:
            # Test database connection
            sync_url = settings.sync_url
            print(f"🔍 Testing connection with: {sync_url}")
            
            engine = create_engine(sync_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print(f"✅ Query result: {result.fetchone()}")
            print("🚀 Database connection successful!")
            return True
        except Exception as e:
            print(f"⏳ Waiting for database... (attempt {attempt + 1}/{max_retries})")
            print(f"❌ Error details: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                print(f"🛑 Database connection failed: {e}")
                return False


def run_alembic_command(command: str) -> bool:
    """Chạy lệnh Alembic"""
    try:
        print(f"⚙️ Running: alembic {command}")
        result = subprocess.run(
            ["alembic"] + command.split(),
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False


async def run_migrations():
    """Chạy database migrations"""
    print("🛠️ Running database migrations...")
    
    # Chờ database sẵn sàng
    if not await wait_for_database():
        print("🛑 Database not ready, skipping migrations...")
        return False
    
    # Chạy migrations
    if not run_alembic_command("upgrade head"):
        print("❌ Migration failed!")
        return False
    
    print("✅ Database migrations completed!")
    return True


def get_optimal_workers():
    """Calculate optimal number of workers based on CPU cores"""
    import multiprocessing
    
    cpu_count = multiprocessing.cpu_count()
    
    # For production: (CPU cores * 2) + 1
    # But cap at reasonable limits for memory usage
    optimal_workers = min((cpu_count * 2) + 1, 8)  # Max 8 workers for stability
    
    print(f"💻 Detected {cpu_count} CPU cores")
    print(f"🧵 Optimal workers: {optimal_workers}")

    # Default to 1 for stability in dev
    return 1


def start_backend():
    """Start backend server"""
    print("🚀 Starting backend...")
    
    environment = settings.environment
    log_level = settings.log_level
    is_development = environment in ["dev", "development"]
    
    if is_development:
        print("🛠️ Starting in development mode with hot reload...")
        # Use import string for reload to work properly
        subprocess.run([
            "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0", 
            "--port", "8386", 
            "--reload",
        ])
    else:
        print("🌐 Starting in production mode...")
        workers = get_optimal_workers()
        
        subprocess.run([
            "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0", 
            "--port", "8386", 
            "--workers", str(workers),  
            "--no-access-log",
            "--log-level", log_level
        ])


async def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 IRIS Hub Startup")
    print("=" * 60)
    
    # Bước 1: Chạy migrations
    await run_migrations()
    
    # Bước 2: Start backend
    start_backend()


if __name__ == "__main__":
    asyncio.run(main())
