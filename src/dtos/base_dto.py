# Copyright (C) 2026 Lucas Dias

"""Base data transfer object definition.

This module provides the common Pydantic configuration used by all DTOs in the
application. The base model enforces strict validation, immutability, and
schema consistency to ensure that data structures remain predictable and
type-safe throughout the system.
"""

import pydantic


class BaseDTO(pydantic.BaseModel):
    """Base class for all application data transfer objects.

    This model centralizes the default Pydantic configuration used across the
    codebase.
    """

    model_config = pydantic.ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
        strict=True,
    )
