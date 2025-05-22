"""Logging configuration for the application."""

import sys

from loguru import logger


def log_config():
    """Configure logging for the application.

    This function sets up loguru logging with a standard format and INFO level.
    """
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
