# Copyright (C) 2026 Lucas Dias

"""Portfolio asset position module.

Provides the Position class, which represents a portfolio position and
exposes calculated metrics such as quantity, value, score, average price,
and current market price.
"""

import decimal
import typing

if typing.TYPE_CHECKING:
    from src.database.models import AssetModel
    from src.finance.position_strategy import PositionStrategy


class Position:
    """Portfolio asset position class.

    Represents a portfolio position and provides access to asset data and
    derived financial metrics computed through a position strategy.
    """

    __slots__ = ("__current_price", "__model", "__strategy")

    def __init__(
        self,
        model: AssetModel,
        strategy: PositionStrategy,
        current_price: decimal.Decimal | None,
    ) -> None:
        """Initialize the position.

        Args:
            model (AssetModel):
                Database model containing the asset data and transaction
                history associated with the position.

            strategy (PositionStrategy):
                Strategy used to calculate position-specific metrics
                such as quantity and value.

            current_price (Decimal | None):
                Current market price of the asset, if available.

        """
        self.__model = model
        self.__strategy = strategy
        self.__current_price = current_price

    @property
    def id(self) -> int:
        """Returns the position's asset identifier.

        Returns:
            int:
                Position's asset identifier.

        """
        return self.__model.id

    @property
    def name(self) -> str:
        """Returns the position's asset name.

        Returns:
            str:
                Position's asset name.

        """
        return self.__model.name

    @property
    def type(self) -> str:
        """Returns the position's asset type.

        Returns:
            str:
                Position's asset type.

        """
        return self.__model.asset_type.name

    @property
    def score(self) -> int:
        """Returns the position's asset score.

        The score may be derived from questionnaire answers or from a
        user-defined score stored in the asset model.

        Returns:
            int:
                Position's asset score.

        """
        # Calculates the score from questionnaire answers if asset type allows
        if self.__model.asset_type.is_question_scored:
            # (True counts - False counts)
            return sum(1 if answer.answer else -1 for answer in self.__model.score_answers)

        # Gets the score defined by the user if available
        if self.__model.user_score is not None:
            return self.__model.user_score

        return 0

    @property
    def current_price(self) -> decimal.Decimal | None:
        """Returns the current market price of the asset, if available.

        Returns:
            Decimal | None:
                Position's asset current price.

        """
        return self.__current_price

    @property
    def average_price(self) -> decimal.Decimal | None:
        """Calculates the average acquisition price.

        It is calculated based on its asset transaction history.

        Returns:
            Decimal | None:
                Position's average acquisition price.

        """
        # Aggregates the total amount invested across all transactions
        total_cost = sum(
            (t.price * t.quantity for t in self.__model.transactions),
            start=decimal.Decimal("0.0"),
        )

        # Aggregates the total quantity acquired across all transactions
        total_quantity = sum(t.quantity for t in self.__model.transactions)

        # Unitary assets always have an effective quantity of one
        if self.__model.asset_type.is_unitary_asset:
            total_quantity = 1

        # Deals with division by zero cases
        if total_quantity == 0:
            return None

        return total_cost / total_quantity

    @property
    def quantity(self) -> int:
        """Returns the quantity represented by the position.

        For unitary assets, the quantity is always one. Otherwise, the value
        is delegated to the configured position strategy.

        Returns:
            int:
                Position current quantity.

        """
        if self.__model.asset_type.is_unitary_asset:
            return 1
        return self.__strategy.quantity(self)

    @property
    def value(self) -> decimal.Decimal:
        """Returns the current value of the position.

        It is calculated by the configured strategy.

        Returns:
            Decimal:
                Position current total value.

        """
        return self.__strategy.value(self)

    def model(self) -> AssetModel:
        """Return the underlying asset model.

        Returns:
            AssetModel:
                Position's asset model.

        """
        return self.__model

    @staticmethod
    def columns() -> list[str]:
        """Return the names of the exposed position properties.

        This method is typically used when dynamically generating tabular
        representations of position data.

        Returns:
            list[str]:
                Exposed position properties as column names for a data table.

        """
        # Gets all columns in position based on property methods
        return [
            name
            for name in Position.__dict__
            if isinstance(getattr(Position, name, None), property)
        ]
