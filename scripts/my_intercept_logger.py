#!/usr/bin/env python3
"""
Thread-safe loguru logging setup with early initialization support.

Usage:
    # In your main application:
    from my_intercept_logger import _early_init
    _early_init()  # Call FIRST, before other imports

    # Import other modules...
    import discord, asyncio, etc

    # Then configure full logging
    from my_intercept_logger import global_log_config
    global_log_config()
"""
# pylint: disable=no-member
# pylint: disable=consider-using-tuple
# pyright: ignore[reportOperatorIssue]
# pyright: ignore[reportOptionalIterable]
# SOURCE: https://betterstack.com/community/guides/logging/loguru/

from __future__ import annotations

import contextvars
import functools
import gc
import inspect
import logging
import os
import re
import sys
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from logging import Logger, LogRecord
from pathlib import Path
from pprint import pformat
from sys import stdout
from time import process_time
from types import FrameType
from typing import TYPE_CHECKING, Any, ClassVar, Deque, Dict, ForwardRef, List, Literal, Optional, Union, cast

import loguru
from loguru import logger
from loguru._defaults import LOGURU_FORMAT
from pydantic import BaseModel

# # LoggerModel = ForwardRef("LoggerModel")  # Commented out - requires pydantic

# # Simplified data classes for testing without pydantic dependency

# @dataclass
# class LoggerPatch:
#     name: str
#     level: str

# @dataclass
# class LoggerModel:
#     name: str
#     level: int | None = None
#     children: list[Any] | None = None

# # LoggerModel.update_forward_refs()  # Not needed for dataclasses

class LoggerPatch(BaseModel):
    name: str
    level: str


class LoggerModel(BaseModel):
    name: str
    level: int | None
    # children: Optional[List["LoggerModel"]] = None
    # fixes: https://github.com/samuelcolvin/pydantic/issues/545
    children: list[Any] | None = None
    # children: ListLoggerModel = None


LoggerModel.update_forward_refs()


if TYPE_CHECKING:
    from better_exceptions.log import BetExcLogger
    from loguru._logger import Logger as _Logger


LOGLEVEL_MAPPING = {
    50: "CRITICAL",
    40: "ERROR",
    30: "WARNING",
    20: "INFO",
    10: "DEBUG",
    0: "NOTSET",
}

LOGURU_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level}</level> | "
    "<cyan>{module}</cyan>:<cyan>{line}</cyan> | "
    "<level>{extra[room_id]}</level> - "
    "<level>{message}</level>"
)

LOGURU_FILE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{extra[room_id]}</level> - "
    "<level>{message}</level>"
)

# NOTE: this is the default format for loguru
_LOGURU_FORMAT = (
    "LOGURU_FORMAT",
    str,
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# NOTE: this is the new format for loguru
NEW_LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<magenta>{file}:{line}</magenta> | "
    "<level>{message}</level> | {extra}"
)


LOG_LEVEL = Literal[
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


# TqdmOutputStream commented out - requires tqdm dependency
# class TqdmOutputStream:
#     def write(self, string: str = "") -> None:
#         tqdm.write(string, file=sys.stderr, end="")
#
#     def isatty(self) -> bool:
#         return sys.stderr.isatty()


_console_handler_id: int | None = None
_file_handler_id: int | None = None

_old_log_dir: str | None = None
_old_console_log_level: LOG_LEVEL | None = None
_old_backup_count: int | None = None

# Track early init state
_early_init_done = False
_early_init_lock = threading.Lock()


def _early_init() -> None:
    """
    Early initialization of logging system - call BEFORE importing other modules.

    This ensures all logging calls are intercepted from the start and prevents
    race conditions with threaded imports or configuration conflicts.

    Thread-safe: Uses a lock to prevent race conditions when called from multiple threads.
    """
    global _early_init_done

    # Quick check without lock for performance
    if _early_init_done:
        return

    # Thread-safe double-checked locking pattern
    with _early_init_lock:
        if _early_init_done:  # Re-check inside lock
            return  # Another thread already initialized

        # Remove default loguru handler immediately
        logger.remove()

        # Create thread-safe InterceptHandler early
        intercept_handler = InterceptHandler()

        # Set up basic root logging level
        logging.root.setLevel(logging.DEBUG)

        # Replace root handler immediately
        logging.root.handlers = [intercept_handler]

        # Configure basic loguru handler with safety features
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            enqueue=True,   # Critical for thread/multiprocessing safety
            catch=True,     # Prevent logging errors from crashing app
            backtrace=True,
            diagnose=True
        )

        # Immediately intercept common problematic loggers
        critical_loggers = [
            "asyncio",
            "concurrent.futures",
            "multiprocessing",
            "threading",
            "urllib3",
            "requests",
            "httpx",
            "aiohttp",
            "discord",
            "discord.client",
            "discord.gateway",
            "discord.http"
        ]

        for logger_name in critical_loggers:
            log_instance = logging.getLogger(logger_name)
            log_instance.handlers = [intercept_handler]
            log_instance.propagate = False

        # Mark as completed inside the lock
        _early_init_done = True
        logger.debug("Early logging initialization completed")


# REQUEST_ID_CONTEXTVAR = contextvars.ContextVar("request_id", default=None)

# # initialize the context variable with a default value
# REQUEST_ID_CONTEXTVAR.set("notset")


def set_log_extras(record: dict[str, Any]) -> None:
    """Set extra log fields in the log record.

    Args:
        record: The log record to modify.
    """
    record["extra"]["datetime"] = datetime.now(UTC)


# SOURCE: https://github.com/joint-online-judge/fastapi-rest-framework/blob/b0e93f0c0085597fcea4bb79606b653422f16700/fastapi_rest_framework/logging.py#L43
def format_record(record: dict[str, Any]) -> str:
    """Custom format for loguru loggers.

    Uses pformat for log any data like request/response body during debug.
    Works with logging if loguru handler it.

    Args:
        record: The log record.

    Returns:
        The formatted log record.
    """
    # """
    # Custom format for loguru loggers.
    # Uses pformat for log any data like request/response body during debug.
    # Works with logging if loguru handler it.

    # Example:
    # -------
    # >>> payload = [{"users":[{"name": "Nick", "age": 87, "is_active": True},
    # >>>     {"name": "Alex", "age": 27, "is_active": True}], "count": 2}]
    # >>> logger.bind(payload=).debug("users payload")
    # >>> [   {   'count': 2,
    # >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
    # >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]

    # """
    format_string = NEW_LOGGER_FORMAT
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


class InterceptHandler(logging.Handler):
    """
    Thread-safe and async-safe interceptor for standard logging into Loguru.

    This implementation ensures proper thread safety and multiprocessing compatibility
    by using improved frame inspection and avoiding potential deadlocks.
    See: https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
    """

    loglevel_mapping: ClassVar[dict[int, str]] = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.FATAL: "FATAL",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
        1: "DUMMY",
        0: "NOTSET",
    }

    def emit(self, record: logging.LogRecord) -> None:
        """Thread-safe emit method that properly handles frame inspection."""
        # Get corresponding Loguru level if it exists
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Improved frame inspection to avoid issues with frozen imports and threading
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            # Check for logging module and frozen/bootstrap code
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        # Use opt() with proper depth and exception info for thread-safe logging
        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def get_logger(
    name: str,
    provider: str | None = None,
    level: int = logging.INFO,
    logger: logging.Logger = logger,
) -> logging.Logger:
    return logger


# def request_id_filter(record: dict[str, Any]):
#     """
#     Inject the request id from the context var to the log record. The logging
#     config format is defined in logger_config.yaml and has request_id as a field.
#     """
#     record["extra"]["request_id"] = REQUEST_ID_CONTEXTVAR.get()


def reset_logging(
    log_dir: str, *, console_log_level: LOG_LEVEL = "INFO", backup_count: int | None = None
) -> None:
    """Reset logging configuration with thread and multiprocessing safety.

    Args:
        log_dir: Directory for log files
        console_log_level: Level for console output
        backup_count: Number of backup files to retain
    """
    global _console_handler_id, _file_handler_id
    global _old_log_dir, _old_console_log_level, _old_backup_count

    # Configure with thread-safe extra context
    logger.configure(extra={"room_id": ""})

    if console_log_level != _old_console_log_level:
        if _console_handler_id is not None:
            logger.remove(_console_handler_id)
        else:
            logger.remove()  # remove the default stderr handler

        # Add console handler with thread/multiprocessing safety
        _console_handler_id = logger.add(
            sys.stderr,
            level=console_log_level,
            format=LOGURU_CONSOLE_FORMAT,
            enqueue=True,  # Enable for thread safety
            catch=True     # Prevent crashes from logging errors
        )

        _old_console_log_level = console_log_level


def global_log_config(log_level: str | int = logging.DEBUG, json: bool = False) -> _Logger:
    """Configure global logging settings with thread and async safety.

    This function sets up thread-safe and multiprocessing-safe logging by:
    - Using enqueue=True for non-blocking, process-safe logging
    - Configuring proper exception handling with catch=True
    - Setting up InterceptHandler for standard logging integration
    - Ensuring all handlers are replaced consistently

    Args:
        log_level: The log level to use. Defaults to logging.DEBUG.
        json: Whether to format logs as JSON. Defaults to False.

    Returns:
        The configured logger instance.
    """

    global _console_handler_id, _file_handler_id
    global _old_log_dir, _old_console_log_level, _old_backup_count

    if isinstance(log_level, str) and (log_level in logging._nameToLevel):
        log_level = logging.DEBUG

    # Create thread-safe intercept handler
    intercept_handler = InterceptHandler()

    # Set root logging level
    logging.root.setLevel(log_level)

    # Replace handlers for all existing loggers to ensure consistency
    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),  # pylint: disable=no-member
        "asyncio",
        "discord",
        "discord.client",
        "discord.gateway",
        "discord.http",
        "chromadb",
        "langchain_chroma",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            # Replace handlers with our thread-safe interceptor
            log_instance = logging.getLogger(name)
            log_instance.handlers = [intercept_handler]
            # Prevent propagation to avoid duplicate logs
            log_instance.propagate = False

    # Configure loguru with thread/async/multiprocessing safety
    logger.configure(
        handlers=[
            {
                # Use stdout as sink for console output
                "sink": stdout,
                # Don't serialize to JSON by default (can be overridden)
                "serialize": json,
                # Use custom format function for structured logging
                "format": format_record,
                # Enable diagnosis for better debugging (disable in production)
                "diagnose": True,
                # Show full backtrace for comprehensive error tracking
                "backtrace": True,
                # CRITICAL: Enable enqueue for thread/multiprocessing safety
                "enqueue": True,
                # Catch exceptions to prevent app crashes from logging errors
                "catch": True,
            }
        ],
        # Add extra context if needed
        # extra={"request_id": REQUEST_ID_CONTEXTVAR.get()},
    )
    # Apply log extras patcher if needed
    # logger.configure(patcher=set_log_extras)

    # Optionally disable specific loggers
    # logger.disable("sentry_sdk")

    print(f"Thread-safe logger configured with level: {log_level}")

    # Set up framework-specific loggers with thread safety
    setup_uvicorn_logger()
    setup_gunicorn_logger()

    return logger


def setup_uvicorn_logger():
    """Configure uvicorn loggers to use thread-safe InterceptHandler."""
    intercept_handler = InterceptHandler()

    # Clear existing handlers and set up interception
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.")
    )
    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = False

    # Set up main uvicorn logger with thread-safe handler
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = [intercept_handler]
    uvicorn_logger.propagate = False


def setup_gunicorn_logger():
    """Configure gunicorn loggers to use thread-safe InterceptHandler."""
    intercept_handler = InterceptHandler()

    # Set up gunicorn error logger
    error_logger = logging.getLogger("gunicorn.error")
    error_logger.handlers = [intercept_handler]
    error_logger.propagate = False

    # Set up gunicorn access logger
    access_logger = logging.getLogger("gunicorn.access")
    access_logger.handlers = [intercept_handler]
    access_logger.propagate = False


def get_lm_from_tree(loggertree: LoggerModel, find_me: str) -> LoggerModel | None:
    """Recursively search for a logger model in the logger tree.

    Args:
        loggertree: The root logger model to search from.
        find_me: The name of the logger model to find.

    Returns:
        The found logger model, or None if not found.
    """
    if find_me == loggertree.name:
        print("Found")
        return loggertree
    else:
        for ch in loggertree.children:
            print(f"Looking in: {ch.name}")
            if i := get_lm_from_tree(ch, find_me):
                return i
    return None


def generate_tree() -> LoggerModel:
    """Generate a tree of logger models.

    Returns:
        The root logger model of the generated tree.
    """
    rootm = LoggerModel(name="root", level=logging.getLogger().getEffectiveLevel(), children=[])
    nodesm: dict[str, LoggerModel] = {}
    items = sorted(logging.root.manager.loggerDict.items())  # type: ignore
    for name, loggeritem in items:
        if isinstance(loggeritem, logging.PlaceHolder):
            nodesm[name] = nodem = LoggerModel(name=name, children=[])
        else:
            nodesm[name] = nodem = LoggerModel(
                name=name, level=loggeritem.getEffectiveLevel(), children=[]
            )
        i = name.rfind(".", 0, len(name) - 1)
        parentm = rootm if i == -1 else nodesm[name[:i]]
        parentm.children.append(nodem)
    return rootm


def obfuscate_message(message: str) -> str:
    """Obfuscate sensitive information in a message.

    Args:
        message: The message to obfuscate.

    Returns:
        The obfuscated message.
    """
    obfuscation_patterns = [
        (r"email: .*", "email: ******"),
        (r"password: .*", "password: ******"),
        (r"newPassword: .*", "newPassword: ******"),
        (r"resetToken: .*", "resetToken: ******"),
        (r"authToken: .*", "authToken: ******"),
        (r"located at .*", "located at ******"),
        (r"#token=.*", "#token=******"),
    ]
    for pattern, replacement in obfuscation_patterns:
        message = re.sub(pattern, replacement, message)

    return message


def formatter(record: dict[str, Any]) -> str:
    """Format a log record.

    Args:
        record: The log record to format.

    Returns:
        The formatted log record.
    """
    record["extra"]["obfuscated_message"] = record["message"]
    return (
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> <level>[{level}]</level> - "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{extra[obfuscated_message]}</level>\n{exception}"
    )


def formatter_sensitive(record: dict[str, Any]) -> str:
    """Format a log record with sensitive information obfuscated.

    Args:
        record: The log record to format.

    Returns:
        The formatted log record with sensitive information obfuscated.
    """
    record["extra"]["obfuscated_message"] = obfuscate_message(record["message"])
    return (
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> <level>[{level}]</level> - "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{extra[obfuscated_message]}</level>\n{exception}"
    )


# SMOKE-TESTS
if __name__ == "__main__":
    # from logging_tree import printout  # Optional dependency

    global_log_config(
        log_level=logging.getLevelName("DEBUG"),
        json=False,
    )
    LOGGER = logger

    def dump_logger_tree():
        rootm = generate_tree()
        LOGGER.debug(rootm)

    def dump_logger(logger_name: str):
        LOGGER.debug(f"getting logger {logger_name}")
        rootm = generate_tree()
        return get_lm_from_tree(rootm, logger_name)

    LOGGER.info("TESTING TESTING 1-2-3")
    # printout()  # Requires logging_tree dependency

    # Test thread safety by logging from multiple threads
    import threading
    import time

    def test_thread_logging(thread_id: int):
        """Test logging from multiple threads."""
        for i in range(5):
            LOGGER.info(f"Thread {thread_id}: Message {i+1}")
            time.sleep(0.1)

    LOGGER.info("Testing thread safety...")
    threads = []
    for i in range(3):
        thread = threading.Thread(target=test_thread_logging, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    LOGGER.success("Thread safety test completed!")

    # Test exception handling
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        LOGGER.exception("Caught test exception:")

    LOGGER.info("All tests completed successfully!")
