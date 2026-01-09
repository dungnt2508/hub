"""
Pytest configuration for integration tests
"""
import sys
from pathlib import Path
import pytest
import asyncio

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function", autouse=False)
async def redis_connection():
    """Setup Redis connection for tests that need it"""
    from backend.infrastructure.redis_client import redis_client
    
    try:
        await redis_client.connect()
        yield redis_client
        await redis_client.disconnect()
    except Exception as e:
        print(f"[WARNING] Redis not available: {e}")
        yield None


@pytest.fixture(scope="function", autouse=False)
async def db_connection():
    """Setup database connection for tests that need it"""
    from backend.infrastructure.database_client import DatabaseClient
    
    try:
        db_client = DatabaseClient()
        await db_client.connect()
        yield db_client
        await db_client.disconnect()
    except Exception as e:
        print(f"[WARNING] Database not available: {e}")
        yield None
