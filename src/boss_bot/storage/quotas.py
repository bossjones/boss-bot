"""Storage quota management system for Boss-Bot."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set


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
        self._active_downloads: set[str] = set()  # Set of active download IDs
        self._max_storage_bytes = self.config.max_total_size_mb * 1024 * 1024  # Convert MB to bytes
        self._current_usage_bytes = 0

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
                f"Cannot start download {download_id}: Maximum concurrent downloads "
                f"({self.config.max_concurrent_downloads}) reached"
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

    def check_quota(self, file_size: int) -> bool:
        """Check if adding a file of given size would exceed quota.

        Args:
            file_size: Size of the file in bytes

        Returns:
            True if file can be added, False if it would exceed quota
        """
        return self._current_usage_bytes + file_size <= self._max_storage_bytes

    def add_file(self, filename: str, size_mb: float) -> None:
        """Record a new file in the quota tracking system.

        Args:
            filename: Name of the file
            size_mb: Size of the file in megabytes

        Raises:
            QuotaExceededError: If adding the file would exceed quota
        """
        if not self.check_quota(size_mb * 1024 * 1024):
            raise QuotaExceededError(
                f"Adding file {filename} ({size_mb}MB) would exceed "
                f"quota of {self.config.max_total_size_mb}MB "
                f"(current usage: {self.current_usage_mb}MB)"
            )

        self._files[filename] = size_mb
        self._current_usage_bytes += size_mb * 1024 * 1024

    def remove_file(self, filename: str) -> None:
        """Remove a file from the quota tracking system.

        Args:
            filename: Name of the file

        Raises:
            KeyError: If the file is not found in the quota tracking system
        """
        if filename not in self._files:
            raise KeyError(f"File {filename} not found in quota tracking")
        size_bytes = self._files[filename] * 1024 * 1024
        self._current_usage_bytes -= size_bytes
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
