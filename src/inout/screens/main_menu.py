# Copyright (C) 2026 Lucas Dias

"""Main menu screen for the user interface.

This module defines :class:`MainMenu`, the application's primary
navigation screen.
"""

import typing

import pyfiglet
from textual import on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Static

from src.inout.user_screen import UserScreen

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class MainMenu(UserScreen):
    """Main navigation screen of the application.

    This screen is displayed when the application starts and serves as
    the central entry point for all major workflows.
    """

    TITLE = "Main Menu"

    CSS = """
    .screen {
        margin-top: 2;
        margin-bottom: 2;
    }

    .title {
        width: 48;
        height: 100%;
        content-align: left middle;
        text-style: bold;
        margin-left: 15;
        margin-right: 2;
    }

    .menu-box {
        width: 1fr;
        height: 100%;
        align: center middle;
    }

    .menu {
        width: auto;
        height: 100%;
        align: center middle;
    }

    .button {
        width: 26;
        height: 3;
    }
    """

    @typing.override
    def compose_body(self) -> ComposeResult:
        figlet = pyfiglet.Figlet(font="speed", width=48)

        with Horizontal(classes="screen"):
            yield Static(figlet.renderText("Profit Prophet"), classes="title")
            with Container(classes="menu-box"), VerticalScroll(classes="menu", can_focus=False):
                yield Button("New allocation", id="button-push-alloc", classes="button button-push")
                yield Button("Visualize data", id="button-push-view", classes="button button-push")
                yield Button("Edit data", id="button-push-crud", classes="button button-push")
                yield Button("Exit", id="button-exit", classes="button")

    @typing.override
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Intercept and optionally block an action before it is executed.

        This method is called by Textual before dispatching an action.
        It allows the screen to approve, deny, or defer handling of actions
        triggered by key bindings or programmatic calls.

        Args:
            action (str):
                The name of the action being requested (e.g. "go_back").

            parameters (tuple[object, ...]):
                A tuple of positional arguments supplied to the action handler.

        Returns:
            bool | None:
                - True: explicitly allow the action;
                - False: block the action;
                - None: defer decision to the next handler in the chain.

        """
        # Blocks "go_back" action
        if action == "go_back":
            return False
        return super().check_action(action, parameters)

    @on(Button.Pressed, ".button-push")
    def handle_push_screen(self, event: Button.Pressed) -> None:
        """Handle navigation button presses and push the corresponding screen.

        This handler processes all buttons with the `.button-push` CSS class,
        extracts the target screen name from the button ID, validates it,
        resolves the corresponding screen from the application's screen
        registry, and pushes it onto the navigation stack.

        Args:
            event (Button.Pressed):
                Event emitted when a navigation button is pressed.

        Raises:
            RuntimeError:
                If the button has no ID, the ID does not follow the expected
                naming convention, or the referenced screen is not registered
                in the application.

        """
        prefix = "button-push-"

        if not event.button.id:
            msg = f"Couldn't find {event.button.__class__.__name__}'s id"
            raise RuntimeError(msg)

        if not event.button.id.startswith(prefix):
            msg = (
                f"{event.button.__class__.__name__}'s id ('{event.button.id}') "
                f"doesn't contain prefix '{prefix}'"
            )
            raise RuntimeError(msg)

        # Gets the screen name from button's id
        screen_name = event.button.id.removeprefix(prefix)

        # Searches for the respective screen
        screen = self.app.SCREENS.get(screen_name, None)

        if not screen:
            msg = f"Couldn't find screen '{screen_name}' inside application"
            raise RuntimeError(msg)

        # Pushes screen
        self.app.logger.log(f"Pushing {screen.TITLE} screen...")
        self.app.push_screen(screen_name)

    @on(Button.Pressed, "#button-exit")
    def handle_exit(self) -> None:
        """Handle exiting the application.

        Displays a notification and logs the exit event, then schedules
        the application to terminate after a brief delay to allow UI
        feedback to be visible.
        """
        msg = "Exiting..."
        self.notify(msg)
        self.app.logger.log(msg)
        self.set_timer(0.5, self.app.exit)
