# Copyright (C) 2026 Lucas Dias

"""Configuration model.

This module defines a immutable configuration structure.
"""

import typing

from src.dtos.base_dto import BaseDTO

if typing.TYPE_CHECKING:
    import pathlib

    import sqlalchemy.engine


class ConfigDTO(BaseDTO):
    """Immutable configuration object describing crawler runtime settings.

    Attributes:
        database_url (sqlalchemy.engine.URL):
            Connection string used to access the application's database.

        logs_folder (pathlib.Path):
            Filesystem path where runtime logs are written.

        max_database_conn_retries (int):
            Maximum number of retry attempts when establishing a database
            connection before failing.

    """

    database_url: sqlalchemy.engine.URL
    logs_folder: pathlib.Path
    max_database_conn_retries: int

    # Enable arbitrary types to prevent Pydantic from attempting schema
    # generation for non-serializable runtime objects
    # (e.g. `sqlalchemy.engine.URL`)
    model_config = BaseDTO.model_config.copy()
    model_config["arbitrary_types_allowed"] = True
