# Copyright (C) 2026 Lucas Dias

"""Asset database model.

This module defines :class:`AssetModel`, which represents an asset owned
or tracked by the application.
"""

import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_type_model import AssetTypeModel
    from src.database.models.score_answer_model import ScoreAnswerModel
    from src.database.models.transaction_model import TransactionModel


class AssetModel(Base, Model):
    """Represent an asset stored in the database.

    Attributes:
        id (int):
            Unique identifier of the asset.

        name (str):
            Human-readable name of the asset.

        user_score (int | None):
            Optional score assigned by the user.

        asset_type_id (int):
            Foreign key referencing the associated asset type.

        asset_type (AssetTypeModel):
            Asset type to which this asset belongs.

        transactions (list[TransactionModel]):
            Transactions associated with this asset.

        score_answers (list[ScoreAnswerModel]):
            Score answers associated with this asset.

    """

    __tablename__ = "asset"
    __plural__ = "assets"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String)
    user_score: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=True, default=None)

    asset_type_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("asset_type.id"))

    # N-1
    asset_type: Mapped[AssetTypeModel] = relationship("AssetTypeModel", back_populates=__plural__)

    # 1-N
    transactions: Mapped[list[TransactionModel]] = relationship(
        "TransactionModel",
        back_populates=__tablename__,
        uselist=True,
    )
    score_answers: Mapped[list[ScoreAnswerModel]] = relationship(
        "ScoreAnswerModel",
        back_populates=__tablename__,
        uselist=True,
    )
