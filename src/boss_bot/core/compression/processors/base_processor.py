"""Abstract base class for media processors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from boss_bot.core.compression.models import CompressionResult, MediaInfo
from boss_bot.core.env import BossSettings


class BaseProcessor(ABC):
    """Abstract base class for media processors."""

    def __init__(self, settings: BossSettings):
        """Initialize the processor with settings."""
        self.settings = settings
        self.supported_extensions: list[str] = []
        self.min_bitrate_kbps: int = 32

    @abstractmethod
    async def compress(self, input_path: Path, target_size_mb: int, output_path: Path) -> CompressionResult:
        """Compress media file.

        Args:
            input_path: Path to input file
            target_size_mb: Target size in megabytes
            output_path: Path for output file

        Returns:
            CompressionResult with operation details

        Raises:
            CompressionError: If compression fails
        """
        pass

    @abstractmethod
    async def get_media_info(self, input_path: Path) -> MediaInfo:
        """Get media file information.

        Args:
            input_path: Path to media file

        Returns:
            MediaInfo object with file details

        Raises:
            CompressionError: If file analysis fails
        """
        pass

    def supports_file(self, file_path: Path) -> bool:
        """Check if processor supports this file type.

        Args:
            file_path: Path to check

        Returns:
            True if file type is supported
        """
        return file_path.suffix.lower().lstrip(".") in self.supported_extensions

    def _calculate_target_bitrate(self, target_size_mb: int, duration_seconds: float) -> int:
        """Calculate target bitrate based on file size and duration.

        Replicates bash script logic but with configurable target size.
        Leave 2MB buffer for container overhead (similar to bash script using 23MB for 25MB target).

        Args:
            target_size_mb: Target file size in MB
            duration_seconds: Media duration in seconds

        Returns:
            Target bitrate in kbps
        """
        # Ensure at least 1MB after buffer
        effective_size_mb = max(1, target_size_mb - 2)
        return int(effective_size_mb * 8 * 1000 / duration_seconds)

    def _generate_output_filename(self, input_path: Path, target_size_mb: int, suffix: str = "") -> str:
        """Generate output filename with size indicator.

        Args:
            input_path: Original file path
            target_size_mb: Target size for filename
            suffix: Optional suffix to add

        Returns:
            Generated filename
        """
        stem = input_path.stem
        extension = input_path.suffix
        size_indicator = f"{target_size_mb}MB"

        if suffix:
            return f"{size_indicator}_{stem}_{suffix}{extension}"
        else:
            return f"{size_indicator}_{stem}{extension}"
