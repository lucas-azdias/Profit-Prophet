# Copyright (C) 2026 Lucas Dias

"""Command-line configuration loading and parsing.

This module provides the `ConfigLoader` class, responsible for defining, parsing,
and validating command-line arguments.

The loader converts user-supplied CLI options into a `ConfigDTO` instance that
encapsulates settings.

It serves as the primary entry point for transforming command-line input into
application configuration consumed by other components.
"""

import argparse
import pathlib

import sqlalchemy.engine

from src.config.config_dto import ConfigDTO


class ConfigLoader:
    """Command-line configuration loader.

    This class is responsible for defining CLI arguments, parsing user input,
    and producing a validated immutable `ConfigDTO` object used throughout the
    application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the command-line interface configuration.

        Creates the argument parser, processes command-line arguments supplied by
        the user, and constructs a `ConfigDTO` instance containing the validated
        runtime configuration.
        """
        # Argument parser for all parameters available for user via CLI
        self.__parser = argparse.ArgumentParser(
            prog="Profit Prophet",
            description=(
                "Manage and optimize your investments across multiple asset classes in one place. "
                "Track your current allocations, compare them to your target portfolio, and get "
                "clear recommendations on where to invest new funds as your wealth grows."
            ),
        )

        self.__parser.add_argument(
            "--database-url",
            type=sqlalchemy.engine.make_url,
            dest="database_url",
            default="sqlite+aiosqlite:///portfolio.db",
            help="Connection URL to access application's database.",
        )

        self.__parser.add_argument(
            "--logs",
            type=pathlib.Path,
            dest="logs_folder",
            default="./logs",
            help="Folder where crawler execution logs are written.",
        )

        self.__parser.add_argument(
            "--max-database-retries",
            type=int,
            dest="max_database_conn_retries",
            default=5,
            help="Maximum number of retry attempts for establishing a database connection.",
        )

        # Rebuilds the config model to solve imports (aka. `ForwardRef`)
        ConfigDTO.model_rebuild(_types_namespace=globals())

        # All user configurations saved
        self.__config = ConfigDTO(**vars(self.__parser.parse_args()))

    def get_config(self) -> ConfigDTO:
        """Return the parsed crawler configuration.

        Returns:
            ConfigDTO:
                Immutable configuration object containing all CLI-provided
                and default crawler settings.

        """
        return self.__config
