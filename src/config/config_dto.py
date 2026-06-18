# Copyright (C) 2026 Lucas Dias

"""Configuration model.

This module defines a immutable configuration structure.
"""

import dataclasses
import typing

if typing.TYPE_CHECKING:
    import pathlib

    import sqlalchemy.engine


@dataclasses.dataclass(frozen=True)
class ConfigDTO:
    """Immutable configuration object describing crawler runtime settings.

    Attributes:
        database_url:
            Connection string used to access the application's database.

        logs_folder:
            Filesystem path where runtime logs are written.

        max_database_conn_retries:
            Maximum number of retry attempts when establishing a database
            connection before failing.

    """

    database_url: sqlalchemy.engine.URL
    logs_folder: pathlib.Path
    max_database_conn_retries: int
