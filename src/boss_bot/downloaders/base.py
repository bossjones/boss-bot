"""Base download manager implementation."""

import re
from enum import Enum
from typing import Dict, Optional
from urllib.parse import urlparse


class DownloadStatus(Enum):
    """Download status enum."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadManager:
    """Base download manager class."""

    VALID_DOMAINS = {
        "twitter.com",
        "x.com",
        "reddit.com",
    }

    def __init__(self, max_concurrent_downloads: int = 5):
        """Initialize download manager."""
        self.max_concurrent_downloads = max_concurrent_downloads
        self.active_downloads: dict[str, dict] = {}

    async def validate_url(self, url: str) -> bool:
        """Validate if URL is supported."""
        try:
            parsed = urlparse(url)
            # Check if URL has valid scheme and netloc
            if not all([parsed.scheme, parsed.netloc]):
                return False
            # Check if domain is supported
            domain = re.sub(r"^www\.", "", parsed.netloc.lower())
            return domain in self.VALID_DOMAINS
        except Exception:
            return False

    async def start_download(self, url: str, download_id: str) -> None:
        """Start a new download."""
        if len(self.active_downloads) >= self.max_concurrent_downloads:
            raise ValueError("Maximum concurrent downloads reached")

        if not await self.validate_url(url):
            raise ValueError("Invalid or unsupported URL")

        self.active_downloads[download_id] = {"url": url, "status": DownloadStatus.DOWNLOADING, "error": None}

    def get_download_status(self, download_id: str) -> DownloadStatus | None:
        """Get status of a download."""
        if download_id not in self.active_downloads:
            return None
        return self.active_downloads[download_id]["status"]

    async def mark_download_complete(self, download_id: str) -> None:
        """Mark a download as complete."""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]["status"] = DownloadStatus.COMPLETED

    async def mark_download_failed(self, download_id: str, error: str) -> None:
        """Mark a download as failed."""
        if download_id in self.active_downloads:
            self.active_downloads[download_id].update({"status": DownloadStatus.FAILED, "error": error})
