# Copyright (C) 2026 Lucas Dias

"""Mixins for Textual widgets.

This module provides helper mixins that extend Textual widgets with
application-specific behavior and typing information.
"""

import typing

if typing.TYPE_CHECKING:
    from src.inout.user_interface import UserInterface


class UserInterfaceMixin:
    """Provide strongly-typed access to the application instance.

    This mixin overrides the :attr:`app` property and narrows its type to
    :class:`UserInterface`, allowing subclasses to access application-specific
    attributes and methods without additional casting.
    """

    @property
    def app(self) -> UserInterface:
        """Return the application as a :class:UserInterface.

        Returns:
            UserInterface:
                Active application instance.

        """
        # IGNORE: Ignored attribute access issue `app` as mixin cannot
        # import the necessary class as it will be imported by the later
        # class
        # IGNORE: Ignored unknown generic type of `App` to allow type override
        return typing.cast("UserInterface", super().app)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
