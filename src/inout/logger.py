# Copyright (C) 2026 Lucas Dias

"""Logging module.

This module provides a centralized logging interface used throughout the
application. It is responsible for creating timestamped log files and recording
runtime events.
"""

import datetime
import logging
import pathlib
import typing


class Logger:
    """Application logging service.

    This class wraps Python's built-in logging framework and provides a
    simplified interface for recording any event. Log entries are written
    to a timestamped file.

    The logger is intended to be shared across all application components to
    provide consistent runtime diagnostics and execution tracking.
    """

    def __init__(self, logs_path: pathlib.Path) -> None:
        """Initialize the logging service.

        Creates a timestamped log file, configures the logging subsystem, and
        records startup information for the current application run.

        Args:
            logs_path (pathlib.Path):
                Directory where log files should be created.

        """
        self.__logs_path = logs_path

        # Guarantees the logs folder exists
        self.__logs_path.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=self.__generate_log_path(),
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] <%(name)s> %(message)s",
            force=True,
        )

        self.__logger = logging.getLogger()

        # Default message in log file
        self.log(f"=== Runtime started: {datetime.datetime.now().astimezone().isoformat()} ===")
        self.log(f"=== Log file: {self.__logs_path} ===")

    def log(
        self,
        msg: str,
        msg_type: typing.Literal["info", "debug", "warning", "error"] = "info",
    ) -> None:
        """Record a message in the log file.

        The message is written using the logging level specified by
        :param:`msg_type`. Optionally, the message may also be displayed
        through the application's console interface.

        Args:
            msg (str):
                Message to record.

            msg_type (Literal["info", "debug", "warning", "error"]):
                Logging severity level.

        """
        log_msg = msg.strip()

        match msg_type:
            case "info":
                self.__logger.info(log_msg)
            case "debug":
                self.__logger.debug(log_msg)
            case "warning":
                self.__logger.warning(log_msg)
            case "error":
                self.__logger.error(log_msg)

    def __generate_log_path(self) -> pathlib.Path:
        return pathlib.Path(self.__logs_path) / f"log_{datetime.datetime.now().astimezone():%Y-%m-%d_%H-%M-%S}.log"
