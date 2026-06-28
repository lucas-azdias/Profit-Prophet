# Copyright (C) 2026 Lucas Dias

"""Portfolio asset allocation proposal module.

Provides the `Allocation` class, which distributes an investment amount
across portfolio positions according to asset type proportions and position
scores, taking existing values into account.
"""

import collections
import decimal
import typing

from src.finance.position import Position
from src.finance.position_strategy import ValueStrategy


class Allocation:
    """Portfolio asset allocation proposal class.

    Represents an allocation proposal generated from a portfolio's
    positions, target asset type proportions, and available budget,
    while considering already allocated values.
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

        Raises:
            ValueError:
                If negative or null values are given.

        """
        self.__positions: list[Position] = []

        if value <= 0:
            msg = "Cannot allocate negative or null values"
            raise ValueError(msg)

        # Groups positions by type and calculates total values for each type
        positions_by_type: dict[str, list[Position]] = collections.defaultdict(list)
        values_by_type: dict[str, decimal.Decimal] = collections.defaultdict(decimal.Decimal)
        for position in positions:
            positions_by_type[position.type].append(position)
            values_by_type[position.type] += position.value

        # Determines which groups are valid (have a total score > 0)
        valid_groups: dict[str, int] = {}
        for asset_type, asset_positions in positions_by_type.items():
            total_score = sum(max(position.score, 0) for position in asset_positions)
            if total_score > 0:
                valid_groups[asset_type] = total_score

        # Calculates how much new budget each asset type needs
        types_budgets = self.__calculate_types_budgets(
            valid_groups.keys(),
            types_proportions,
            values_by_type,
            value,
        )

        # If no budget for any type, return empty allocation
        if not types_budgets:
            return

        # Allocates positions
        self.__positions = self.__allocate_positions(positions_by_type, valid_groups, types_budgets)

    @property
    def positions(self) -> list[Position]:
        """Return the generated allocation positions.

        Returns:
            list[Position]:
                The generated allocation positions.

        """
        return self.__positions[:]

    @staticmethod
    def __calculate_types_budgets(
        valid_groups: typing.Iterable[str],
        types_proportions: dict[str, decimal.Decimal],
        values_by_type: dict[str, decimal.Decimal],
        value: decimal.Decimal,
    ) -> dict[str, decimal.Decimal]:
        # Sum proportions only for the groups that can actually receive an allocation
        total_valid_proportions = sum(
            types_proportions.get(asset_type, decimal.Decimal("0.0")) for asset_type in valid_groups
        )

        # Guards against division by zero (returns empty allocation)
        if total_valid_proportions <= 0:
            return {}

        # Calculates current and target total value for the entire portfolio
        total_current_portfolio_value = sum(values_by_type.values())
        target_portfolio_value = total_current_portfolio_value + value

        # Calculates how much new budget each asset type needs
        types_budgets: dict[str, decimal.Decimal] = {}
        total_allocated_budget = decimal.Decimal("0.0")
        for asset_type in valid_groups:
            type_proportion = (
                types_proportions.get(asset_type, decimal.Decimal("0.0")) / total_valid_proportions
            )
            target_type_value = target_portfolio_value * type_proportion

            # Budget needed is target calue minus what we already hold
            needed_budget = target_type_value - values_by_type[asset_type]

            # Prevents selling positions if an asset type is overweight (floor at 0)
            types_budgets[asset_type] = max(needed_budget, decimal.Decimal("0.0"))

            # Adds to total allocated budget
            total_allocated_budget += types_budgets[asset_type]

        # If all allocations exceed their proportions, make an empty allocation
        if total_allocated_budget <= 0:
            return {}

        # Normalizes allocated value considering not allocated values
        budget_multiplier = value / total_allocated_budget
        for asset_type in types_budgets:
            types_budgets[asset_type] *= budget_multiplier

        return types_budgets

    @staticmethod
    def __allocate_positions(
        positions_by_type: dict[str, list[Position]],
        valid_groups: dict[str, int],
        types_budgets: dict[str, decimal.Decimal],
    ) -> list[Position]:
        # Final allocated positions
        positions: list[Position] = []

        # Allocates the type-level budget down to individual positions
        for asset_type, total_score in valid_groups.items():
            # All positions with this type
            asset_positions = positions_by_type[asset_type]

            # Available budget for this type
            type_budget = types_budgets.get(asset_type, decimal.Decimal("0.0"))

            # Calculates total current value of positions with a valid score in this group
            valid_type_value = sum(
                position.value for position in asset_positions if position.score > 0
            )
            target_type_value = valid_type_value + type_budget

            # Allocates for each position
            for position in asset_positions:
                # If score is negative or null, then don't allocate
                if position.score <= 0:
                    position_allocation = decimal.Decimal("0.0")
                else:
                    # Target value for this specific position based on its score weight
                    position_score_weight = decimal.Decimal(position.score) / total_score
                    target_position_value = target_type_value * position_score_weight

                    # Allocates if needed budget is positive (prevents selling)
                    position_allocation = max(
                        target_position_value - position.value,
                        decimal.Decimal("0.0"),
                    )

                positions.append(
                    Position(
                        position.model(),
                        ValueStrategy(position_allocation),
                        position.current_price,
                    ),
                )

        return positions
