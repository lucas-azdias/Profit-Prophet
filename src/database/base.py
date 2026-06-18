# Copyright (C) 2026 Lucas Dias

"""SQLAlchemy declarative base definition.

This module defines the application's root declarative base class used
by all ORM models. The base provides a shared metadata registry that
enables model discovery, relationship mapping, schema generation, and
database migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All database models should inherit from this class to participate in
    SQLAlchemy's declarative mapping system and share a common metadata
    registry.
    """
