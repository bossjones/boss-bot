"""Storage quota management system for Boss-Bot."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


class QuotaExceededError(Exception):
    """Raised when a file operation would exceed the storage quota."""

    pass


@dataclass
class QuotaConfig:
    """Configuration for storage quotas."""

    max_total_size_mb: int = 50  # From story constraints
    max_concurrent_downloads: int = 5  # From story constraints


class QuotaManager:
    """Manages storage quotas for downloaded files."""

    def __init__(self, storage_root: Path):
        """Initialize the quota manager.

        Args:
            storage_root: Path to the storage directory
        """
        self.storage_root = storage_root
        self.config = QuotaConfig()
        self._files: dict[str, float] = {}  # filename -> size in MB

    @property
    def current_usage_mb(self) -> float:
        """Get the current storage usage in megabytes."""
        return sum(self._files.values())

    def check_quota(self, size_mb: float) -> bool:
        """Check if adding a file of given size would exceed quota.

        Args:
            size_mb: Size of the file in megabytes

        Returns:
            True if file can be added, False if it would exceed quota
        """
        return (
            size_mb <= self.config.max_total_size_mb
            and (self.current_usage_mb + size_mb) <= self.config.max_total_size_mb
        )

    def add_file(self, filename: str, size_mb: float) -> None:
        """Record a new file in the quota tracking system.

        Args:
            filename: Name of the file
            size_mb: Size of the file in megabytes

        Raises:
            QuotaExceededError: If adding the file would exceed quota
        """
        if not self.check_quota(size_mb):
            raise QuotaExceededError(
                f"Adding file {filename} ({size_mb}MB) would exceed "
                f"quota of {self.config.max_total_size_mb}MB "
                f"(current usage: {self.current_usage_mb}MB)"
            )

        self._files[filename] = size_mb
