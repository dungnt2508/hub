from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Alembic Config
config = context.config

# Logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Import metadata ONLY
# Yêu cầu: project phải là package hợp lệ (có __init__.py)
from app.infrastructure.database.base import Base  # noqa
from app.infrastructure.database import models     # ĐÃ SỬA

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Priority:
    1. DATABASE_URL env
    2. sqlalchemy.url in alembic.ini
    """
    url = os.getenv("SYNC_URL")
    if url:
        return url

    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}

    url = get_database_url()

    section["sqlalchemy.url"] = url

    engine = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()



if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
