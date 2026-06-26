# Copyright (C) 2026 Lucas Dias

"""Playwright browser engine manager.

This module provides `BrowserEngine`, a thin wrapper around Playwright
responsible for managing the lifecycle of a browser instance.

The engine owns both the Playwright runtime and the launched browser,
providing methods to start and stop the browser and create isolated
browser contexts for consumers.
"""

import typing

import playwright.async_api

if typing.TYPE_CHECKING:
    from src.inout.logger import Logger


class BrowserEngine:
    """Manage the lifecycle of a Playwright browser instance.

    The engine must be launched before creating contexts. Resources are
    released through `BrowserEngine.dispatch`.

    """

    def __init__(self, logger: Logger) -> None:
        """Initialize a browser engine.

        Args:
            logger (Logger):
                Logger used to record browser lifecycle events.

        """
        self.__logger = logger
        self.__playwright: playwright.async_api.Playwright | None = None
        self.__browser: playwright.async_api.Browser | None = None

    async def launch(
        self,
        *,
        channel: str = "chromium",
        headless: bool = True,
    ) -> None:
        """Launch the Playwright browser.

        Starts the Playwright runtime and launches a Chromium browser
        instance.

        Args:
            channel (str):
                Browser channel to launch.

            headless (bool):
                Whether the browser should run without a visible UI.

        Raises:
            RuntimeError:
                If the browser engine has already been launched.

        """
        if self.__browser is not None:
            msg = "Browser has already been launched"
            raise RuntimeError(msg)

        self.__playwright = await playwright.async_api.async_playwright().start()

        self.__browser = await self.__playwright.chromium.launch(
            channel=channel,
            headless=headless,
        )

        self.__logger.log("Browser engine has been launched")

    async def dispatch(self) -> None:
        """Release all resources owned by the browser engine.

        Closes the browser instance, stops the Playwright runtime, and
        resets the engine state.
        """
        if self.__browser is not None:
            await self.__browser.close()
            self.__browser = None

        if self.__playwright is not None:
            await self.__playwright.stop()
            self.__playwright = None

        self.__logger.log("Browser engine has been dispatched")

    async def new_context(
        self,
    ) -> playwright.async_api.BrowserContext:
        """Create a new isolated browser context.

        Returns:
            BrowserContext:
                Newly created browser context.

        Raises:
            RuntimeError:
                If the browser engine has not been launched.

        """
        if self.__browser is None:
            msg = "Browser is not launched"
            raise RuntimeError(msg)

        # Returns a new browser context
        return await self.__browser.new_context()
