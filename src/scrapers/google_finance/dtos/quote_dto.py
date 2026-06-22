# Copyright (C) 2026 Lucas Dias

"""Google Finance quote data transfer objects.

This module defines the DTOs used to represent a fully parsed Google Finance
quote page. It includes both high-level structural models (such as the full
quote container) and metadata models used to describe how each section is
extracted from the DOM via XPath selectors.
"""

import typing

import pydantic

from src.dtos.base_dto import BaseDTO

if typing.TYPE_CHECKING:
    from src.scrapers.google_finance.dtos.quote_sections_dto import (
        QuoteSectionHeaderDTO,
        QuoteSectionOverviewDTO,
    )


class QuoteSectionMetadataDTO(BaseDTO):
    """Metadata describing how a quote section is extracted from the DOM.

    This DTO provides configuration required to locate and extract a specific
    section of a Google Finance quote page. It is primarily used as
    `json_schema_extra` attached to DTO fields, enabling runtime scraping
    logic to resolve DOM locations dynamically.

    Attributes:
        xpath (str):
            Absolute or relative XPath expression pointing to the root element
            of the section within the Google Finance page structure.

    """

    xpath: str


class QuoteDTO(BaseDTO):
    """Represents a single Google Finance quote.

    All monetary values, ratios, percentages, and large numeric metrics
    are stored as :class:`Decimal` instances for precision. And percentage
    values are normalized to decimal fractions.

    Datetime values are timezone-aware.

    Attributes:
        ticker (str):
            Exchange-qualified ticker symbol (e.g. `AAPL:NASDAQ`).

        header (QuoteSectionHeaderDTO):
            High-level header information.

        overview (QuoteSectionOverviewDTO):
            Fundamental and statistical market indicators.

    """

    ticker: str

    header: QuoteSectionHeaderDTO = pydantic.Field(
        json_schema_extra=QuoteSectionMetadataDTO(
            xpath=(
                "/html/body/c-wiz[3]/div[1]/div[1]/div[1]/div[2]/div[2]/"
                "div[1]/div[1]/c-wiz[1]/div[1]/div[3]/c-wiz[1]/div[1]/"
                "div[1]/div[1]/div[1]"
            ),
        ).model_dump(),
    )
    overview: QuoteSectionOverviewDTO = pydantic.Field(
        json_schema_extra=QuoteSectionMetadataDTO(
            xpath=(
                "html/body/c-wiz[3]/div[1]/div[1]/div[1]/div[2]/div[2]/"
                "div[1]/div[1]/c-wiz[1]/div[1]/span[1]/div[1]/div[1]//"
                "div[2]/span[1]/div[1]/div[1]/div[1]/c-wiz[1]/div[1]/"
                "div[1]"
            ),
        ).model_dump(),
    )
