# Copyright (C) 2026 Lucas Dias

"""Asset type database model.

This module defines the :class:`AssetTypeModel` entity, which represents a category
of assets within a portfolio.
"""

import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_model import AssetModel
    from src.database.models.portfolio_model import PortfolioModel
    from src.database.models.score_question_model import ScoreQuestionModel


class AssetTypeModel(Base, Model):
    """Represent an asset type stored in the database.

    Attributes:
        id (int):
            Unique identifier of the asset type.

        name (str):
            Human-readable name of the asset type.

        proportion (int):
            Target allocation proportion assigned to this asset type.

        is_question_scored (bool):
            Indicates whether the asset type allocation is determined
            through questionnaire scoring.

        portfolio_id (int):
            Foreign key referencing the associated portfolio.

        portfolio (PortfolioModel):
            Portfolio to which this asset type belongs.

        assets (list[AssetModel]):
            Assets associated with this asset type.

        score_questions (list[ScoreQuestionModel]):
            Score questions associated with this asset type.

    """

    __tablename__ = "asset_type"
    __plural__ = "asset_types"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String)
    proportion: Mapped[int] = mapped_column(sqlalchemy.Integer)
    is_question_scored: Mapped[bool] = mapped_column(sqlalchemy.Boolean, default=False)

    portfolio_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("portfolio.id"))

    # N-1
    portfolio: Mapped[PortfolioModel] = relationship("PortfolioModel", back_populates=__plural__)

    # 1-N
    assets: Mapped[list[AssetModel]] = relationship("AssetModel", back_populates=__tablename__, uselist=True)
    score_questions: Mapped[list[ScoreQuestionModel]] = relationship(
        "ScoreQuestionModel",
        back_populates=__tablename__,
        uselist=True,
    )
