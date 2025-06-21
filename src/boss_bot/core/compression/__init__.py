"""Media compression module for Boss-Bot.

This module provides video, audio, and image compression capabilities with
configurable target sizes and quality settings. It replicates the logic from
the bash script compress-discord.sh but with enhanced Python features.
"""

# CompressionManager import is handled at the bottom to avoid circular imports
# Import CompressionManager after models to avoid circular imports
from .manager import CompressionManager
from .models import (
    CompressionError,
    CompressionResult,
    CompressionSettings,
    MediaInfo,
)

__all__ = [
    "CompressionManager",
    "CompressionError",
    "CompressionResult",
    "CompressionSettings",
    "MediaInfo",
]
