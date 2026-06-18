# Copyright (C) 2026 Lucas Dias

"""Application entry point.

This module initializes the application's core services.
It serves as the executable entry point for launching the
application.
"""

import asyncio

from src.config.config_loader import ConfigLoader
from src.database.database import Database
from src.inout.logger import Logger
from src.inout.user_interface import UserInterface


async def main() -> None:
    """Run the application startup sequence."""
    # Loads user configurations
    config = ConfigLoader().get_config()

    # Creates logger
    logger = Logger(config.logs_folder)

    # Starts database connection
    database = Database(config.database_url, config.max_database_conn_retries, logger)
    await database.start()

    # Starts user interface
    await UserInterface(database, logger).run_async()


if __name__ == "__main__":
    asyncio.run(main())
