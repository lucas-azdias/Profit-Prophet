# Copyright (C) 2026 Lucas Dias

"""Transactions database model.

This module defines the `TransactionModel`, which represents a transaction
performed for an asset.
"""

# IGNORE: Required at runtime because SQLAlchemy resolves Mapped annotations
import datetime  # noqa: TC003
import decimal  # noqa: TC003
import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_model import AssetModel


class TransactionModel(Base, Model):
    """Represent a transaction stored in the database.

    Attributes:
        id (int):
            Unique identifier of the transaction.

        price (float):
            Unit price of the asset in the transaction.

        quantity (int):
            Quantity of asset units involved in the transaction.

        done_at (datetime.datetime):
            Date and time when the transaction was executed.

        asset_id (int):
            Foreign key referencing the associated asset.

        asset (AssetModel):
            Asset associated with this transaction.

    """

    __tablename__ = "transaction"
    __plural__ = "transactions"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    price: Mapped[decimal.Decimal] = mapped_column(sqlalchemy.Numeric(20, 8))
    quantity: Mapped[int] = mapped_column(sqlalchemy.Integer)
    done_at: Mapped[datetime.datetime] = mapped_column(sqlalchemy.DateTime(timezone=True))

    asset_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("asset.id"))

    # N-1
    asset: Mapped[AssetModel] = relationship("AssetModel", back_populates=__plural__)
