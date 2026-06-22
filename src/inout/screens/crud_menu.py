# Copyright (C) 2026 Lucas Dias

"""CRUD screen for managing database records.

This module defines :class:`CrudMenu`, a generic database management
screen that automatically discovers SQLAlchemy models and provides
interfaces for creating, updating, deleting, and viewing records.

Each registered model is displayed in its own tab, allowing users to
perform CRUD operations through a common user interface without
requiring model-specific screens.
"""

import datetime
import enum
import typing

import sqlalchemy
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Rule, Select, TabbedContent, TabPane

from src.database.base import Base
from src.inout.user_screen import UserScreen

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget

    from src.database.model import Model


class CrudSelectValues(enum.Enum):
    """Supported CRUD operations available in the interface.

    Attributes:
        ADD (enum.auto):
            Create a new record in the selected table.

        EDIT (enum.auto):
            Update the currently selected record in the data table.

        DELETE (enum.auto):
            Remove the currently selected record from the database.

    """

    ADD = enum.auto()
    EDIT = enum.auto()
    DELETE = enum.auto()


class CrudMenu(UserScreen):
    """Database management screen.

    This screen dynamically generates a tab for each registered database
    model and displays its contents in a data table. Users can create,
    update, and delete records through a unified interface.

    Operations are performed against the currently selected model and
    are synchronized with the database asynchronously.
    """

    TITLE = "Edit data"

    BINDINGS: typing.ClassVar = [
        Binding("r", "refresh_data", "Refresh data"),
    ]

    CSS = """
    .input-options {
        width: 1fr;
        height: 3;
    }

    .input-box {
        width: 1fr;
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
        width: 15;
    }

    .button-confirm {
        width: 0;
    }
    """

    @typing.override
    def compose_body(self) -> ComposeResult:
        self.__models: list[type[Model]] = sorted(
            [mapper.class_ for mapper in Base.registry.mappers],
            key=lambda x: x.__name__,
        )

        with VerticalScroll(classes="screen", can_focus=False), TabbedContent():
            for model in self.__models:
                with TabPane(
                    " ".join([s.capitalize() for s in model.__plural__.split("_")]),
                    id=f"tab-{model.__tablename__}",
                ):
                    with Horizontal(classes="input-options"):
                        with Vertical(classes="input-box"):
                            yield Input(
                                id=f"input-{model.__tablename__}",
                                placeholder="Type row data...",
                                tooltip=(
                                    'Type row data, separate columns with ";" '
                                    'and use "@" for default value'
                                ),
                            )
                        with Horizontal(classes="options-box"):
                            yield Select[CrudSelectValues](
                                id=f"select-{model.__tablename__}",
                                classes="select",
                                prompt="Select",
                                options=[
                                    ("Add", CrudSelectValues.ADD),
                                    ("Edit", CrudSelectValues.EDIT),
                                    ("Delete", CrudSelectValues.DELETE),
                                ],
                                tooltip="Select an operation",
                            )
                            yield Button(
                                "▶",
                                id=f"button-confirm-{model.__tablename__}",
                                classes="button-confirm",
                                tooltip="Confirm",
                            )
                    yield Rule(line_style="solid", orientation="horizontal")
                    yield DataTable[str](id=f"data-table-{model.__tablename__}", cursor_type="row")

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Load data for the newly activated tab.

        Args:
            event (TabbedContent.TabActivated):
                Event generated when a tab becomes active.

        """
        self.app.logger.log(f"Changing active tab to '{event.tab.label}'...")

        # Finds the current model
        model = self.__find_current_model(event.pane, "tab-")

        # Runs worker that populates data table with database data
        self.run_worker(self.__load_data_table(model))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events.

        Args:
            event (Button.Pressed):
                Event generated when a button is pressed.

        """
        button_confirm_prefix = "button-confirm-"

        # Checks if it is the confirmation button
        if not event.button.id or not event.button.id.startswith(button_confirm_prefix):
            self.app.logger.log("Unknown button was pressed and ignored", msg_type="warning")
            return

        # Finds the current model
        model = self.__find_current_model(event.button, button_confirm_prefix)

        # Gets the select element
        select = typing.cast(
            "Select[CrudSelectValues]",
            self.query_one(f"#select-{model.__tablename__}", Select),
        )

        # Matches the selected action and executes it
        match select.value:
            case CrudSelectValues.ADD:
                self.run_worker(self.__add_instance(model))
            case CrudSelectValues.EDIT:
                self.run_worker(self.__edit_instance(model))
            case CrudSelectValues.DELETE:
                self.run_worker(self.__delete_instance(model))
            case _:
                msg = "Select an operation first"
                self.notify(msg, severity="warning")
                self.app.logger.log(msg, msg_type="warning")

    def action_refresh_data(self) -> None:
        """Refresh the currently displayed model data.

        This action clears the active input field and reloads the records
        shown in the current tab's data table.

        """
        # Queries for the current tab
        tabs = self.query_one(TabbedContent)
        current_tab = tabs.get_pane(tabs.active)

        # Finds the current model
        model = self.__find_current_model(current_tab, "tab-")

        # Clears the input and reloads data in the table
        self.run_worker(self.__refresh_data(model))

    @staticmethod
    def __parse_bool(value: str) -> bool:
        match value.strip().lower():
            case "true" | "1" | "yes" | "y":
                return True
            case "false" | "0" | "no" | "n":
                return False
            case _:
                msg = f"Invalid boolean value: {value}"
                raise ValueError(msg)

    def __find_current_model(self, widget: Widget, prefix: str) -> type[Model]:
        if not widget.id:
            msg = f"Couldn't find {widget.__class__.__name__}'s id"
            raise RuntimeError(msg)

        if not widget.id.startswith(prefix):
            msg = (
                f"{widget.__class__.__name__}'s id ('{widget.id}') "
                f"doesn't contain prefix '{prefix}'"
            )
            raise RuntimeError(msg)

        # Gets the tablename from tab pane
        tablename = widget.id.removeprefix(prefix)

        # Finds the model
        model: type[Model] | None = None
        for m in self.__models:
            if m.__tablename__ == tablename:
                model = m

        if not model:
            msg = f"Couldn't find {widget.__class__.__name__}'s respective database model"
            raise RuntimeError(msg)

        return model

    def __retrieve_input_data(self, model: type[Model]) -> dict[str, object] | None:
        # Gets the input element
        input_field = self.query_one(f"#input-{model.__tablename__}", Input)

        # Parses values inside input
        values = [value.strip() for value in input_field.value.split(";")]

        # Checks if any value was given or if only separators were given
        if not values or not input_field.value.replace(";", ""):
            msg = "No value was given in the input field"
            self.notify(msg, severity="warning")
            self.app.logger.log(msg, msg_type="warning")
            return None

        # Retrieves all columns
        columns = [column for column in model.__table__.columns if not column.primary_key]

        # Checks expected columns quantity
        if len(values) != len(columns):
            msg = f"Expected {len(columns)} values, got {len(values)}"
            self.notify(msg, severity="error")
            self.app.logger.log(msg, msg_type="error")
            return None

        # Typed data for each column
        data: dict[str, object] = {}

        # Standard converters for some python types
        converters: dict[type[object], typing.Callable[[str], object]] = {
            bool: lambda x: bool(self.__parse_bool(x)),
            datetime.datetime: datetime.datetime.fromisoformat,
            datetime.date: datetime.date.fromisoformat,
        }

        # Coverts each column's value to the correct type
        for column, value in zip(columns, values, strict=True):
            python_type: type[object] = getattr(column.type, "python_type", str)

            # Default case
            if value == "@":
                if column.default is not None or column.nullable:
                    continue

                msg = f"Column '{column.name}' requires a value."
                self.notify(msg, severity="warning")
                self.app.logger.log(msg, msg_type="warning")
                return None

            # Gets standard converter
            converter = converters.get(python_type, python_type)

            try:
                # Common case
                data[column.name] = converter(value)

            except ValueError:
                msg = f"Invalid value for column '{column.name}'"
                self.notify(msg, severity="error")
                self.app.logger.log(msg, msg_type="error")
                return None

        return data

    async def __load_data_table(self, model: type[Model]) -> None:
        # Gets the respective data table
        data_table = typing.cast(
            "DataTable[str]",
            self.query_one(f"#data-table-{model.__tablename__}", DataTable),
        )

        # Clears data in the table
        data_table.clear(columns=True)

        # Recovers all rows in database
        async with self.app.get_session() as session:
            result = await session.execute(sqlalchemy.select(model))
            rows = result.scalars().all()

        # Gets all columns in model
        columns = model.__table__.columns.keys()

        # Populates columns
        for col in columns:
            data_table.add_column(col)

        # Populates rows
        for row in rows:
            data_table.add_row(*[getattr(row, c) for c in columns])

    async def __refresh_data(self, model: type[Model]) -> None:
        # Gets the input element
        input_field = self.query_one(f"#input-{model.__tablename__}", Input)

        # Clears the input
        input_field.clear()

        # Reloads data in the table
        await self.__load_data_table(model)

    async def __add_instance(self, model: type[Model]) -> None:
        self.app.logger.log(f"Adding instance to '{model.__tablename__}'")

        # Retrieves parsed input data
        input_data = self.__retrieve_input_data(model)

        if not input_data:
            return

        # Commits the change to the database
        async with self.app.get_session() as session:
            session.add(model(**input_data))
            await session.commit()

        # Clears the input and reloads data in the table
        await self.__refresh_data(model)

        self.app.logger.log(f"Added instance to '{model.__tablename__}' successfully")

    async def __edit_instance(self, model: type[Model]) -> None:
        self.app.logger.log(f"Editing '{model.__tablename__}' instance")

        # Retrieves parsed input data
        input_data = self.__retrieve_input_data(model)

        if not input_data:
            return

        # Gets the respective data table
        data_table = typing.cast(
            "DataTable[str]",
            self.query_one(f"#data-table-{model.__tablename__}", DataTable),
        )

        # Gets selected position
        row_key, _ = data_table.coordinate_to_cell_key(data_table.cursor_coordinate)

        pk_data: dict[str, object] = {}  # All primary keys
        row_data: dict[str, str] = {}  # Selected row's data (ignores primary key columns)

        for column, value in zip(model.__table__.columns, data_table.get_row(row_key), strict=True):
            if column.primary_key:
                pk_data[column.key] = value
            else:
                row_data[column.key] = value

        # Compares input and table data to define data to be updated
        update_data = {
            key: value for key, value in input_data.items() if str(value) != row_data[key]
        }

        # Commits the change to the database
        async with self.app.get_session() as session:
            await session.execute(
                sqlalchemy.update(model).filter_by(**pk_data).values(**update_data),
            )
            await session.commit()

        # Clears the input and reloads data in the table
        await self.__refresh_data(model)

        self.app.logger.log(f"Edited '{model.__tablename__}' instance successfully")

    async def __delete_instance(self, model: type[Model]) -> None:
        self.app.logger.log(f"Deleting '{model.__tablename__}' instance")

        # Gets the respective data table
        data_table = typing.cast(
            "DataTable[str]",
            self.query_one(f"#data-table-{model.__tablename__}", DataTable),
        )

        # Gets selected position
        row_key, _ = data_table.coordinate_to_cell_key(data_table.cursor_coordinate)

        pk_data: dict[str, object] = {}  # All primary keys
        row_data: dict[str, str] = {}  # Selected row's data (ignores primary key columns)

        for column, value in zip(model.__table__.columns, data_table.get_row(row_key), strict=True):
            if column.primary_key:
                pk_data[column.key] = value
            else:
                row_data[column.key] = value

        # Commits the change to the database
        async with self.app.get_session() as session:
            await session.execute(sqlalchemy.delete(model).filter_by(**pk_data))
            await session.commit()

        # Clears the input and reloads data in the table
        await self.__refresh_data(model)

        self.app.logger.log(f"Deleted '{model.__tablename__}' instance successfully")
