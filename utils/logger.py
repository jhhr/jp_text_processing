"""
The package logs through the standard `logging` module, under one logger named
`jp_text_processing`. Library code never prints: the logger starts with a `NullHandler`, so
whoever embeds the package decides where its lines go by adding handlers to `package_logger`
and setting its level. `console_logging` is that decision made for the suites and scripts.
"""

import logging
import sys
from typing import Literal, Optional, Protocol, TextIO, Union

LOGGER_NAME = "jp_text_processing"

package_logger = logging.getLogger(LOGGER_NAME)
package_logger.addHandler(logging.NullHandler())

# Discards everything, for probes whose failures are expected and not worth a line.
silent_logger = logging.getLogger(f"{LOGGER_NAME}.silent")
silent_logger.disabled = True

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
    level: Union[LogLevel, int] = "error", stream: Optional[TextIO] = None
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


def set_level(level: Union[LogLevel, int]) -> None:
    package_logger.setLevel(LOG_LEVELS[level] if isinstance(level, str) else level)


class LegacyLogger(Protocol):
    """
    The hand-rolled logger the add-ons still pass in (`anki_shared/utils/logger.py`): a level
    name plus one method per level taking the finished message.
    """

    level: LogLevel

    def error(self, message: str) -> None: ...

    def warning(self, message: str) -> None: ...

    def info(self, message: str) -> None: ...

    def debug(self, message: str) -> None: ...


class _LegacyLoggerHandler(logging.Handler):
    """Hands each record to the legacy logger's method for its level, prefix and colour included."""

    def __init__(self, legacy: LegacyLogger):
        super().__init__()
        self.legacy = legacy

    def emit(self, record: logging.LogRecord) -> None:
        method = getattr(self.legacy, record.levelname.lower(), self.legacy.error)
        method(self.format(record))


def as_logger(logger: Union[logging.Logger, LegacyLogger, None]) -> logging.Logger:
    """
    The `logging.Logger` the package works with, from whatever a caller handed in.

    `None` is the package logger. A legacy hand-rolled logger is wrapped in a standalone
    `logging.Logger` that filters at its level and delivers through its own methods, so the
    caller's sink and prefixes keep working unchanged.
    """
    if logger is None:
        return package_logger
    if isinstance(logger, logging.Logger):
        return logger
    adapted = logging.Logger(f"{LOGGER_NAME}.legacy", LOG_LEVELS[logger.level])
    adapted.propagate = False
    adapted.addHandler(_LegacyLoggerHandler(logger))
    return adapted
