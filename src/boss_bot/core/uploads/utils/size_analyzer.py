"""File size analysis utilities for upload planning."""

from __future__ import annotations

from typing import List

from boss_bot.core.env import BossSettings
from boss_bot.core.uploads.models import MediaFile, SizeAnalysis


class FileSizeAnalyzer:
    """Analyzes file sizes to determine upload strategy."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        # Discord's default limit is 25MB for most servers
        self.discord_limit_mb = 25.0
        # Use compression target size from settings
        self.max_upload_size_mb = getattr(settings, "compression_max_upload_size_mb", 50.0)

    async def analyze_files(self, media_files: list[MediaFile]) -> SizeAnalysis:
        """Analyze media files to categorize by size requirements.

        Args:
            media_files: List of media files to analyze

        Returns:
            SizeAnalysis with files categorized by size requirements
        """
        acceptable_files = []
        oversized_files = []

        for media_file in media_files:
            if media_file.size_mb <= self.discord_limit_mb:
                acceptable_files.append(media_file)
            else:
                oversized_files.append(media_file)

        total_size_mb = sum(f.size_mb for f in media_files)

        return SizeAnalysis(
            acceptable_files=acceptable_files,
            oversized_files=oversized_files,
            total_files=len(media_files),
            total_size_mb=total_size_mb,
        )

    def can_upload_directly(self, media_file: MediaFile) -> bool:
        """Check if a file can be uploaded directly to Discord.

        Args:
            media_file: Media file to check

        Returns:
            True if file is within Discord's size limits
        """
        return media_file.size_mb <= self.discord_limit_mb

    def needs_compression(self, media_file: MediaFile) -> bool:
        """Check if a file needs compression before upload.

        Args:
            media_file: Media file to check

        Returns:
            True if file exceeds Discord's size limits
        """
        return media_file.size_mb > self.discord_limit_mb

    def get_size_category(self, media_file: MediaFile) -> str:
        """Get a human-readable size category for a file.

        Args:
            media_file: Media file to categorize

        Returns:
            String describing the size category
        """
        size_mb = media_file.size_mb

        if size_mb < 1.0:
            return "small"
        elif size_mb <= 10.0:
            return "medium"
        elif size_mb <= self.discord_limit_mb:
            return "large"
        elif size_mb <= 50.0:
            return "oversized"
        else:
            return "very_large"

    def estimate_compression_needed(self, media_file: MediaFile) -> float:
        """Estimate compression ratio needed to fit Discord limits.

        Args:
            media_file: Media file to analyze

        Returns:
            Compression ratio needed (0.0-1.0)
        """
        if self.can_upload_directly(media_file):
            return 1.0  # No compression needed

        # Target slightly under Discord limit to account for metadata
        target_size_mb = self.discord_limit_mb * 0.95
        return target_size_mb / media_file.size_mb

    def get_batch_size_limit_mb(self) -> float:
        """Get the batch size limit for uploads.

        Returns:
            Maximum batch size in MB
        """
        return getattr(self.settings, "upload_batch_size_mb", 20.0)

    def can_fit_in_batch(self, files: list[MediaFile], max_size_mb: float = None) -> bool:
        """Check if files can fit in a single upload batch.

        Args:
            files: List of media files
            max_size_mb: Maximum batch size in MB (uses setting if None)

        Returns:
            True if all files fit within batch size limit
        """
        if max_size_mb is None:
            max_size_mb = self.get_batch_size_limit_mb()

        total_size_mb = sum(f.size_mb for f in files)
        return total_size_mb <= max_size_mb
