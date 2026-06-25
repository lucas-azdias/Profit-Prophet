# Copyright (C) 2026 Lucas Dias

"""Portfolio asset allocation proposal module.

Provides the :class:`Allocation` class, which distributes an investment
amount across portfolio positions according to asset type proportions
and position scores.
"""

import collections
import decimal

from src.finance.position import Position
from src.finance.position_strategy import ValueStrategy


class Allocation:
    """Portfolio asset allocation proposal class.

    Represents an allocation proposal generated from a portfolio's
    positions, target asset type proportions, and available budget.
    """

    def __init__(
        self,
        positions: list[Position],
        types_proportions: dict[str, decimal.Decimal],
        value: decimal.Decimal,
    ) -> None:
        """Initialize the allocation.

        Args:
            positions (list[Position]):
                Positions eligible to receive allocations.

            types_proportions (dict[str, decimal.Decimal]):
                Target proportion for each asset type.

            value (Decimal):
                Total amount available for allocation.

        """
        self.__positions: list[Position] = []

        # Groups positions by type
        positions_by_type: dict[str, list[Position]] = collections.defaultdict(list)
        for position in positions:
            positions_by_type[position.type].append(position)

        # Determines which groups are valid (have a total score > 0)
        valid_groups: dict[str, int] = {}
        for asset_type, asset_positions in positions_by_type.items():
            total_score = sum(max(position.score, 0) for position in asset_positions)
            if total_score > 0:
                valid_groups[asset_type] = total_score

        # Sum proportions only for the groups that can actually receive an allocation
        total_valid_proportions = sum(
            types_proportions.get(asset_type, decimal.Decimal("0.0")) for asset_type in valid_groups
        )

        # Guards against division by zero
        if total_valid_proportions <= 0:
            return

        # Allocates the budget among the valid groups
        for asset_type, total_score in valid_groups.items():
            asset_positions = positions_by_type[asset_type]

            type_proportion = types_proportions.get(asset_type, decimal.Decimal("0.0"))
            type_budget = (value * type_proportion) / total_valid_proportions

            for position in asset_positions:
                score = max(position.score, decimal.Decimal("0.0"))
                position_allocation = type_budget * score / total_score

                self.__positions.append(
                    Position(
                        position.model(),
                        ValueStrategy(position_allocation),
                        position.current_price,
                    ),
                )

    @property
    def positions(self) -> list[Position]:
        """Return the generated allocation positions.

        Returns:
            list[Position]:
                The generated allocation positions.

        """
        return self.__positions[:]
