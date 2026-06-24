# Copyright (C) 2026 Lucas Dias

"""Portfolio allocation generation screen.

This module defines :class:`AllocationMenu`, a screen responsible for
loading portfolio data, building portfolio positions, and generating
allocation suggestions based on a user-provided investment amount.

Users can select a portfolio, enter an allocation value, and visualize
the resulting allocation in a tabular format. Portfolio data can also be
refreshed on demand through a keyboard shortcut.
"""

import decimal
import typing

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key, Mount, ScreenResume, ScreenSuspend
from textual.types import NoSelection
from textual.widgets import Button, DataTable, Input, Rule, Select

from src.finance.positions.position import Position
from src.inout.user_screen import UserScreen

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult


class AllocationMenu(UserScreen):
    """Portfolio allocation generation screen.

    This screen allows users to select a portfolio, enter an allocation
    amount, and generate a suggested allocation across portfolio
    positions.

    Portfolio information is loaded asynchronously from the finance
    manager and displayed through interactive Textual widgets. Generated
    allocations are presented in a data table for review.
    """

    TITLE = "New allocation"

    BINDINGS: typing.ClassVar = [
        Binding("r", "refresh_data", "Refresh data"),
    ]

    CSS = """
    .screen {
        padding-top: 2;
    }

    .input-options {
        width: 1fr;
        height: 3;
    }

    .input-box {
        width: 50;
        align-horizontal: left;
    }

    .options-box {
        width: auto;
        height: 100%;
        align-horizontal: right;
    }

    .options-box > * {
        margin-right: 1;
    }

    .select {
        width: 25;
    }

    Button {
        width: 0;
    }
    """

    @typing.override
    def compose_body(self) -> ComposeResult:
        with VerticalScroll(classes="screen", can_focus=False):
            with Horizontal(classes="input-options"):
                with Vertical(classes="input-box"):
                    yield Input(
                        id="input",
                        classes="portfolio-control",
                        placeholder="Enter the allocation amount...",
                        tooltip="Enter the amount to allocate to the portfolio",
                        disabled=True,
                    )
                with Horizontal(classes="options-box"):
                    yield Select[int](
                        id="select",
                        classes="select portfolio-control",
                        prompt="Select portfolio",
                        options=[],
                        tooltip="Select a portfolio to allocate",
                        disabled=True,
                    )
                    yield Button(
                        "Generate",
                        id="button-confirm",
                        classes="button-confirm portfolio-control",
                        tooltip="Generate new allocation",
                        disabled=True,
                    )
                    yield Button(
                        "Clear",
                        id="button-clear",
                        classes="button-clear",
                        tooltip="Clear allocation",
                    )
            yield Rule(line_style="solid", orientation="horizontal")
            yield DataTable[str](id="data-table", cursor_type="row")

    @on(Mount)
    @typing.override
    def handle_mount(self) -> None:
        """Initialize the allocation table.

        Discovers all public allocation properties exposed by
        :class:`Position` and creates a corresponding column in the data
        table.
        """
        # Gets all columns in position based on property methods
        columns = [
            name
            for name in Position.__dict__
            if isinstance(getattr(Position, name, None), property)
        ]

        # Gets the respective data table
        data_table = typing.cast("DataTable[str]", self.query_one("#data-table", DataTable))

        # Populates columns
        for col in columns:
            data_table.add_column(col)

    @on(ScreenResume)
    def handle_screen_resume(self) -> None:
        """Load portfolio data when the screen becomes active."""
        # Fetches all registered portfolios for select options
        self.run_worker(self.__get_portfolios(), exclusive=True)

    @on(ScreenSuspend)
    def handle_screen_suspend(self) -> None:
        """Cancel active workers when leaving the screen.

        Prevents background operations from continuing after the screen is
        no longer visible.
        """
        # Cancels all workers when exiting the screen
        self.workers.cancel_all()

    @on(Button.Pressed, "#button-confirm")
    def handle_button_confirm(self) -> None:
        """Generate an allocation using the current form values."""
        # Generates the allocation and shows it
        self.__generate_allocation()

    @on(Button.Pressed, "#button-clear")
    def handle_button_clear(self) -> None:
        """Remove the allocation from the data table."""
        # Gets the data table
        data_table = typing.cast("DataTable[str]", self.query_one("#data-table", DataTable))

        # Clears data in the table
        data_table.clear()

    @on(Key)
    def handle_key_pressed(self, event: Key) -> None:
        """Handle key press events.

        Args:
            event (Key):
                Event generated when a key is pressed.

        """
        match event.key:
            case "ctrl+o":
                self.notify("Generating allocation...")
                self.query_one("#button-confirm", Button).press()
            case "ctrl+l":
                self.notify("Cleaned allocation")
                self.query_one("#button-clear", Button).press()
            case _:
                pass

    def action_refresh_data(self) -> None:
        """Refresh portfolio information and rebuild allocation data."""
        self.run_worker(self.__refresh_data(), exclusive=True)

    async def __refresh_data(self) -> None:
        # Fetches all registered portfolios for select options
        await self.__get_portfolios()

        # Generates the allocation and shows it
        self.__generate_allocation(show_errors=False)

    async def __get_portfolios(self) -> None:
        # Fetches all portfolios' data
        await self.app.finance_manager.fetch_data()
        portfolios_info = self.app.finance_manager.portfolios_info

        has_portfolios = bool(portfolios_info)

        # Disable/enable elements based on existence of portfolios
        for widget in self.query(".portfolio-control"):
            widget.disabled = not has_portfolios

        # Notifies the user if no portfolio was found in the database
        if not has_portfolios:
            self.notify("No portfolios were found")
            return

        # Notifies the user on the amount of found portfolios
        portfolios_quantity = len(portfolios_info)
        if portfolios_quantity == 1:
            self.notify(f"{portfolios_quantity} portfolio was found")
        else:
            self.notify(f"{portfolios_quantity} portfolios were found")

        # Populates the select options with the found portfolios
        select = typing.cast("Select[int]", self.query_one("#select", Select))
        select.set_options(
            [(name, portfolio_id) for portfolio_id, name in portfolios_info],
        )

        # Blocks confirmm button for building
        confirm_button = self.query_one("#button-confirm", Button)
        confirm_button.disabled = True

        # Builds necessary data inside portfolios
        await self.app.finance_manager.build_data()

        # Notifies about building completion
        self.notify("Data has been built")

        # Releases confirm button after building
        confirm_button.disabled = False

    def __generate_allocation(self, *, show_errors: bool = True) -> None:
        # Gets the input element
        input_field = self.query_one("#input", Input)

        # Parses the input value
        try:
            value = decimal.Decimal(input_field.value)
        except decimal.InvalidOperation:
            msg = "Invalid value was given in input field"
            if show_errors:
                self.notify(msg, severity="error")
            self.app.logger.log(msg, msg_type="error")
            return

        # Gets the select element
        select = typing.cast("Select[int]", self.query_one("#select", Select))

        # Gets the selected portfolio's id
        portfolio_id = select.value

        # Notifies user if no portfolio was selected
        if isinstance(portfolio_id, NoSelection):
            msg = "Select a portfolio first"
            if show_errors:
                self.notify(msg, severity="warning")
            self.app.logger.log(msg, msg_type="warning")
            return

        # Generates the new allocation
        allocation = self.app.finance_manager.new_allocation(portfolio_id, value)

        # Gets the data table
        data_table = typing.cast("DataTable[str]", self.query_one("#data-table", DataTable))

        # Clears data in the table
        data_table.clear()

        # Gets all columns in data table
        columns = [str(column.label) for column in data_table.columns.values()]

        # Tabulates the allocation data
        rows: list[dict[str, str]] = [
            {column: getattr(position, column) for column in columns}
            for position in allocation.positions
        ]

        # Populates rows
        for row in rows:
            # Skips if row has no data (avoids empty rows)
            if not row:
                continue

            data_table.add_row(*[str(row[c]) for c in columns])
