# Copyright (C) 2026 Lucas Dias

"""Base screen abstractions for the Textual user interface.

This module defines `UserScreen`, an abstract base class used by all
application screens. It provides a common layout consisting of a header,
body, and footer, and exposes the application instance as a strongly
typed `UserInterface`.
"""

import abc
import typing

from textual import on
from textual.binding import Binding
from textual.events import Mount
from textual.screen import Screen
from textual.widgets import Footer, Header

from src.inout.mixins import UserInterfaceMixin

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class UserScreen(UserInterfaceMixin, Screen[None]):
    """Base class for all application screens.

    This class provides a common layout consisting of a header, a body,
    and a footer. Subclasses must implement `compose_body` to define
    the screen-specific widgets displayed between the header and footer.
    """

    BINDINGS: typing.ClassVar = [
        Binding("backspace", "go_back", " Go back"),  # Needs an extra space for formatting purposes
        Binding("escape", "unfocus_widget", "Unfocus"),
    ]

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

    @on(Mount)
    def handle_mount(self) -> None:
        """Remove focus from the currently focused widget on mount."""
        self.call_after_refresh(lambda: self.app.set_focus(None))

    def action_go_back(self) -> None:
        """Navigate back to the previous screen if possible."""
        # Only pop if there is something to go back to
        if len(self.app.screen_stack) <= 1:
            return

        self.app.pop_screen()

    def action_unfocus_widget(self) -> None:
        """Remove focus from the currently focused widget."""
        self.app.set_focus(None)
