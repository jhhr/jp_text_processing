"""
The package logs through the standard `logging` module, under one logger named
`jp_text_processing`. Library code never prints: the logger starts with a `NullHandler`, so
whoever embeds the package decides where its lines go by adding handlers to `package_logger`
and setting its level. `console_logging` is that decision made for the suites and scripts.

There is only the one logger, so nothing is threaded through call signatures: a module that
logs takes it as `from ..utils.logger import package_logger as logger` and calls it directly.
"""

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Literal, TextIO

LOGGER_NAME = "jp_text_processing"

package_logger = logging.getLogger(LOGGER_NAME)
package_logger.addHandler(logging.NullHandler())

LogLevel = Literal["error", "warning", "info", "debug"]

LOG_LEVELS: dict[LogLevel, int] = {
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
GREEN = "\033[32m"
RESET = "\033[0m"

LEVEL_COLOURS = {
    logging.ERROR: RED,
    logging.WARNING: YELLOW,
    logging.INFO: BLUE,
    logging.DEBUG: GREEN,
}


class ColourFormatter(logging.Formatter):
    """`[LEVEL] message` with the level coloured - the line the suites have always printed."""

    def format(self, record: logging.LogRecord) -> str:
        colour = LEVEL_COLOURS.get(record.levelno, "")
        return f"{colour}[{record.levelname}]{RESET} {super().format(record)}"


class _ConsoleHandler(logging.StreamHandler):
    """The handler `console_logging` owns, so calling it again replaces rather than stacks."""


def console_logging(
    level: LogLevel | int = "error", stream: TextIO | None = None
) -> None:
    """
    Send the package's logging to `stream` (stdout as of the call) at `level`, replacing any
    earlier console handler.

    For the suites and scripts. An application embedding the package adds its own handlers to
    `package_logger` instead.
    """
    for handler in list(package_logger.handlers):
        if isinstance(handler, _ConsoleHandler):
            package_logger.removeHandler(handler)
    handler = _ConsoleHandler(sys.stdout if stream is None else stream)
    handler.setFormatter(ColourFormatter())
    package_logger.addHandler(handler)
    set_level(level)


def set_level(level: LogLevel | int) -> None:
    package_logger.setLevel(LOG_LEVELS[level] if isinstance(level, str) else level)


@contextmanager
def silenced() -> Iterator[None]:
    """
    Drop everything the package logs for the duration of the block.

    For probes whose failures are expected and not worth a line: the caller asked a question the
    package answers by trying an alignment that may well not exist, and its complaints about the
    attempt are not the caller's business.
    """
    was_disabled = package_logger.disabled
    package_logger.disabled = True
    try:
        yield
    finally:
        package_logger.disabled = was_disabled
