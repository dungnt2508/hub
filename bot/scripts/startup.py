"""
Startup script for PNJ Hub
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.logger import logger
from backend.shared.config import config


async def check_dependencies():
    """Check if all required services are available"""
    import redis.asyncio as redis
    from sqlalchemy.ext.asyncio import create_async_engine
    import os
    
    checks = []
    
    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        checks.append(("Redis", True))
        logger.info("Redis connection: OK")
    except Exception as e:
        checks.append(("Redis", False))
        logger.error(f"Redis connection failed: {e}")
    
    # Check Database
    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            engine = create_async_engine(database_url)
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            await engine.dispose()
            checks.append(("Database", True))
            logger.info("Database connection: OK")
    except Exception as e:
        checks.append(("Database", False))
        logger.warning(f"Database connection failed: {e}")
    
    # Check Qdrant (optional)
    try:
        import httpx
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{qdrant_url}/health", timeout=5.0)
            if response.status_code == 200:
                checks.append(("Qdrant", True))
                logger.info("Qdrant connection: OK")
            else:
                checks.append(("Qdrant", False))
                logger.warning("Qdrant health check failed")
    except Exception as e:
        checks.append(("Qdrant", False))
        logger.warning(f"Qdrant connection failed: {e}")
    
    # Summary
    all_ok = all(status for _, status in checks)
    if not all_ok:
        logger.warning("Some services are not available. Check logs above.")
    
    return all_ok


def main():
    """Main startup function"""
    logger.info("Starting PNJ Hub - Global Router System")
    logger.info(f"Configuration: {config.to_dict()}")
    
    # Check dependencies
    asyncio.run(check_dependencies())
    
    # Start API server
    import uvicorn
    import os
    
    uvicorn.run(
        "backend.interface.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8386)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO").lower(),
    )


if __name__ == "__main__":
    main()

