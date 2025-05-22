"""Storage quota management system for Boss-Bot."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set, Union

from boss_bot.storage.validation_manager import FileValidator


class QuotaExceededError(Exception):
    """Raised when a quota limit is exceeded."""

    pass


@dataclass
class QuotaConfig:
    """Configuration for storage quotas."""

    max_total_size_mb: int = 50  # From story constraints
    max_concurrent_downloads: int = 5  # From story constraints


class QuotaManager:
    """Manages storage quotas and concurrent downloads."""

    def __init__(self, storage_root: Path):
        """Initialize the QuotaManager.

        Args:
            storage_root: Root directory for file storage
        """
        self.storage_root = storage_root
        self.config = QuotaConfig()
        self._active_downloads: set[str] = set()
        self._files: dict[str, float] = {}  # filename -> size in MB
        self._current_usage_bytes = 0
        self.validator = FileValidator()

        # Create storage directory structure
        self._create_directory_structure()

    def _create_directory_structure(self) -> None:
        """Create the required directory structure for file storage.

        Creates:
            - downloads/: Main downloads directory
            - downloads/temp/: Temporary storage during downloads
            - downloads/completed/: Successfully downloaded files
            - downloads/failed/: Failed download attempts for debugging
        """
        dirs = ["downloads", "downloads/temp", "downloads/completed", "downloads/failed"]

        for dir_path in dirs:
            full_path = self.storage_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    @property
    def current_usage_mb(self) -> float:
        """Get the current storage usage in megabytes."""
        return self._current_usage_bytes / (1024 * 1024)  # Convert bytes to MB

    @property
    def active_downloads_count(self) -> int:
        """Get the number of active downloads."""
        return len(self._active_downloads)

    def can_start_download(self) -> bool:
        """Check if a new download can be started based on concurrent limit.

        Returns:
            True if a new download can be started, False otherwise
        """
        return self.active_downloads_count < self.config.max_concurrent_downloads

    def start_download(self, download_id: str) -> None:
        """Start tracking a new download.

        Args:
            download_id: Unique identifier for the download

        Raises:
            QuotaExceededError: If maximum concurrent downloads would be exceeded
        """
        if not self.can_start_download():
            raise QuotaExceededError(
                f"Cannot start download: Maximum concurrent downloads ({self.config.max_concurrent_downloads}) reached"
            )
        self._active_downloads.add(download_id)

    def complete_download(self, download_id: str) -> None:
        """Mark a download as complete and stop tracking it.

        Args:
            download_id: Unique identifier for the download

        Raises:
            ValueError: If the download_id is not being tracked
        """
        if download_id not in self._active_downloads:
            raise ValueError(f"Download {download_id} is not being tracked")
        self._active_downloads.remove(download_id)

    def check_quota(self, size_mb: int) -> bool:
        """Check if adding a file of given size would exceed quota.

        Args:
            size_mb: Size of the file in megabytes

        Returns:
            bool: True if file can be added, False if it would exceed quota
        """
        current_mb = self._current_usage_bytes / (1024 * 1024)
        return current_mb + size_mb <= self.config.max_total_size_mb

    def add_file(self, file_path: str | Path, size_mb: int) -> None:
        """Add a file to the quota tracking.

        Args:
            file_path: Path to the file (can be string or Path object)
            size_mb: Size of the file in megabytes

        Raises:
            QuotaExceededError: If adding the file would exceed quota
        """
        if not self.check_quota(size_mb):
            raise QuotaExceededError(f"Adding file would exceed quota of {self.config.max_total_size_mb}MB")

        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self._files[file_path.name] = float(size_mb)
        self._current_usage_bytes += size_mb * 1024 * 1024

    def remove_file(self, filename: str) -> None:
        """Remove a file from quota tracking.

        Args:
            filename: Name of the file to remove

        Raises:
            KeyError: If file is not found in quota tracking
        """
        if filename not in self._files:
            raise KeyError(f"File {filename} not found in quota tracking")

        size_mb = self._files[filename]
        self._current_usage_bytes -= int(size_mb * 1024 * 1024)
        del self._files[filename]

    def get_quota_status(self) -> dict:
        """Get the current quota status.

        Returns:
            dict: A dictionary containing:
                - total_bytes: Total storage capacity in bytes
                - used_bytes: Currently used storage in bytes
                - available_bytes: Available storage in bytes
                - total_size_mb: Total storage capacity in MB
                - used_size_mb: Currently used storage in MB
                - available_size_mb: Available storage in MB
                - usage_percentage: Current usage as a percentage
                - active_downloads: Number of active downloads
                - max_concurrent_downloads: Maximum concurrent downloads allowed
        """
        total_bytes = self.config.max_total_size_mb * 1024 * 1024
        used_bytes = self._current_usage_bytes
        available_bytes = total_bytes - used_bytes
        usage_percentage = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0

        return {
            "total_bytes": total_bytes,
            "used_bytes": used_bytes,
            "available_bytes": available_bytes,
            "total_size_mb": self.config.max_total_size_mb,
            "used_size_mb": used_bytes / (1024 * 1024),
            "available_size_mb": available_bytes / (1024 * 1024),
            "usage_percentage": usage_percentage,
            "active_downloads": len(self._active_downloads),
            "max_concurrent_downloads": self.config.max_concurrent_downloads,
        }
