# Copyright (C) 2026 Lucas Dias

"""Portfolio position strategy module.

Defines position calculation strategies used to determine the quantity
and value of portfolio positions.
"""

import decimal
import typing

if typing.TYPE_CHECKING:
    from src.finance.position import Position


class PositionStrategy(typing.Protocol):
    """Portfolio position strategy class.

    Defines the contract for position calculation strategies.
    """

    def quantity(self, position: Position) -> int:
        """Calculate the quantity represented by a position.

        Args:
            position (Position):
                The current asset position.

        Returns:
            int:
                Position current quantity calculated by the strategy.

        """
        raise NotImplementedError

    def value(self, position: Position) -> decimal.Decimal:
        """Calculate the value represented by a position.

        Args:
            position (Position):
                The current asset position.

        Returns:
            Decimal:
                Position current total value calculated by the strategy.

        """
        raise NotImplementedError


class QuantityStrategy:
    """Calculates position metrics using the asset quantity held."""

    # IGNORE: It is not possible to change the function definition
    # as it generates an error with the `Protocol`
    def quantity(self, position: Position) -> int:  # noqa: PLR6301
        """Return the total quantity held in the position.

        Args:
            position (Position):
                Position for which the quantity will be calculated.

        Returns:
            int:
                The number of units acquired based on past transactions.

        """
        return sum(transaction.quantity for transaction in position.model().transactions)

    def value(self, position: Position) -> decimal.Decimal:
        """Calculate the current position value based on the held quantity and current market price.

        Args:
            position (Position):
                Position for which the value will be calculated.

        Returns:
            Decimal:
                The current position value or 0.0 when no market price is
                available.

        """
        if position.current_price is None:
            return decimal.Decimal("0.0")
        return self.quantity(position) * position.current_price


class ValueStrategy:
    """Calculate position metrics from a target monetary value."""

    def __init__(self, value: decimal.Decimal) -> None:
        """Initialize the strategy.

        Args:
            value (Decimal):
                Target monetary value represented by the position.

        """
        self.__value = value

    def quantity(self, position: Position) -> int:
        """Calculate how many units can be acquired using the configured target value.

        Args:
            position (Decimal):
                Position used to determine the asset price.

        Returns:
            int:
                The number of units that can be acquired or 0 when no market
                price is available.

        """
        if position.current_price is None:
            return 0
        return int(self.__value // position.current_price)

    # IGNORE: It is not possible to use underline notation to indicate
    # unused parameter as it generates an error with the `Protocol`
    def value(self, position: Position) -> decimal.Decimal:  # noqa: ARG002
        """Return the configured target value.

        Args:
            position (Position):
                Position associated with the calculation. The
                parameter is unused but required by the strategy protocol.

        Returns:
            Decimal:
                The target monetary value.

        """
        return self.__value
