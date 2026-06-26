# Copyright (C) 2026 Lucas Dias

"""Score questions database model.

This module defines the `ScoreQuestionModel`, which represents a question
used to evaluate investor preferences, risk tolerance, or suitability.
"""

import typing

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.database.model import Model

if typing.TYPE_CHECKING:
    from src.database.models.asset_type_model import AssetTypeModel
    from src.database.models.score_answer_model import ScoreAnswerModel


class ScoreQuestionModel(Base, Model):
    """Represent a score question stored in the database.

    Attributes:
        id (int):
            Unique identifier of the score question.

        text (str):
            Text content of the question.

        asset_type_id (int):
            Foreign key referencing the associated asset type.

        asset_type (AssetTypeModel):
            Asset type associated with this score question.

        score_answers (list[ScoreAnswerModel]):
            Answers associated with this score question.

    """

    __tablename__ = "score_question"
    __plural__ = "score_questions"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(sqlalchemy.Text)

    asset_type_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("asset_type.id"))

    # N-1
    asset_type: Mapped[AssetTypeModel] = relationship("AssetTypeModel", back_populates=__plural__)

    # 1-N
    score_answers: Mapped[list[ScoreAnswerModel]] = relationship(
        "ScoreAnswerModel",
        back_populates=__tablename__,
        uselist=True,
    )
