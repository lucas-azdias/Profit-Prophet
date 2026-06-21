# Copyright (C) 2026 Lucas Dias

"""Google Finance quote section models.

This module defines the data structures used to describe and extract
individual sections and fields from a Google Finance quote page.

These models are consumed by the scraper layer to dynamically interpret
DOM structure and transform raw page content into strongly typed DTOs.
"""

import enum
import typing

import pydantic

from src.dtos.base_dto import BaseDTO

if typing.TYPE_CHECKING:
    import collections.abc
    import re


class QuoteSectionFieldSearchMethods(enum.Enum):
    """Defines supported strategies for extracting a field value from the DOM.

    These methods determine how the scraper locates raw text before any
    parsing or normalization is applied.

    Attributes:
        XPATH (enum.auto):
            Extract value directly using an XPath expression.

        SPLIT_LINES (enum.auto):
            Extract value by scanning inner text line-by-line and locating
            structured label/value pairs.

    """

    XPATH = enum.auto()
    SPLIT_LINES = enum.auto()


class QuoteSectionFieldMetadataDTO(BaseDTO):
    """Metadata describing how a single quote field is extracted and parsed.

    This model is used by the scraper to determine the locatation of the
    raw value in the DOM, the transformation using regex rules and how to
    post-process the extracted data.

    Attributes:
        search_method (QuoteSectionFieldSearchMethods):
            Strategy used to extract the raw value from the page.

        label (str):
            XPath expression or text label used depending on the search method.

        regex_pattern (re.Pattern[str] | None):
            Optional compiled regex used to extract structured data from the
            raw text.

        regex_order (collections.abc.Sequence[str] | None):
            Optional ordering of named regex groups used when assembling the
            final output.

        separator (str):
            String used to join multiple extracted regex groups.

        post_regex (
            typing.Callable[[collections.abc.Sequence[str]], collections.abc.Sequence[str]]
        ):
            Callable applied after regex extraction for final transformation
            of captured values.

    """

    search_method: QuoteSectionFieldSearchMethods
    label: str
    regex_pattern: re.Pattern[str] | None = pydantic.Field(default=None)
    regex_order: collections.abc.Sequence[str] | None = pydantic.Field(default=None)
    separator: str = pydantic.Field(default=" ")
    post_regex: typing.Callable[[collections.abc.Sequence[str]], collections.abc.Sequence[str]] = (
        pydantic.Field(
            default=lambda x: x,
        )
    )


class QuoteSectionDTO(BaseDTO):
    """Base model for a Google Finance quote section.

    This class acts as a structural placeholder for concrete quote sections
    (e.g. header, overview, statistics). Each subclass defines its own
    fields and extraction metadata.
    """
