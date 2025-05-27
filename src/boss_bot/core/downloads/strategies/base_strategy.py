"""Base strategy interface for download implementations."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


class BaseDownloadStrategy(abc.ABC):
    """Strategy interface for choosing download implementation.

    This abstract base class defines the interface for download strategies
    that can choose between CLI and API implementations based on feature flags.
    """

    def __init__(self, download_dir: Path):
        """Initialize strategy with download directory.

        Args:
            download_dir: Directory where downloads should be saved
        """
        self.download_dir = download_dir

    @abc.abstractmethod
    async def download(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Download using chosen strategy (CLI or API).

        Args:
            url: URL to download from
            **kwargs: Additional download options

        Returns:
            MediaMetadata object with download results

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If download fails and no fallback is available
        """
        pass

    @abc.abstractmethod
    async def get_metadata(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Get metadata using chosen strategy (CLI or API).

        Args:
            url: URL to get metadata from
            **kwargs: Additional metadata options

        Returns:
            MediaMetadata object with metadata

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If metadata extraction fails
        """
        pass

    @abc.abstractmethod
    def supports_url(self, url: str) -> bool:
        """Check if strategy supports URL.

        Args:
            url: URL to check

        Returns:
            True if URL is supported by this strategy
        """
        pass

    @property
    @abc.abstractmethod
    def platform_name(self) -> str:
        """Get platform name for this strategy.

        Returns:
            Platform name (e.g., 'twitter', 'reddit')
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(platform={self.platform_name}, download_dir={self.download_dir})"
