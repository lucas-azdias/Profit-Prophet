# Copyright (C) 2026 Lucas Dias

"""Google Finance quote scraper.

This module provides an asynchronous scraper responsible for retrieving and
parsing quote data from Google Finance. The scraper navigates to a quote page,
extracts structured information from predefined sections, and converts the
raw page content into strongly typed DTO models.
"""

import datetime
import decimal
import re
import typing
import unicodedata

import playwright.async_api

from src.scrapers.google_finance.dtos.quote_dto import (
    QuoteDTO,
    QuoteSectionMetadataDTO,
)
from src.scrapers.google_finance.dtos.quote_section_dto import (
    QuoteSectionDTO,
    QuoteSectionFieldMetadataDTO,
    QuoteSectionFieldSearchMethods,
)

if typing.TYPE_CHECKING:
    import types


class Scraper:
    """Asynchronous Google Finance quote scraper.

    This scraper uses Playwright to load Google Finance quote pages and
    extract financial data into structured DTOs. Instances may be managed
    manually through :meth:`start` and :meth:`close` or used as an
    asynchronous context manager.

    Attributes:
        BASE_URL (Literal):
            Base Google Finance URL used to construct quote page requests.

    """

    BASE_URL: typing.ClassVar = "https://www.google.com/finance/beta/quote"

    def __init__(
        self,
        page: playwright.async_api.Page | None = None,
        *,
        channel: str = "chromium",
    ) -> None:
        """Initialize a Google Finance scraper instance.

        The scraper can either operate on an existing Playwright page or create
        and manage its own browser resources when started. If no page is
        provided, a browser instance will be launched during
        :meth:`start`.

        Args:
            page (playwright.async_api.Page | None):
                Existing Playwright page to use for scraping operations. When
                omitted, the scraper creates a new browser and page when started.

            channel (str):
                Browser channel used when launching Playwright-managed browser
                instances. Defaults to `"chromium"`.

        """
        self.__page = page
        self.__channel = channel

        self.__playwright: playwright.async_api.Playwright | None = None
        self.__browser: playwright.async_api.Browser | None = None

    async def start(self) -> None:
        """Start the scraper and initialize browser resources.

        Creates a Playwright instance, launches a browser, and opens a new page
        for scraping operations.

        Raises:
            RuntimeError:
                If the scraper has already been started.

        """
        if self.__page is not None:
            msg = "'GoogleFinanceScraper' has already been started"
            raise RuntimeError(msg)

        self.__playwright = await playwright.async_api.async_playwright().start()

        self.__browser = await self.__playwright.chromium.launch(
            headless=True,
            channel=self.__channel,
        )

        self.__page = await self.__browser.new_page()

    async def close(self) -> None:
        """Release all browser resources associated with the scraper.

        Closes the browser, stops Playwright and resets the scraper state.
        """
        if self.__browser:
            await self.__browser.close()

        if self.__playwright:
            await self.__playwright.stop()

        self.__page = None
        self.__browser = None
        self.__playwright = None

    async def __aenter__(self) -> typing.Self:
        """Start the scraper when entering an asynchronous context.

        Returns:
            Scraper:
                The initialized scraper instance.

        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        """Close the scraper when leaving an asynchronous context.

        Args:
            exc_type (type[BaseException] | None):
                Type of the exception raised within the context block, if any.

            exc (BaseException | None):
                Exception instance raised within the context block, if any.

            tb (types.TracebackType | None):
                Traceback associated with the raised exception, if any.

        """
        await self.close()

    async def scrape_quote(self, ticker: str) -> QuoteDTO:
        """Retrieve and parse quote information for a ticker symbol.

        Loads the corresponding Google Finance page, extracts all configured
        quote sections, converts field values into their declared types, and
        returns a fully populated quote DTO.

        Args:
            ticker (str):
                Financial instrument ticker symbol to scrape.

        Returns:
            Structured quote data for the requested ticker.

        Raises:
            TypeError:
                If the quote model or one of its section models contains invalid
                metadata or unsupported field types.

        """
        # Loads ticker URL
        await self.__started_page.goto(
            f"{self.BASE_URL}/{ticker}?hl=en",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        # Waits for page to load completly with a manually selected event
        await self.__started_page.wait_for_event(
            "response",
            predicate=lambda response: response.url.endswith("/part_00000000.ts") and response.ok,
            timeout=10000,
        )

        # All quote's sections filled with data
        quote_data: dict[str, QuoteSectionDTO] = {}

        # Ticker field name inside quote class
        ticker_name = "ticker"

        # Builds all sections
        for section_name, section_field in QuoteDTO.model_fields.items():
            # Skips ticker field
            if section_name == ticker_name:
                continue

            # Validates if annotation indicates a quote section
            if section_field.annotation is None or not issubclass(
                section_field.annotation,
                QuoteSectionDTO,
            ):
                msg = (
                    f"Field '{section_name}' must be a '{QuoteSectionDTO.__name__}' "
                    f"subclass, got {section_field.annotation!r}"
                )
                raise TypeError(msg)

            # Retrieves XPath from section's metadata
            xpath = QuoteSectionMetadataDTO.model_validate(section_field.json_schema_extra).xpath

            # Builds section based on its fields' metadata
            section = await self.__build_section(section_field.annotation, xpath)

            # Stores section
            quote_data[section_name] = section

        # Returns compiled quote
        return QuoteDTO.model_validate({**quote_data, ticker_name: ticker})

    @property
    def __started_page(self) -> playwright.async_api.Page:
        if self.__page is None:
            msg = "'GoogleFinanceScraper' has not been started"
            raise RuntimeError(msg)

        return self.__page

    async def __build_section(
        self,
        section_type: type[QuoteSectionDTO],
        xpath: str,
    ) -> QuoteSectionDTO:
        # All section's fields filled with data
        section_data: dict[str, typing.Any] = {}

        # Rebuilds the section model to solve imports (aka. `ForwardRef`)
        section_type.model_rebuild(_types_namespace=globals(), raise_errors=False)

        # Builds all section's data based on its metadata
        for field_name, field in section_type.model_fields.items():
            # Goes to section's XPath
            container = self.__started_page.locator(f"xpath={xpath}")

            # Safely extract inner types from generic unions
            field_args: tuple[type[typing.Any], ...] = typing.get_args(field.annotation)

            # If no non-None types were found, then get the entire annotation
            field_type = (
                next((t for t in field_args if t is not type(None)), None) or field.annotation
            )

            # If no non-None types were found at all, then raises exception
            if field_type is None:
                msg = (
                    f"Field '{field_name}' in model '{section_type.__name__}' "
                    f"has an unresolvable type annotation: '{field.annotation}'. "
                    f"Ensure the field provides at least one concrete runtime type."
                )
                raise TypeError(msg)

            # Gets validated metadata
            field_metadata = QuoteSectionFieldMetadataDTO.model_validate(
                field.json_schema_extra,
            )

            field_data_text: str | None = None

            # Executes the selected search method for this field
            match field_metadata.search_method:
                case QuoteSectionFieldSearchMethods.XPATH:
                    # Goes to section's XPath and retrieve data
                    field_data_text = await container.locator(
                        f"xpath={field_metadata.label}",
                    ).text_content()

                case QuoteSectionFieldSearchMethods.SPLIT_LINES:
                    # Gets inner text and converts to lines
                    inner_text = await container.inner_text()
                    lines = [line for line in inner_text.splitlines() if line]

                    for i in range(len(lines) - 1):
                        # Grabs the next line if label is matched
                        if lines[i] == field_metadata.label:
                            field_data_text = lines[i + 1].strip()
                            break

            # No data was found for this field
            if field_data_text is None:
                section_data[field_name] = None
                continue

            # Normalizes data and removes invalid characters
            field_data_text = unicodedata.normalize("NFKC", field_data_text).strip()

            # Applies regex into data if a pattern is defined in the metadata
            if field_metadata.regex_pattern is not None:
                match = re.search(field_metadata.regex_pattern, field_data_text)

                # Couldn't match any data for this field
                if not match:
                    section_data[field_name] = None
                    continue

                matched_result: list[str]

                # If no custom ordering was requested, then use the entire regex match
                if field_metadata.regex_order is None:
                    matched_result = [match.group()]

                # Specific group ordering was requested
                else:
                    # All matched named groups
                    groups_dict = match.groupdict()

                    # Extract matched chunks in the specified order
                    matched_result = [
                        groups_dict[group_name] or ""
                        for group_name in field_metadata.regex_order
                        if group_name in groups_dict
                    ]

                # Executes the post regex script
                matched_result = list(field_metadata.post_regex(matched_result))

                # Join chunks using the designated separator
                field_data_text = field_metadata.separator.join(matched_result)

            # Parsed field data
            field_data: typing.Any | None = None

            # Parses field data based on expected type
            if field_type is str:
                field_data = field_data_text

            elif field_type is decimal.Decimal:
                # Checks if value is a percentage value (e.g. "10.0%")
                is_percentage = "%" in field_data_text

                # Removes thousands marker
                value = field_data_text.replace(",", "")

                # Multiplier for value based on suffix symbol
                multiplier = decimal.Decimal("1.0")

                # All multiplier symbols and their values
                multiplier_suffixes = {
                    "K": decimal.Decimal(1_000),
                    "M": decimal.Decimal(1_000_000),
                    "B": decimal.Decimal(1_000_000_000),
                    "T": decimal.Decimal(1_000_000_000_000),
                }

                # Matches any multiplier suffix symbol
                match = re.search(
                    f"([{''.join(multiplier_suffixes.keys())}])$",
                    value,
                    re.IGNORECASE,
                )

                # Updates multiplier and removes it from the value
                if match:
                    multiplier = multiplier_suffixes[match.group(1).upper()]
                    value = value[:-1]

                # Filters characters inside the value
                value = re.sub(r"[^0-9.\-+]", "", value)

                # Parses the value
                if value:
                    try:
                        result = decimal.Decimal(value)
                    except ValueError, TypeError:
                        pass
                    else:
                        # Applies multiplier and percentage adjustment
                        result *= multiplier
                        if is_percentage:
                            result /= decimal.Decimal("100.0")
                        field_data = result

            elif field_type is datetime.datetime:
                field_data = datetime.datetime.fromisoformat(field_data_text)

            elif field_type is datetime.date:
                field_data = datetime.date.fromisoformat(field_data_text)

            else:
                # Unsupported type inside the section model
                msg = (
                    f"Unsupported parsing type "
                    f"'{getattr(field_type, '__name__', str(field_type))}' encountered for "
                    f"field '{field_name}' in model '{section_type.__name__}'. Could "
                    f"not convert raw string value: {field_data_text!r}."
                )
                raise TypeError(msg)

            section_data[field_name] = field_data

        return section_type.model_validate(section_data)
