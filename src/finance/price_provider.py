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

    async def get_price(self, ticker: str) -> decimal.Decimal:
        """Retrieve the current market price for a ticker.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            Decimal
                The current market price.

        """
        raise NotImplementedError

    async def is_valid_ticker(self, ticker: str) -> bool:
        """Determine whether a ticker symbol is valid.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            bool:
                True if the ticker is valid; otherwise, False.

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

    async def get_price(self, ticker: str) -> decimal.Decimal:
        """Retrieve the current market price for a ticker.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            Decimal:
                The current market price.

        Raises:
            ValueError:
                If a price cannot be obtained for the ticker.

        """
        async with self.__scraper as scraper:
            # Request the latest quote information for the ticker
            quote = await scraper.scrape_quote(ticker)

        price = quote.header.price

        # A quote was found, but it does not contain a valid price
        if price is None:
            msg = f"Could not retrieve price for ticker '{ticker}'"
            raise ValueError(msg)

        return price

    async def is_valid_ticker(self, ticker: str) -> bool:
        """Determine whether a ticker symbol exists and can be queried.

        Args:
            ticker (str):
                Asset ticker symbol.

        Returns:
            bool:
                True if the ticker is valid; otherwise, False.

        """
        # Delegate ticker validation to the Google Finance scraper
        async with self.__scraper as scraper:
            return await scraper.is_valid_ticker(ticker)
