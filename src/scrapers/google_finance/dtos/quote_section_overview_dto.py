# Copyright (C) 2026 Lucas Dias

"""Google Finance quote overview data transfer object.

This module defines :class:`QuoteSectionOverviewDTO`, a Pydantic-based
model representing the "overview" or "fundamentals" section of a Google
Finance quote page.
"""

import datetime
import re
import typing

import pydantic

from src.scrapers.google_finance.dtos.quote_section_dto import (
    QuoteSectionDTO,
    QuoteSectionFieldMetadataDTO,
    QuoteSectionFieldSearchMethods,
)

if typing.TYPE_CHECKING:
    import decimal


class QuoteSectionOverviewDTO(QuoteSectionDTO):
    """Quote overview section with fundamental and statistical market data.

    Attributes:
       open (decimal.Decimal | None):
           Session opening price.

       high (decimal.Decimal | None):
           Session high price.

       low (decimal.Decimal | None):
           Session low price.

       market_cap (decimal.Decimal | None):
           Market capitalization.

       avg_volume (decimal.Decimal | None):
           Average trading volume.

       volume (decimal.Decimal | None):
           Current trading volume.

       dividend (decimal.Decimal | None):
           Dividend yield as a decimal fraction.

       quarterly_dividend (decimal.Decimal | None):
           Quarterly dividend amount per share.

       ex_dividend_date (datetime.date | None):
           Ex-dividend date.

       pe_ratio (decimal.Decimal | None):
           Price-to-earnings ratio.

       eps (decimal.Decimal | None):
           Earnings per share.

       beta (decimal.Decimal | None):
           Beta coefficient.

       wk52_high (decimal.Decimal | None):
           52-week high price.

       wk52_low (decimal.Decimal | None):
           52-week low price.

       shares_outstanding (decimal.Decimal | None):
           Number of shares outstanding.

       employees (decimal.Decimal | None):
           Number of employees.

    """

    open: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Open",
        ).model_dump(),
    )
    high: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="High",
        ).model_dump(),
    )
    low: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Low",
        ).model_dump(),
    )
    market_cap: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Mkt. cap",
        ).model_dump(),
    )
    avg_volume: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Avg. vol.",
        ).model_dump(),
    )
    volume: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Volume",
        ).model_dump(),
    )
    dividend: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Dividend",
        ).model_dump(),
    )
    quarterly_dividend: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Quarterly dividend",
        ).model_dump(),
    )
    ex_dividend_date: datetime.date | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Ex-dividend date",
            regex_pattern=re.compile(
                r"(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})",
                re.IGNORECASE,
            ),
            regex_order=("month", "day", "year"),
            post_regex=lambda x: [datetime.date.strptime(" ".join(x), "%b %d %Y").isoformat()],
        ).model_dump(),
    )
    pe_ratio: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="P/E ratio",
        ).model_dump(),
    )
    eps: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="EPS",
        ).model_dump(),
    )
    beta: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Beta",
        ).model_dump(),
    )
    wk52_high: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="52-wk high",
        ).model_dump(),
    )
    wk52_low: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="52-wk low",
        ).model_dump(),
    )
    shares_outstanding: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="Shares outstanding",
        ).model_dump(),
    )
    employees: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.SPLIT_LINES,
            label="No. of employees",
        ).model_dump(),
    )
