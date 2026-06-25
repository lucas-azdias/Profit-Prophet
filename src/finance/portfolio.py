# Copyright (C) 2026 Lucas Dias

"""Portfolio management module.

Provides the Portfolio class, which encapsulates portfolio data and
coordinates position construction, market price retrieval, and allocation
generation.
"""

import typing

from src.finance.allocation import Allocation
from src.finance.position import Position
from src.finance.position_strategy import QuantityStrategy

if typing.TYPE_CHECKING:
    import decimal

    from src.database.models import PortfolioModel
    from src.finance.price_provider import PriceProvider


class Portfolio:
    """Portfolio management class.

    Represents an investment portfolio and exposes operations for building
    positions and generating allocations based on the portfolio's target
    asset distribution.
    """

    def __init__(self, model: PortfolioModel, price_provider: PriceProvider) -> None:
        """Initialize the portfolio.

        Args:
            model (PortfolioModel):
                Database model containing the portfolio configuration,
                asset types, and associated assets.

            price_provider (PriceProvider):
                Service used to retrieve market prices for
                portfolio assets.

        """
        self.__model = model
        self.__price_provider = price_provider
        self.__positions: list[Position] | None = None

    @property
    def id(self) -> int:
        """Returns the portfolio identifier.

        Returns:
            int:
                Portfolio identifier.

        """
        return self.__model.id

    @property
    def name(self) -> str:
        """Returns the portfolio name.

        Returns:
            str:
                Portfolio name.

        """
        return self.__model.name

    async def build_positions(self) -> None:
        """Build the portfolio positions from the underlying assets.

        Market prices are retrieved for assets that use ticker-based pricing,
        while assets that do not require external pricing are created without
        a market value.
        """
        # Creates a position for every asset belonging to the portfolio
        self.__positions = [
            Position(
                asset,
                QuantityStrategy(),
                await self.__price_provider.get_price(asset.name)
                if await self.__price_provider.is_valid_ticker(asset.name)
                and not asset.asset_type.is_unitary_asset
                else None,
            )
            for asset_type in self.__model.asset_types
            for asset in asset_type.assets
        ]

    def new_allocation(self, value: decimal.Decimal) -> Allocation:
        """Create a new allocation proposal using the current positions and asset type proportions.

        Args:
            value (Decimal):
                Amount available for allocation.

        Returns:
            Allocation:
                An allocation instance based on the portfolio strategy.

        Raises:
            RuntimeError:
                If positions have not been built yet.

        """
        if self.__positions is None:
            msg = f"'{self.__class__.__name__}' positions have not been built yet."
            raise RuntimeError(msg)

        # Generates an allocation using the current positions and the target
        # proportions configured for each asset type
        return Allocation(
            self.__positions,
            {asset_type.name: asset_type.proportion for asset_type in self.__model.asset_types},
            value,
        )
