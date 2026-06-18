# Copyright (C) 2026 Lucas Dias

"""Main menu screen for the user interface.

This module defines :class:`MainMenu`, the application's primary
navigation screen.
"""

import typing

import pyfiglet
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
        width: 100%;
        height: 100%;
        margin-top: 3;
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
                yield Button("New allocation", id="button-alloc", classes="button")
                yield Button("Visualize data", id="button-view", classes="button")
                yield Button("Edit data", id="button-crud", classes="button")
                yield Button("Exit", id="button-exit", classes="button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events from the main menu.

        Args:
            event (Button.Pressed):
                Event generated when a button is pressed.

        """
        match event.button.id:
            case "button-alloc":
                self.app.logger.log("Pushing allocation menu screen...")
                self.app.push_screen("alloc")
            case "button-view":
                self.notify("Visualizing data...")
            case "button-crud":
                self.app.logger.log("Pushing CRUD menu screen...")
                self.app.push_screen("crud")
            case "button-exit":
                msg = "Exiting..."
                self.notify(msg)
                self.app.logger.log(msg)
                self.set_timer(0.5, self.app.exit)
            case _:
                pass
