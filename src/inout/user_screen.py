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
    import collections.abc

    from textual.app import ComposeResult
    from textual.widget import Widget


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

    async def execute_loading_worker[R](
        self,
        widget: Widget,
        awaitable: collections.abc.Awaitable[R],
        successful_msg: str,
        *,
        catchable_exceptions: tuple[type[BaseException], ...] = (),
        exception_msg: str = "Error occurred",
    ) -> bool:
        """Execute an asynchronous task while displaying a loading indicator on a widget.

        This method manages the loading state of a specific widget during the execution
        of a background awaitable task. It handles exceptions gracefully, displays user
        notifications for success or failure, and guarantees that the loading spinner
        is turned off when completed.

        Args:
            widget (Widget):
                The Textual widget that should display the loading spinner.

            awaitable (Awaitable[R]):
                The coroutine or awaitable task to be executed.

            successful_msg (str):
                The toast notification message to display upon success.

            catchable_exceptions (tuple[type[BaseException], ...]):
                A tuple of exception classes to intercept and handle.

            exception_msg (str):
                The toast notification error message to display if an expected
                exception is raised.

        Returns:
            bool:
                True if the awaitable completed successfully without raising a caught
                exception; False otherwise.

        """
        # Turns on built-in loading indicator spinner on widget
        widget.loading = True

        # Final result sucess flag
        result = False

        try:
            # Executes and awaits awaitable
            await awaitable
        except catchable_exceptions:
            self.notify(exception_msg, severity="error")
        else:
            # Notifies about sucessful execution
            self.notify(successful_msg)

            # Changes result to sucess
            result = True
        finally:
            # Turns off the loading indicator
            widget.loading = False

        return result
