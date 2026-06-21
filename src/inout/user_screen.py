# Copyright (C) 2026 Lucas Dias

"""Base screen abstractions for the Textual user interface.

This module defines :class:`UserScreen`, an abstract base class used by
all application screens. It provides a common layout consisting of a
header, body, and footer, and exposes the application instance as a
strongly typed :class:`UserInterface`.
"""

import abc
import typing

from textual.screen import Screen
from textual.widgets import Footer, Header

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.inout.user_interface import UserInterface


class UserScreen(Screen[None]):
    """Base class for all application screens.

    This class provides a common layout consisting of a header, a body,
    and a footer. Subclasses must implement :meth:`compose_body` to
    define the screen-specific widgets displayed between the header and
    footer.

    The :attr:`app` property is narrowed to :class:`UserInterface` to
    provide access to application-specific functionality with proper
    static typing.
    """

    @property
    @typing.override
    def app(self) -> UserInterface:
        # IGNORE: Ignored unknown generic type of `App` to allow type override
        return typing.cast("UserInterface", super().app)  # pyright: ignore[reportUnknownMemberType]

    @typing.override
    def compose(self) -> ComposeResult:
        yield Header()
        yield from self.compose_body()
        yield Footer()

    @abc.abstractmethod
    def compose_body(self) -> ComposeResult:
        """Compose the widgets that form the main content of the screen.

        Returns:
            ComposeResult:
                The widgets to be displayed between the screen header and
                footer.

        """
