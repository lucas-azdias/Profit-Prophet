# Copyright (C) 2026 Lucas Dias

"""Finance price provider module.

Defines interfaces and implementations responsible for retrieving
market prices and validating asset tickers.
"""

import typing

from src.scrapers.google_finance.scraper import Scraper

if typing.TYPE_CHECKING:
    import decimal

    import playwright.async_api

    from src.inout.logger import Logger


class PriceProvider(typing.Protocol):
    """Finance price provider class.

    Defines the contract for services that provide market prices and
    ticker validation.
    """

    async def get_price(self, ticker: str) -> decimal.Decimal | None:
        """Retrieve the current market price for a ticker.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            Decimal | None
                The current market price if available.

        """
        raise NotImplementedError


class GoogleFinancePriceProvider:
    """Retrieves market data using Google Finance through the scraper infrastructure."""

    def __init__(self, context: playwright.async_api.BrowserContext, logger: Logger) -> None:
        """Initialize the price provider.

        Args:
            context (BrowserContext):
                Browser context used by the scraper.

            logger (Logger):
                Logger used to record scraper activity and errors.

        """
        self.__scraper = Scraper(context, logger)

    async def close(self) -> None:
        """Release resources used by the underlying scraper."""
        # Flush any pending scraper operations and release resources
        await self.__scraper.dispatch()

    async def get_price(self, ticker: str) -> decimal.Decimal | None:
        """Retrieve the current market price for a ticker.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            Decimal | None:
                The current market price if available.

        """
        async with self.__scraper as scraper:
            if not await scraper.is_valid_ticker(ticker):
                return None

            # Request the latest quote information for the ticker
            quote = await scraper.scrape_quote(ticker)

        return quote.header.price
