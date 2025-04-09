"""Logging configuration for the boss-bot application."""

import sys
from pathlib import Path
from typing import Dict, Union

from loguru import logger
from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration."""

    LOGGER_NAME: str = "boss_bot"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: Path = Path("logs/boss_bot.log")

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        # Ensure log directory exists
        self.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Configure loguru
        config: dict[str, str | dict] = {
            "handlers": [
                {
                    "sink": sys.stderr,
                    "format": self.LOG_FORMAT,
                    "level": self.LOG_LEVEL,
                    "colorize": True,
                },
                {
                    "sink": str(self.LOG_FILE_PATH),
                    "format": self.LOG_FORMAT,
                    "level": self.LOG_LEVEL,
                    "rotation": "20 MB",
                    "retention": "1 month",
                    "compression": "zip",
                },
            ],
        }

        # Remove default handler
        logger.remove()

        # Add new handlers
        for handler in config["handlers"]:
            logger.add(**handler)

        logger.info(f"Logging configured for {self.LOGGER_NAME}")


# Create default logging configuration
log_config = LogConfig()
