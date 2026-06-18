# Copyright (C) 2026 Lucas Dias

"""Database model package.

This package provides all SQLAlchemy ORM models used by the application.
The models define the database schema and relationships for portfolios,
asset types, assets, transactions, score questions, and score answers.

Exports:
    AssetModel:
        Represents an asset owned within an asset type.

    AssetTypeModel:
        Represents a category of assets within a portfolio.

    PortfolioModel:
        Represents an investment portfolio containing asset types.

    ScoreAnswerModel:
        Represents an answer provided for a score question.

    ScoreQuestionModel:
        Represents a question used for investor profiling or suitability
        assessment.

    TransactionModel:
        Represents a transaction associated with an asset.
"""

from src.database.models.asset_model import AssetModel
from src.database.models.asset_type_model import AssetTypeModel
from src.database.models.portfolio_model import PortfolioModel
from src.database.models.score_answer_model import ScoreAnswerModel
from src.database.models.score_question_model import ScoreQuestionModel
from src.database.models.transaction_model import TransactionModel

__all__ = [
    "AssetModel",
    "AssetTypeModel",
    "PortfolioModel",
    "ScoreAnswerModel",
    "ScoreQuestionModel",
    "TransactionModel",
]
