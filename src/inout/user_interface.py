# Copyright (C) 2026 Lucas Dias

"""Textual application entry point and screen management.

This module defines `UserInterface`, the root Textual application responsible
for managing screen navigation, database access, logging, and global keyboard
bindings.
"""

import typing

from textual import on
from textual.app import App
from textual.events import Mount

from src.finance.finance_manager import FinanceManager
from src.inout.screens.allocation_menu import AllocationMenu
from src.inout.screens.crud_menu import CrudMenu
from src.inout.screens.main_menu import MainMenu

if typing.TYPE_CHECKING:
    import sqlalchemy.ext.asyncio
    from textual._path import CSSPathType
    from textual.driver import Driver

    from src.database.database import Database
    from src.inout.logger import Logger
    from src.inout.user_screen import UserScreen
    from src.scrapers.browser_engine import BrowserEngine


class UserInterface(App[None]):
    """Main Textual application.

    This class coordinates screen navigation, database access, and
    logging facilities used throughout the application. It also defines
    global key bindings for widget focus navigation and registers all
    available screens.
    """

    # IGNORE: The type was overriden to allow access to screens inside
    # and avoid complain for unknown generic type as Textual
    # doesn't specify it as `Any`
    SCREENS: typing.ClassVar[dict[str, type[UserScreen]]] = {  # pyright: ignore[reportIncompatibleVariableOverride]
        "main": MainMenu,
        "crud": CrudMenu,
        "alloc": AllocationMenu,
    }

    DEFAULT_CSS = """
    .screen {
        width: 100%;
        height: 100%;
        padding-top: 1;
    }
    """

    # IGNORE: It is importing parameters from Textual `App` class,
    # so it was necessary to ignore limit of them
    def __init__(  # noqa: PLR0913
        self,
        database: Database,
        logger: Logger,
        browser_engine: BrowserEngine,
        *,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool | None = None,
    ) -> None:
        """Initialize the application.

        Args:
            database (Database):
                Database service used to create and manage asynchronous
                SQLAlchemy sessions.

            logger (Logger):
                Logger instance used to record application events and
                diagnostics.

            browser_engine (BrowserEngine):
                Browser automation engine responsible for managing the Playwright
                lifecycle, browser instance, and creation of isolated browser
                contexts used by scraping operations.

            driver_class (type[Driver] | None):
                Optional Textual driver implementation used to run the
                application.

            css_path (CSSPathType | None):
                Path to a CSS stylesheet applied to the application's user
                interface.

            watch_css (bool):
                Whether stylesheet changes should be automatically detected and
                reloaded during execution.

            ansi_color (bool | None):
                Whether ANSI color support should be enabled.

        """
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.__database = database
        self.__logger = logger
        self.__finance_manager = FinanceManager(self.__database, browser_engine, self.__logger)

    @property
    def logger(self) -> Logger:
        """Return the application's logger instance.

        Returns:
            Logger:
                The application's logger instance.

        """
        return self.__logger

    @property
    def finance_manager(self) -> FinanceManager:
        """Return the application's finance manager.

        Returns:
            FinanceManager:
                Finance manager responsible for portfolio allocation,
                asset analysis, and other financial operations.

        """
        return self.__finance_manager

    def get_session(self) -> sqlalchemy.ext.asyncio.AsyncSession:
        """Create and return a new asynchronous database session.

        Returns:
            AsyncSession:
                An asynchronous SQLAlchemy session.

        """
        return self.__database.get_session()

    @on(Mount)
    def handle_mount(self) -> None:
        """Display the main menu when the application starts."""
        # Starts finance manager
        self.run_worker(self.__finance_manager.start())

        # Installs main screen
        self.push_screen("main")
