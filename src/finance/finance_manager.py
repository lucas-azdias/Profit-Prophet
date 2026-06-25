# Copyright (C) 2026 Lucas Dias

"""Finance management module.

The finance manager acts as the main orchestration layer between the
database, price providers, price automation infrastructure, and
portfolio business objects.
"""

import typing

import sqlalchemy
import sqlalchemy.orm

from src.database.models import AssetModel, AssetTypeModel, PortfolioModel
from src.finance.portfolio import Portfolio
from src.finance.price_provider import GoogleFinancePriceProvider

if typing.TYPE_CHECKING:
    import decimal

    from src.database.database import Database
    from src.finance.allocation import Allocation
    from src.finance.price_provider import PriceProvider
    from src.inout.logger import Logger
    from src.scrapers.browser_engine import BrowserEngine


class FinanceManager:
    """Manages portfolio data, price providers, and portfolio calculations.

    This class coordinates loading portfolio information from the database,
    creating portfolio domain objects, retrieving market prices, and building
    portfolio positions used throughout the application.
    """

    def __init__(self, database: Database, browser_engine: BrowserEngine, logger: Logger) -> None:
        """Initialize the finance manager.

        Args:
            database (Database):
                Database access layer used to retrieve portfolio data.

            browser_engine (BrowserEngine):
                Browser automation engine used by price providers.

            logger (Logger):
                Application logger.

        """
        self.__database = database
        self.__browser_engine = browser_engine
        self.__logger = logger

        # Populated after fetch is executed
        self.__portfolios: dict[int, Portfolio] | None = None

        # Initialized during start
        self.__price_provider: PriceProvider | None = None

    async def start(self) -> None:
        """Initialize external resources required by the manager.

        Creates the Google Finance price provider and its browser context.

        Raises:
            RuntimeError:
                If the manager has already been initialized.

        """
        if self.__price_provider is not None:
            msg = f"'{self.__class__.__name__}' is already initialized."
            raise RuntimeError(msg)

        # Creates a dedicated price provider with a new browser context
        self.__price_provider = GoogleFinancePriceProvider(
            await self.__browser_engine.new_context(),
            self.__logger,
        )

    async def fetch_data(self) -> None:
        """Load all portfolio data from the database.

        The query eagerly loads all related entities required for portfolio
        calculations, avoiding lazy-loading operations later in the workflow.

        Raises:
            RuntimeError:
                If the manager has not been started.

        """
        # Searches for all portfolios in the database
        async with self.__database.get_session() as session:
            portfolio_models = list(
                await session.scalars(
                    sqlalchemy.select(PortfolioModel).options(
                        sqlalchemy.orm.selectinload(PortfolioModel.asset_types)
                        .selectinload(AssetTypeModel.assets)
                        .selectinload(AssetModel.transactions),
                        sqlalchemy.orm.selectinload(PortfolioModel.asset_types)
                        .selectinload(AssetTypeModel.assets)
                        .selectinload(AssetModel.asset_type),
                        sqlalchemy.orm.selectinload(PortfolioModel.asset_types)
                        .selectinload(AssetTypeModel.assets)
                        .selectinload(AssetModel.score_answers),
                    ),
                ),
            )

        if self.__price_provider is None:
            msg = f"'{self.__class__.__name__}' have not been started yet"
            raise RuntimeError(msg)

        # Creates domain portfolio objects keyed by their ids
        self.__portfolios = {
            portfolio_model.id: Portfolio(portfolio_model, self.__price_provider)
            for portfolio_model in portfolio_models
        }

    async def build_data(self) -> None:
        """Build derived portfolio data.

        This method triggers position calculations for every fetched
        portfolio. It should be executed after :meth:`fetch_data`.
        """
        for portfolio in self.__fetched_portfolios.values():
            await portfolio.build_positions()

    @property
    def portfolios_info(self) -> list[tuple[int, str]]:
        """Return basic information about all loaded portfolios.

        Returns:
            list[tuple[int, str]]:
                Id numbers and names from all loaded portfolios.

        """
        return [(p.id, p.name) for p in self.__fetched_portfolios.values()]

    def new_allocation(self, portfolio_id: int, value: decimal.Decimal) -> Allocation:
        """Create a new allocation proposal for a portfolio.

        Args:
            portfolio_id: Identifier of the target portfolio.
            value: Amount available for allocation.

        Returns:
            Allocation:
                A newly created allocation instance.

        """
        return self.__fetched_portfolios[portfolio_id].new_allocation(value)

    @property
    def __fetched_portfolios(self) -> typing.Mapping[int, Portfolio]:
        # Checks if portfolio data has been loaded before
        # any operation attempts to access it
        if self.__portfolios is None:
            msg = "Portfolios have not been fetched"
            raise RuntimeError(msg)

        # Returns the fetched portfolio collection
        return self.__portfolios
