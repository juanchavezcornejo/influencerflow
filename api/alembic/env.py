"""Alembic migration environment.

Uses the app settings for the DB URL and the ORM ``Base.metadata`` for
autogeneration. Runs migrations synchronously against a sync-converted URL so
Alembic's default tooling keeps working.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import settings
from app.db import Base

# Import models here so Alembic can autogenerate their tables.
# e.g. from app.models import user, asset
_ = Base  # keep the metadata import alive for autogeneration

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_db_url(url: str) -> str:
    """Alembic uses sync drivers. Strip +asyncpg / +aiosqlite if present."""
    return (
        url.replace("+asyncpg", "")
        .replace("postgresql+psycopg", "postgresql")
        .replace("+aiosqlite", "")
    )


config.set_main_option("sqlalchemy.url", _sync_db_url(settings.database_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running against a DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
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
