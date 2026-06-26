# Copyright (C) 2026 Lucas Dias

"""Base model contract for all database entities.

This module defines `Model`, a common base class used to enforce required
metadata attributes across all SQLAlchemy models in the application.

Every subclass must define both `__tablename__` and `__plural__`. These
attributes are validated during class creation through `__init_subclass__`
to ensure a consistent interface for database and user-interface operations.
"""

import typing

if typing.TYPE_CHECKING:
    import sqlalchemy


class Model:
    """Base class that defines required model metadata.

    All database models must inherit from this class and provide the
    `__tablename__` and `__plural__` class attributes. These values
    are used throughout the application for database operations and
    user-interface generation.

    Attributes:
        __tablename__ (str):
            Name of the database table associated with the model.

        __plural__ (str):
            Human-readable plural name of the model.

        __table__ (sqlalchemy.Table):
            SQLAlchemy table metadata associated with the model.

    """

    __tablename__: str
    __plural__: str
    __table__: sqlalchemy.Table

    # IGNORE: As it is a generic class, `Any` was used to ignore all parameters
    def __init_subclass__(cls, **kwargs: typing.Any) -> None:  # noqa: ANN401
        """Validate model metadata during subclass creation.

        Ensures that every subclass explicitly defines both
        `__tablename__` and `__plural__`.

        Args:
            **kwargs (typing.Any):
                Additional keyword arguments passed to the parent
                implementation.

        Raises:
            TypeError:
                If the subclass does not define `__tablename__`.

            TypeError:
                If the subclass does not define `__plural__`.

        """
        super().__init_subclass__(**kwargs)

        if "__tablename__" not in cls.__dict__:
            msg = f"{cls.__name__} must define __tablename__"
            raise TypeError(msg)

        if "__plural__" not in cls.__dict__:
            msg = f"{cls.__name__} must define __plural__"
            raise TypeError(msg)
