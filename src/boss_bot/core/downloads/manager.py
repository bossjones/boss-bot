"""Base download manager implementation."""

import asyncio
import logging
from typing import Dict, List, Optional
from uuid import UUID

from boss_bot.core.env import BossSettings
from boss_bot.storage.quotas import QuotaManager
from boss_bot.storage.validation_manager import FileValidator

logger = logging.getLogger(__name__)


class DownloadStatus:
    """Status of a download."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Download:
    """Represents a download task."""

    def __init__(self, download_id: UUID, url: str, user_id: int, channel_id: int, filename: str | None = None):
        """Initialize a download task."""
        self.download_id = download_id
        self.url = url
        self.user_id = user_id
        self.channel_id = channel_id
        self.filename = filename
        self.status = DownloadStatus.QUEUED
        self.progress = 0.0
        self.error = None
        self.task: asyncio.Task | None = None


class DownloadManager:
    """Manages download tasks."""

    def __init__(self, settings: BossSettings, max_concurrent_downloads: int | None = 2):
        """Initialize the download manager.

        Args:
            settings: BossSettings instance
            max_concurrent_downloads: Maximum number of concurrent downloads (default: 2)
        """
        self.settings = settings
        self.max_concurrent_downloads = max_concurrent_downloads or 2
        self.active_downloads: dict[UUID, Download] = {}
        self.validator = FileValidator()
        self.quota_manager = QuotaManager(storage_root=self.settings.storage_root)
        self._download_lock = asyncio.Lock()

    async def start_download(self, download: Download) -> bool:
        """Start a download task.

        Args:
            download: The download to start

        Returns:
            bool: True if download started successfully
        """
        async with self._download_lock:
            # Check if we can start another download
            if len(self.active_downloads) >= self.max_concurrent_downloads:
                return False

            # Add to active downloads
            self.active_downloads[download.download_id] = download
            download.status = DownloadStatus.DOWNLOADING

            # Start download task
            download.task = asyncio.create_task(self._download_task(download))

            return True

    async def _download_task(self, download: Download):
        """Execute the download task.

        Args:
            download: The download to execute
        """
        try:
            # TODO: Implement actual download logic in Phase 1
            # For now, just simulate a download
            for i in range(10):
                if download.status == DownloadStatus.CANCELLED:
                    return

                download.progress = (i + 1) * 10
                await asyncio.sleep(1)

            download.status = DownloadStatus.COMPLETED

        except asyncio.CancelledError:
            # Handle cancellation gracefully
            download.status = DownloadStatus.CANCELLED
            logger.debug(f"Download {download.download_id} was cancelled")
            # Re-raise to ensure proper task cancellation
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            download.status = DownloadStatus.FAILED
            download.error = str(e)

        finally:
            # Remove from active downloads
            async with self._download_lock:
                self.active_downloads.pop(download.download_id, None)

    async def cancel_download(self, download_id: UUID, user_id: int) -> bool:
        """Cancel a download.

        Args:
            download_id: ID of download to cancel
            user_id: ID of user requesting cancellation

        Returns:
            bool: True if download was cancelled
        """
        download = self.active_downloads.get(download_id)
        if not download:
            return False

        # Check if user has permission to cancel
        if download.user_id != user_id:
            return False

        download.status = DownloadStatus.CANCELLED
        if download.task:
            download.task.cancel()
            try:
                await download.task
            except asyncio.CancelledError:
                pass

        # Remove from active downloads
        async with self._download_lock:
            self.active_downloads.pop(download_id, None)

        return True

    async def get_download_status(self, download_id: UUID) -> str | None:
        """Get the status of a download.

        Args:
            download_id: ID of download to check

        Returns:
            Optional[str]: Status message if download found
        """
        download = self.active_downloads.get(download_id)
        if not download:
            return None

        status_msg = f"Status: {download.status}"
        if download.status == DownloadStatus.DOWNLOADING:
            status_msg += f" ({download.progress:.1f}%)"
        elif download.status == DownloadStatus.FAILED:
            status_msg += f" (Error: {download.error})"

        return status_msg

    async def get_active_downloads(self) -> list[Download]:
        """Get list of active downloads.

        Returns:
            List[Download]: List of active downloads
        """
        return list(self.active_downloads.values())

    async def cleanup(self):
        """Clean up resources."""
        # Cancel all active downloads
        for download in self.active_downloads.values():
            download.status = DownloadStatus.CANCELLED
            if download.task:
                download.task.cancel()

        # Wait for all tasks to complete
        if self.active_downloads:
            await asyncio.gather(*[d.task for d in self.active_downloads.values() if d.task], return_exceptions=True)

        self.active_downloads.clear()

    async def validate_url(self, url: str) -> bool:
        """Validate if a URL is supported for downloading.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is valid and supported
        """
        # For now, just check if it's a valid Twitter or Reddit URL
        valid_domains = ["twitter.com", "reddit.com"]
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.scheme in ["http", "https"] and any(domain in parsed.netloc for domain in valid_domains)
        except Exception:
            return False
