# Copyright (C) 2026 Lucas Dias

"""Textual application entry point and screen management.

This module defines :class:`UserInterface`, the root Textual application
responsible for managing screen navigation, database access, logging,
and global keyboard bindings.
"""

import typing

from textual.app import App
from textual.binding import Binding

from src.inout.screens.allocation_menu import AllocationMenu
from src.inout.screens.crud_menu import CrudMenu
from src.inout.screens.main_menu import MainMenu

if typing.TYPE_CHECKING:
    import sqlalchemy.ext.asyncio
    from textual._path import CSSPathType
    from textual.driver import Driver

    from src.database.database import Database
    from src.inout.logger import Logger


class UserInterface(App[None]):
    """Main Textual application.

    This class coordinates screen navigation, database access, and
    logging facilities used throughout the application. It also defines
    global key bindings for widget focus navigation and registers all
    available screens.
    """

    SCREENS: typing.ClassVar = {
        "main": MainMenu,
        "crud": CrudMenu,
        "alloc": AllocationMenu,
    }

    BINDINGS: typing.ClassVar = [
        Binding("up", "app.focus_previous", "Up"),
        Binding("left", "app.focus_previous", "Left"),
        Binding("down", "app.focus_next", "Down"),
        Binding("right", "app.focus_next", "Right"),
    ]

    def __init__(  # noqa: PLR0913
        self,
        database: Database,
        logger: Logger,
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

    @property
    def logger(self) -> Logger:
        """Return the application's logger instance.

        Returns:
            Logger:
                The application's logger instance.

        """
        return self.__logger

    def get_session(self) -> sqlalchemy.ext.asyncio.AsyncSession:
        """Create and return a new asynchronous database session.

        Returns:
            AsyncSession:
                An asynchronous SQLAlchemy session.

        """
        return self.__database.get_session()

    def on_mount(self) -> None:
        """Display the main menu when the application starts."""
        self.push_screen("main")
