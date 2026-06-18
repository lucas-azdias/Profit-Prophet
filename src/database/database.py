# Copyright (C) 2026 Lucas Dias

"""Database connection and session management.

This module defines :class:`Database`, which is responsible for
initializing the SQLAlchemy engine, managing database sessions,
verifying connectivity, and applying pending schema migrations during
application startup.
"""

import asyncio
import typing

import alembic.command
import alembic.config
import sqlalchemy
import sqlalchemy.engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.database.base import Base

if typing.TYPE_CHECKING:
    from src.inout.logger import Logger


class Database:
    """Manage database connectivity and sessions.

    This class encapsulates the application's SQLAlchemy engine and
    session factory. It provides methods for establishing database
    connections, creating sessions, disposing resources, and applying
    Alembic migrations.
    """

    def __init__(self, url: sqlalchemy.engine.URL, max_conn_retries: int, logger: Logger) -> None:
        """Initialize the database manager.

        Args:
            url (sqlalchemy.engine.URL):
                Database connection URL.

            max_conn_retries (int):
                Maximum number of connection attempts before startup fails.

            logger (Logger):
                Logger used to record database events and errors.

        """
        self.__url = url
        self.__max_conn_retries = max_conn_retries
        self.__logger = logger
        self.__engine: AsyncEngine | None = None
        self.__session_factory: async_sessionmaker[AsyncSession] | None = None

    async def start(self) -> None:
        """Initialize the database connection.

        This method creates the SQLAlchemy engine and session factory,
        verifies database connectivity, and applies any pending schema
        migrations.

        Raises:
            ValueError:
                If the application's SQLAlchemy base metadata is not defined.

            SystemExit:
                If the database cannot be initialized or connected after the
                configured number of retries.

        """
        # Creates a async connection engine
        self.__engine = create_async_engine(
            self.__url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

        # Checks `Base` class
        if not Base.metadata:
            msg = "Database base class for models not defined"
            raise ValueError(msg)

        # Creates session factory
        self.__session_factory = async_sessionmaker(
            bind=self.__engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        # Retry connection loop
        for attempt in range(self.__max_conn_retries + 1):
            try:
                # Tests connection immediately
                async with self.__engine.connect() as conn:
                    await conn.execute(sqlalchemy.text("SELECT 1"))

            except SQLAlchemyError as e:
                self.__logger.log(f"Database initialization error: {e}", msg_type="error")
                raise SystemExit(1) from None

            except Exception as e:  # noqa: BLE001
                self.__logger.log(
                    f"Database connection failed (attempt {attempt + 1}/{self.__max_conn_retries}): {e}",
                    msg_type="error",
                )

                if attempt < self.__max_conn_retries:
                    retry_backoff = 5
                    self.__logger.log(f"Retrying in {retry_backoff:.2f} seconds...")
                    await asyncio.sleep(retry_backoff)
                else:
                    self.__logger.log(
                        f"Could not initialize database connection after multiple attempts: {e}",
                        msg_type="error",
                    )
                    raise SystemExit(1) from None

            else:
                self.__logger.log("Database engine initialized successfully")

                # Applies models schema to database
                await self.__upgrade_schema()

                # If succeeds, break from retry loop
                break

    async def close(self) -> None:
        """Dispose database resources.

        The database engine is shut down and all associated resources are
        released. Any existing session factory is also discarded.

        Raises:
            RuntimeError:
                If the database connection has not been initialized.

        """
        if self.__engine is None:
            msg = "Database connection has not been initialized."
            raise RuntimeError(msg)

        await self.__engine.dispose()

        self.__engine = None
        self.__session_factory = None

        self.__logger.log("Database engine disposed successfully.")

    def get_session(self) -> AsyncSession:
        """Create a new database session.

        Returns:
            AsyncSession:
                A new asynchronous SQLAlchemy session.

        Raises:
                RuntimeError:
                    If the database connection has not been initialized.

        """
        if self.__session_factory is None:
            msg = "Database connection has not been initialized."
            raise RuntimeError(msg)

        return self.__session_factory()

    async def __upgrade_schema(self) -> None:
        if self.__engine is None:
            msg = "Database connection has not been initialized."
            raise RuntimeError(msg)

        cfg = alembic.config.Config("./alembic.ini")
        cfg.set_main_option("sqlalchemy.url", str(self.__url))

        await asyncio.to_thread(
            alembic.command.upgrade,
            cfg,
            "head",
        )
