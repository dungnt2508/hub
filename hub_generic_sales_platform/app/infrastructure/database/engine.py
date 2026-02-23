"""
Database engine và session management
Sử dụng SQLAlchemy async
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from app.core.config.settings import get_settings
from app.core.shared.logger import get_logger

logger = get_logger(__name__, component="database")
settings = get_settings()

# Global engine và session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Lấy database engine (singleton)"""
    global _engine

    if _engine is None:
        settings = get_settings()

        logger.info(
            "Initialize database engine",
            database_url=settings.database_url.split("@")[-1]  # Hide credentials
        )

        # Sử dụng connection string gốc (timezone sẽ được set từ PostgreSQL config)
        db_url = settings.database_url

        # Với asyncpg, không set timezone trong connect_args vì không được hỗ trợ
        # Timezone sẽ được set từ PostgreSQL config (docker-compose hoặc database setting)
        _engine = create_async_engine(
            db_url,
            # echo=settings.database.echo_sql,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,  # Kiểm tra connection trước khi dùng
            pool_recycle=settings.db_pool_recycle,
            connect_args={
                "server_settings": {
                    "application_name": settings.app_name,
                    "statement_timeout": "300000",  # 5 phút timeout
                }
            } if "asyncpg" in db_url else {}
        )

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Lấy async session maker"""
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Initialize async session maker")

    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency để lấy database session

    Usage trong FastAPI:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            ...
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Khởi tạo database (chạy khi startup)"""
    logger.info("Initialize database connection")
    engine = get_engine()

    # Test connection và set timezone Asia/Ho_Chi_Minh (UTC+7)
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            # Set timezone Asia/Ho_Chi_Minh cho session này
            await conn.execute(text("SET timezone = 'Asia/Ho_Chi_Minh'"))
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful", timezone="Asia/Ho_Chi_Minh (UTC+7)")
    except Exception as e:
        logger.error("Database connection error", error=str(e), exc_info=True)
        raise


async def close_database():
    """Đóng database connection (chạy khi shutdown)"""
    global _engine, _async_session_maker

    if _engine:
        logger.info("Close database connection")
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
