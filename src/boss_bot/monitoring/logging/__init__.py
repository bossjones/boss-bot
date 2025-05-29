"""Logging configuration for the application."""

import sys
import warnings

from loguru import logger

# Import new thread-safe logging functionality
from .interceptor import (
    ThreadSafeLogConfig,
    configure_thread_safe_logging,
    early_init,
    is_early_init_done,
)
from .logging_config import LogConfig
from .logging_config import log_config as new_log_config


def log_config():
    """
    Configure logging for the application.

    DEPRECATED: This function is deprecated in favor of thread-safe logging.
    Use early_init() followed by configure_thread_safe_logging() instead.

    This function sets up loguru logging with a standard format and INFO level.
    For production applications with threading, asyncio, or multiprocessing,
    use the thread-safe alternatives.
    """
    warnings.warn(
        "log_config() is deprecated. Use early_init() and configure_thread_safe_logging() "
        "from boss_bot.monitoring.logging for thread-safe logging in production.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Remove default handler
    logger.remove()

    # Add stderr handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Log configuration complete
    logger.info("Logging is configured.")


def setup_thread_safe_logging(
    log_level: str = "INFO",
    enable_file_logging: bool = False,  # Default to stdout only
    log_file_path: str = "logs/boss_bot.log",
    enable_json_logging: bool = False,
    enable_sensitive_obfuscation: bool = False,
    enable_payload_formatting: bool = True,
) -> logger:
    """
    Convenience function to set up thread-safe logging for boss-bot.

    This is the recommended way to configure logging for production applications.
    Call early_init() first, preferably before importing other modules.
    Defaults to stdout-only logging for containerized environments.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Whether to log to files (default: False, stdout only)
        log_file_path: Path to log file (only used if file logging enabled)
        enable_json_logging: Whether to format logs as JSON
        enable_sensitive_obfuscation: Enable security obfuscation for sensitive data
        enable_payload_formatting: Enable pretty-printing of payload data

    Returns:
        Configured logger instance

    Example:
        from boss_bot.monitoring.logging import early_init, setup_thread_safe_logging

        # Call FIRST - before other imports
        early_init()

        # Import other modules...
        import discord, asyncio, etc

        # Configure full logging (stdout only by default)
        logger = setup_thread_safe_logging(log_level="DEBUG")

        # With payload formatting and security obfuscation
        logger = setup_thread_safe_logging(
            log_level="INFO",
            enable_sensitive_obfuscation=True,
            enable_payload_formatting=True
        )
    """
    # Ensure early init was called
    if not is_early_init_done():
        early_init()

    config = ThreadSafeLogConfig(
        log_level=log_level,
        enable_file_logging=enable_file_logging,
        log_file_path=log_file_path,
        enable_json_logging=enable_json_logging,
        enable_sensitive_obfuscation=enable_sensitive_obfuscation,
        enable_payload_formatting=enable_payload_formatting,
    )

    return configure_thread_safe_logging(config)


def setup_boss_bot_logging(settings=None) -> logger:
    """
    Setup logging specifically configured for boss-bot with settings integration.

    This is the recommended function for boss-bot applications as it automatically
    configures logging based on BossSettings and environment.

    Args:
        settings: Optional BossSettings instance. If not provided, will try to import and create one.

    Returns:
        Configured logger instance

    Example:
        from boss_bot.monitoring.logging import early_init, setup_boss_bot_logging
        from boss_bot.core.env import BossSettings

        # Call FIRST - before other imports
        early_init()

        # Import other modules...
        import discord, asyncio, etc

        # Configure logging with boss-bot settings
        settings = BossSettings()
        logger = setup_boss_bot_logging(settings)

        # Or let it auto-create settings
        logger = setup_boss_bot_logging()
    """
    # Ensure early init was called
    if not is_early_init_done():
        early_init()

    # Import settings if not provided
    if settings is None:
        try:
            from boss_bot.core.env import BossSettings

            settings = BossSettings()
        except ImportError:
            # Fall back to default configuration if BossSettings not available
            return setup_thread_safe_logging()

    # Create config from boss settings
    config = ThreadSafeLogConfig.from_boss_settings(settings)

    return configure_thread_safe_logging(config)


# Export all the logging functionality
__all__ = [
    # Legacy (deprecated)
    "log_config",
    # New thread-safe logging (recommended)
    "early_init",
    "setup_thread_safe_logging",
    "setup_boss_bot_logging",  # Boss-bot specific setup
    "configure_thread_safe_logging",
    "ThreadSafeLogConfig",
    # Configuration classes
    "LogConfig",
    "new_log_config",
    # Utilities
    "is_early_init_done",
]
