"""
Thread-safe, async-safe, and multiprocessing-safe logging interceptor for boss-bot.

This module provides early initialization of logging system with proper thread safety
and standard library logging interception using Loguru. Critical for production
applications using threading, asyncio, multiprocessing, or frameworks like Discord.py.

Usage:
    # In your main application (FIRST - before other imports):
    from boss_bot.monitoring.logging.interceptor import early_init
    early_init()

    # Import other modules...
    import discord, asyncio, etc

    # Then configure full logging
    from boss_bot.monitoring.logging.interceptor import configure_thread_safe_logging
    configure_thread_safe_logging()
"""

from __future__ import annotations

import contextvars
import inspect
import logging
import re
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from pprint import pformat
from typing import Any, ClassVar

import loguru
from loguru import logger
from pydantic import BaseModel

# Global log level mapping
LOGLEVEL_MAPPING = {
    50: "CRITICAL",
    40: "ERROR",
    30: "WARNING",
    20: "INFO",
    10: "DEBUG",
    0: "NOTSET",
}

# Format constants for different use cases
LOGURU_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level}</level> | "
    "<cyan>{module}</cyan>:<cyan>{line}</cyan> | "
    "<level>{extra[room_id]}</level> - "
    "<level>{message}</level>"
)

NEW_LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<magenta>{file}:{line}</magenta> | "
    "<level>{message}</level> | {extra}"
)

# Context variable for request tracking
REQUEST_ID_CONTEXTVAR = contextvars.ContextVar("request_id", default="notset")

# Thread safety for early initialization
_early_init_done = False
_early_init_lock = threading.Lock()

# Handler tracking
_console_handler_id: int | None = None
_file_handler_id: int | None = None


def set_log_extras(record: dict[str, Any]) -> None:
    """Set extra log fields in the log record.

    Args:
        record: The log record to modify.
    """
    record["extra"]["datetime"] = datetime.now(UTC)


def request_id_filter(record: dict[str, Any]) -> None:
    """
    Inject the request id from the context var to the log record.
    """
    record["extra"]["request_id"] = REQUEST_ID_CONTEXTVAR.get()


def format_record(record: dict[str, Any]) -> str:
    """Custom format for loguru loggers.

    Uses pformat for log any data like request/response body during debug.
    Works with logging if loguru handler it.

    Args:
        record: The log record.

    Returns:
        The formatted log record.

    Example:
    -------
    >>> payload = [{"users":[{"name": "Nick", "age": 87, "is_active": True},
    >>>     {"name": "Alex", "age": 27, "is_active": True}], "count": 2}]
    >>> logger.bind(payload=payload).debug("users payload")
    >>> [   {   'count': 2,
    >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
    >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]
    """
    format_string = NEW_LOGGER_FORMAT
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(record["extra"]["payload"], indent=4, compact=True, width=88)
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


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
        (r"Bearer [A-Za-z0-9\-_]+", "Bearer ******"),
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9\-_]+", "api_key: ******"),
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


def early_init() -> None:
    """
    Early initialization of logging system - call BEFORE importing other modules.

    This ensures all logging calls are intercepted from the start and prevents
    race conditions with threaded imports or configuration conflicts.

    Thread-safe: Uses double-checked locking to prevent race conditions when
    multiple threads call it simultaneously.

    CRITICAL REQUIREMENTS:
    - Race Condition Prevention: Uses double-checked locking pattern
    - Thread-Safe InterceptHandler: Proper frame inspection for threading contexts
    - Multiprocessing Safety: All handlers use enqueue=True
    """
    global _early_init_done

    # Quick check without lock for performance (first check)
    if _early_init_done:
        return

    # Thread-safe double-checked locking pattern
    with _early_init_lock:
        if _early_init_done:  # Double-check inside lock
            return  # Another thread already initialized

        # Remove default loguru handler immediately
        logger.remove()

        # Create thread-safe InterceptHandler early
        intercept_handler = InterceptHandler()

        # Set up basic root logging level
        logging.root.setLevel(logging.DEBUG)

        # Replace root handler immediately
        logging.root.handlers = [intercept_handler]

        # Configure basic loguru handler with safety features - stdout only
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>",
            enqueue=True,  # Critical for thread/multiprocessing safety
            catch=True,  # Prevent logging errors from crashing app
            backtrace=True,
            diagnose=True,
        )

        # Immediately intercept critical loggers for Discord.py, async frameworks, and boss-bot
        critical_loggers = [
            # Python standard library
            "asyncio",
            "concurrent.futures",
            "multiprocessing",
            "threading",
            "urllib3",
            "requests",
            "httpx",
            "aiohttp",
            # Discord.py framework
            "discord",
            "discord.client",
            "discord.gateway",
            "discord.http",
            "discord.voice_client",
            "discord.shard",
            "discord.ext.commands",
            "discord.ext.tasks",
            # Boss-bot specific modules
            "boss_bot",
            "boss_bot.bot",
            "boss_bot.bot.client",
            "boss_bot.bot.cogs",
            "boss_bot.core",
            "boss_bot.core.downloads",
            "boss_bot.core.queue",
            "boss_bot.cli",
            "boss_bot.monitoring",
            "boss_bot.storage",
            "boss_bot.utils",
            # AI/LangChain ecosystem
            "langchain",
            "langchain.agents",
            "langchain.chains",
            "langchain.llms",
            "langchain.vectorstores",
            "langsmith",
            "openai",
            "anthropic",
            # Download tools
            "gallery_dl",
            "yt_dlp",
            "youtube_dl",
            # Monitoring and metrics
            "prometheus_client",
            "uvicorn",
            "gunicorn",
            "fastapi",
        ]

        for logger_name in critical_loggers:
            log_instance = logging.getLogger(logger_name)
            log_instance.handlers = [intercept_handler]
            log_instance.propagate = False

        # Mark as completed inside the lock
        _early_init_done = True
        logger.debug("Early logging initialization completed with thread safety")


class InterceptHandler(logging.Handler):
    """
    Thread-safe and async-safe interceptor for standard logging into Loguru.

    This implementation ensures proper thread safety and multiprocessing compatibility
    by using improved frame inspection and avoiding potential deadlocks.

    Key safety features:
    - Proper frame inspection that works with frozen imports and threading
    - Exception handling to prevent crashes
    - Thread-safe emit method
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


class ThreadSafeLogConfig(BaseModel):
    """
    Thread-safe logging configuration for boss-bot.

    Configured for stdout-only logging with thread safety and interception features.
    Can be configured from BossSettings for full integration.
    """

    log_level: str = "INFO"
    enable_file_logging: bool = False  # Default to stdout only
    log_file_path: str = "logs/boss_bot.log"  # Used only if file logging enabled
    enable_json_logging: bool = False
    enable_interception: bool = True
    enable_sensitive_obfuscation: bool = False  # Enable security obfuscation
    enable_payload_formatting: bool = True  # Enable payload pretty-printing

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    @classmethod
    def from_boss_settings(cls, settings: Any) -> ThreadSafeLogConfig:
        """Create ThreadSafeLogConfig from BossSettings.

        Args:
            settings: Boss-bot settings instance (BossSettings)

        Returns:
            ThreadSafeLogConfig instance configured from boss-bot settings
        """
        # Determine file logging based on environment and debug settings
        enable_file_logging = (
            settings.debug or settings.environment.value == "development" or settings.environment.value == "staging"
        )

        # Use storage_root for log file path
        log_file_path = str(settings.storage_root / "logs" / "boss_bot.log")

        # Enable JSON logging for production environments
        enable_json_logging = settings.environment.value == "production"

        # Enable sensitive obfuscation for production
        enable_sensitive_obfuscation = settings.environment.value == "production"

        return cls(
            log_level=settings.log_level,
            enable_file_logging=enable_file_logging,
            log_file_path=log_file_path,
            enable_json_logging=enable_json_logging,
            enable_sensitive_obfuscation=enable_sensitive_obfuscation,
            enable_payload_formatting=True,  # Always enable for debugging
        )


def configure_thread_safe_logging(config: ThreadSafeLogConfig | None = None) -> loguru.Logger:
    """
    Configure global logging settings with thread, async, and multiprocessing safety.

    This function sets up thread-safe and multiprocessing-safe logging by:
    - Using enqueue=True for non-blocking, process-safe logging
    - Configuring proper exception handling with catch=True
    - Setting up InterceptHandler for standard logging integration
    - Ensuring all handlers are replaced consistently

    Args:
        config: Optional configuration. Uses defaults if not provided.

    Returns:
        The configured logger instance.
    """
    if config is None:
        config = ThreadSafeLogConfig()

    global _console_handler_id, _file_handler_id

    # Ensure early init was called
    if not _early_init_done:
        early_init()

    # Convert string log level to logging constant
    if isinstance(config.log_level, str) and hasattr(logging, config.log_level):
        log_level = getattr(logging, config.log_level)
    else:
        log_level = logging.INFO

    # Create thread-safe intercept handler
    intercept_handler = InterceptHandler()

    # Set root logging level
    logging.root.setLevel(log_level)

    # Replace handlers for all existing loggers to ensure consistency
    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),  # pylint: disable=no-member
        # Python standard library
        "asyncio",
        "concurrent.futures",
        "multiprocessing",
        "threading",
        "urllib3",
        "requests",
        "httpx",
        "aiohttp",
        # Discord.py framework
        "discord",
        "discord.client",
        "discord.gateway",
        "discord.http",
        "discord.voice_client",
        "discord.shard",
        "discord.ext.commands",
        "discord.ext.tasks",
        # Boss-bot specific modules
        "boss_bot",
        "boss_bot.bot",
        "boss_bot.bot.client",
        "boss_bot.bot.cogs",
        "boss_bot.core",
        "boss_bot.core.downloads",
        "boss_bot.core.queue",
        "boss_bot.cli",
        "boss_bot.monitoring",
        "boss_bot.storage",
        "boss_bot.utils",
        # AI/LangChain ecosystem
        "langchain",
        "langchain.agents",
        "langchain.chains",
        "langchain.llms",
        "langsmith",
        "openai",
        "anthropic",
        # Download tools
        "gallery_dl",
        "yt_dlp",
        "youtube_dl",
        # Monitoring and web frameworks
        "prometheus_client",
        "uvicorn",
        "gunicorn",
        "fastapi",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            # Replace handlers with our thread-safe interceptor
            log_instance = logging.getLogger(name)
            log_instance.handlers = [intercept_handler]
            # Prevent propagation to avoid duplicate logs
            log_instance.propagate = False

    # Configure loguru with thread/async/multiprocessing safety - stdout only
    # Choose formatter based on configuration
    if config.enable_payload_formatting:
        formatter_func = format_record
    elif config.enable_sensitive_obfuscation:
        formatter_func = formatter_sensitive
    else:
        formatter_func = formatter

    # Remove existing handlers and configure new ones
    logger.remove()

    # Configure main stdout handler with advanced formatting
    logger.add(
        sys.stdout,
        serialize=config.enable_json_logging,
        format=formatter_func if not config.enable_json_logging else NEW_LOGGER_FORMAT,
        level=config.log_level,
        diagnose=True,
        backtrace=True,
        # CRITICAL: Enable enqueue for thread/multiprocessing safety
        enqueue=True,
        # Catch exceptions to prevent app crashes from logging errors
        catch=True,
    )

    # Add file handler if explicitly enabled
    if config.enable_file_logging:
        # Ensure log directory exists
        Path(config.log_file_path).parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            config.log_file_path,
            serialize=config.enable_json_logging,
            format=formatter_func if not config.enable_json_logging else NEW_LOGGER_FORMAT,
            level=config.log_level,
            diagnose=True,
            backtrace=True,
            enqueue=True,
            catch=True,
            rotation="20 MB",
            retention="1 month",
            compression="zip",
        )

    # Set up framework-specific loggers with thread safety
    _setup_discord_logger(intercept_handler)
    _setup_uvicorn_logger(intercept_handler)
    _setup_gunicorn_logger(intercept_handler)

    logger.info(f"Thread-safe logging configured with level: {config.log_level}")
    return logger


def _setup_discord_logger(intercept_handler: InterceptHandler) -> None:
    """Configure Discord.py loggers to use thread-safe InterceptHandler."""
    discord_loggers = [
        "discord",
        "discord.client",
        "discord.gateway",
        "discord.http",
        "discord.voice_client",
        "discord.shard",
        "discord.ext.commands",
    ]

    for logger_name in discord_loggers:
        log_instance = logging.getLogger(logger_name)
        log_instance.handlers = [intercept_handler]
        log_instance.propagate = False


def _setup_uvicorn_logger(intercept_handler: InterceptHandler) -> None:
    """Configure uvicorn loggers to use thread-safe InterceptHandler."""
    # Clear existing handlers and set up interception
    loggers = (logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn."))
    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = False

    # Set up main uvicorn logger with thread-safe handler
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = [intercept_handler]
    uvicorn_logger.propagate = False


def _setup_gunicorn_logger(intercept_handler: InterceptHandler) -> None:
    """Configure gunicorn loggers to use thread-safe InterceptHandler."""
    # Set up gunicorn error logger
    error_logger = logging.getLogger("gunicorn.error")
    error_logger.handlers = [intercept_handler]
    error_logger.propagate = False

    # Set up gunicorn access logger
    access_logger = logging.getLogger("gunicorn.access")
    access_logger.handlers = [intercept_handler]
    access_logger.propagate = False


def is_early_init_done() -> bool:
    """Check if early initialization has been completed."""
    return _early_init_done


def reset_logging_state() -> None:
    """
    Reset logging state for testing purposes.

    WARNING: This is only for testing and should not be used in production.
    """
    global _early_init_done
    with _early_init_lock:
        _early_init_done = False
        logger.remove()


# Logger tree analysis functions from original
class LoggerModel(BaseModel):
    """Model for logger tree analysis."""

    name: str
    level: int | None = None
    children: list[Any] | None = None


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
            nodesm[name] = nodem = LoggerModel(name=name, level=loggeritem.getEffectiveLevel(), children=[])
        i = name.rfind(".", 0, len(name) - 1)
        parentm = rootm if i == -1 else nodesm[name[:i]]
        parentm.children.append(nodem)
    return rootm


def get_lm_from_tree(loggertree: LoggerModel, find_me: str) -> LoggerModel | None:
    """Recursively search for a logger model in the logger tree.

    Args:
        loggertree: The root logger model to search from.
        find_me: The name of the logger model to find.

    Returns:
        The found logger model, or None if not found.
    """
    if find_me == loggertree.name:
        return loggertree
    else:
        if loggertree.children:
            for ch in loggertree.children:
                if result := get_lm_from_tree(ch, find_me):
                    return result
    return None


def reset_logging(
    log_level: str = "INFO", *, enable_sensitive_obfuscation: bool = False, enable_payload_formatting: bool = True
) -> None:
    """Reset logging configuration with thread and multiprocessing safety.

    Args:
        log_level: Level for logging output
        enable_sensitive_obfuscation: Enable security obfuscation
        enable_payload_formatting: Enable payload pretty-printing
    """
    global _console_handler_id, _file_handler_id

    # Configure with thread-safe extra context and request ID
    logger.configure(
        extra={"room_id": "", "request_id": REQUEST_ID_CONTEXTVAR.get()},
        patcher=set_log_extras if not enable_sensitive_obfuscation else None,
    )

    # Remove existing handlers
    if _console_handler_id is not None:
        logger.remove(_console_handler_id)
    else:
        logger.remove()  # remove the default stderr handler

    # Choose formatter
    if enable_payload_formatting:
        formatter_func = format_record
    elif enable_sensitive_obfuscation:
        formatter_func = formatter_sensitive
    else:
        formatter_func = formatter

    # Add console handler with thread/multiprocessing safety - stdout only
    _console_handler_id = logger.add(
        sys.stdout,
        level=log_level,
        format=formatter_func,
        enqueue=True,  # Enable for thread safety
        catch=True,  # Prevent crashes from logging errors
    )


# Export the main early initialization function with boss-bot naming convention
__all__ = [
    # Core functions
    "early_init",
    "configure_thread_safe_logging",
    "reset_logging",
    # Configuration
    "ThreadSafeLogConfig",
    "InterceptHandler",
    # Formatting and utilities
    "format_record",
    "set_log_extras",
    "request_id_filter",
    "obfuscate_message",
    "formatter",
    "formatter_sensitive",
    # Logger tree analysis
    "LoggerModel",
    "generate_tree",
    "get_lm_from_tree",
    # Constants
    "LOGLEVEL_MAPPING",
    "NEW_LOGGER_FORMAT",
    "LOGURU_CONSOLE_FORMAT",
    "REQUEST_ID_CONTEXTVAR",
    # Utilities
    "is_early_init_done",
    "reset_logging_state",
]
