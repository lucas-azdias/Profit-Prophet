# Copyright (C) 2026 Lucas Dias

"""Portfolio database model.

This module defines the `PortfolioModel`, which represents an investment
portfolio. A portfolio groups multiple asset types and serves as the
top-level structure for asset allocation definitions.
"""

import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_type_model import AssetTypeModel


class PortfolioModel(Base, Model):
    """Represent a portfolio stored in the database.

    Attributes:
        id (int):
            Unique identifier of the portfolio.

        name (str):
            Human-readable name of the portfolio.

        asset_types (list[AssetTypeModel]):
            Asset types associated with this portfolio.

    """

    __tablename__ = "portfolio"
    __plural__ = "portfolios"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String)

    # 1-N
    asset_types: Mapped[list[AssetTypeModel]] = relationship(
        "AssetTypeModel",
        back_populates=__tablename__,
        uselist=True,
    )
