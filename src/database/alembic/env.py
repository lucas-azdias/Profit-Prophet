# Copyright (C) 2026 Lucas Dias

"""Alembic migration environment configuration.

This module configures Alembic for use with the application's
SQLAlchemy models and database engine. It supports both offline and
online migration modes and exposes the application's metadata for
automatic schema generation.
"""

import asyncio

import alembic
import sqlalchemy
import sqlalchemy.ext.asyncio

# IGNORE: Import the entire database package (required on runtime even though it is not used)
from src.database import base, models  # type: ignore reportUnusedImport # noqa: F401

config = alembic.context.config

# Add models metadata
target_metadata = base.Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode.

    Offline migrations generate SQL statements without establishing a
    connection to the target database. Migration scripts are executed
    using only the configured database URL.

    """
    url = config.get_main_option("sqlalchemy.url")
    alembic.context.configure(
        url=url,
        target_metadata=base.Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode.

    Online migrations establish a database connection using the
    configured SQLAlchemy engine and execute migration operations
    directly against the target database.

    """

    def do_migrations(connection: sqlalchemy.Connection) -> None:
        alembic.context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()

    async def run_migrations() -> None:
        connectable = sqlalchemy.ext.asyncio.async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=sqlalchemy.pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_migrations)

        await connectable.dispose()

    asyncio.run(run_migrations())


if alembic.context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
