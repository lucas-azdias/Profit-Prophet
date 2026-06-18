# Copyright (C) 2026 Lucas Dias

"""Score answers database model.

This module defines the :class:`ScoreAnswerModel`, which represents an answer
provided for a score question.
"""

import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_model import AssetModel
    from src.database.models.score_question_model import ScoreQuestionModel


class ScoreAnswerModel(Base, Model):
    """Represent a score answer stored in the database.

    Attributes:
        id (int):
            Unique identifier of the score answer.

        answer (bool):
            Boolean answer provided for the score question.

        score_question_id (int):
            Foreign key referencing the associated score question.

        asset_id (int):
            Foreign key referencing the associated asset.

        asset (AssetModel):
            Asset associated with this score answer.

        score_question (ScoreQuestionModel):
            Score question associated with this answer.

    """

    __tablename__ = "score_answer"
    __plural__ = "score_answers"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    answer: Mapped[bool] = mapped_column(sqlalchemy.Boolean)

    score_question_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("score_question.id"))
    asset_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("asset.id"))

    # N-1
    asset: Mapped[AssetModel] = relationship("AssetModel", back_populates=__plural__)
    score_question: Mapped[ScoreQuestionModel] = relationship("ScoreQuestionModel", back_populates=__plural__)
