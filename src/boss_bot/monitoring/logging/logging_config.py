"""Logging configuration for the boss-bot application."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Union

from loguru import logger
from pydantic import BaseModel

if TYPE_CHECKING:
    from boss_bot.core.env import BossSettings


class LogConfig(BaseModel):
    """Logging configuration for boss-bot.

    This class provides traditional Loguru configuration with boss-bot integration.
    For production applications with threading, asyncio, or multiprocessing,
    use the thread-safe logging from boss_bot.monitoring.logging instead.
    """

    LOGGER_NAME: str = "boss_bot"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: Path = Path("logs/boss_bot.log")
    ENABLE_FILE_LOGGING: bool = False  # Default to stdout only for containerized environments

    @classmethod
    def from_boss_settings(cls, settings: "BossSettings") -> "LogConfig":
        """Create LogConfig from BossSettings.

        Args:
            settings: Boss-bot settings instance

        Returns:
            LogConfig instance with values from settings
        """
        # Determine log file path using storage_root from settings
        log_file_path = settings.storage_root / "logs" / "boss_bot.log"

        return cls(
            LOG_LEVEL=settings.log_level,
            LOG_FILE_PATH=log_file_path,
            ENABLE_FILE_LOGGING=settings.debug or settings.environment.value == "development",
        )

    def setup_logging(self, settings: Optional["BossSettings"] = None) -> None:
        """Set up logging configuration.

        Args:
            settings: Optional boss-bot settings for enhanced configuration
        """
        # Use settings-based configuration if available
        if settings:
            config = self.from_boss_settings(settings)
        else:
            config = self

        # Ensure log directory exists only if file logging is enabled
        if config.ENABLE_FILE_LOGGING:
            config.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Configure loguru handlers
        handlers = [
            # Console handler (always enabled)
            {
                "sink": sys.stderr,
                "format": config.LOG_FORMAT,
                "level": config.LOG_LEVEL,
                "colorize": True,
                "enqueue": True,  # Thread safety
                "catch": True,  # Error resilience
            }
        ]

        # Add file handler only if enabled
        if config.ENABLE_FILE_LOGGING:
            handlers.append(
                {
                    "sink": str(config.LOG_FILE_PATH),
                    "format": config.LOG_FORMAT,
                    "level": config.LOG_LEVEL,
                    "rotation": "20 MB",
                    "retention": "1 month",
                    "compression": "zip",
                    "enqueue": True,  # Thread safety
                    "catch": True,  # Error resilience
                }
            )

        # Remove default handler
        logger.remove()

        # Add configured handlers
        for handler in handlers:
            logger.add(**handler)

        logger.info(
            f"Logging configured for {config.LOGGER_NAME} (level: {config.LOG_LEVEL}, file_logging: {config.ENABLE_FILE_LOGGING})"
        )


# Create default logging configuration
log_config = LogConfig()
