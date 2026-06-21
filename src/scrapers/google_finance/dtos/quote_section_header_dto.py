# Copyright (C) 2026 Lucas Dias

"""Google Finance quote header data transfer object.

This module defines :class:`QuoteSectionHeaderDTO`, a Pydantic-based
data model representing the high-level "header" section of a Google
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
    import collections.abc
    import decimal


class QuoteSectionHeaderDTO(QuoteSectionDTO):
    """High-level quote header information.

    Attributes:
        company (str | None):
            Company or instrument name.

        price (decimal.Decimal | None):
            Current quoted price.

        change_value (decimal.Decimal | None):
            Absolute price change for the current session.

        change_percent (decimal.Decimal | None):
            Relative price change as a decimal fraction.

        status (str | None):
            Current market status (e.g. open, closed, pre-market).

        last_updated (datetime.datetime | None):
            Timestamp reported by Google Finance, normalized to ISO datetime.

        currency (str | None):
            Quote currency (e.g. USD, EUR, BRL).

    """

    @staticmethod
    def __parse_extracted_last_updated(
        x: collections.abc.Sequence[str],
    ) -> collections.abc.Sequence[str]:
        # Unpack the extracted date/time components
        year, month, day, time_str, raw_tz = x

        # Parse the timezone offset and normalize it into integer hour/minute
        hours_str, _, minutes_str = raw_tz[1:].partition(":")
        minutes_str = minutes_str or "00"

        hours = int(hours_str)
        minutes = int(minutes_str)

        # Create a timezone object representing the extracted UTC offset
        multiplier = -1 if raw_tz.startswith("-") else 1
        tzinfo = datetime.timezone(multiplier * datetime.timedelta(hours=hours, minutes=minutes))

        # Gets given year or current year based on timezone
        year = year or str(datetime.datetime.now(tzinfo).year)

        return [
            datetime.datetime.strptime(
                f"{year} {month} {day} {time_str} {raw_tz[0]}{hours:02d}{minutes:02d}",
                "%Y %b %d %I:%M:%S %p %z",
            ).isoformat(),
        ]

    company: str | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[1]/div[1]",
        ).model_dump(),
    )

    price: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[1]/div[1]/span[1]/span[1]",
        ).model_dump(),
    )
    change_value: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[1]/div[2]/div[2]/span[1]/span[1]/span[1]/span[1]",
        ).model_dump(),
    )
    change_percent: decimal.Decimal | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[1]/div[2]/span[1]/span[1]",
        ).model_dump(),
    )

    status: str | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[2]",
            regex_pattern=re.compile(
                r"^\b(?P<status>Closed|Pre-market|After-hours|Market open|Open)\b[:]?[\s]*",
                re.IGNORECASE,
            ),
            regex_order=("status",),
            post_regex=lambda x: (x[0] or "Open").lower(),
        ).model_dump(),
    )
    last_updated: datetime.datetime | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[2]",
            regex_pattern=re.compile(
                r"\b(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})(?P<year>,\s+\d{4})?,\s+"
                r"(?P<time>\d{1,2}:\d{2}:\d{2}\s+[AP]M)\s+"
                r"(?:UTC|GMT)(?P<timezone>[+-]\d{1,2}(?::\d{2})?)\b",
                re.IGNORECASE,
            ),
            regex_order=("year", "month", "day", "time", "timezone"),
            post_regex=__parse_extracted_last_updated,
        ).model_dump(),
    )
    currency: str | None = pydantic.Field(
        default=None,
        json_schema_extra=QuoteSectionFieldMetadataDTO(
            search_method=QuoteSectionFieldSearchMethods.XPATH,
            label="./div[2]/div[1]/div[2]",
            regex_pattern=re.compile(
                r"\b([A-Z]{3})\b$",
                re.IGNORECASE,
            ),
            post_regex=lambda x: x[0].lower(),
        ).model_dump(),
    )
