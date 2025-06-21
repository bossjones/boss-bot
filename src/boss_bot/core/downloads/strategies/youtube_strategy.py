"""YouTube download strategy with CLI/API choice."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.handlers.youtube_handler import YouTubeHandler
from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy

if TYPE_CHECKING:
    from boss_bot.core.downloads.clients import AsyncYtDlp

logger = logging.getLogger(__name__)


class YouTubeDownloadStrategy(BaseDownloadStrategy):
    """Strategy for YouTube downloads with CLI/API choice.

    This strategy implements the choice between CLI (existing YouTubeHandler)
    and API-direct (AsyncYtDlp) approaches based on feature flags.
    """

    def __init__(self, feature_flags: DownloadFeatureFlags, download_dir: Path):
        """Initialize YouTube strategy.

        Args:
            feature_flags: Feature flags for download implementation choice
            download_dir: Directory where downloads should be saved
        """
        # Initialize with internal variable to allow property override
        self._download_dir = download_dir
        self.feature_flags = feature_flags

        # ✅ Keep existing handler (no changes to existing functionality)
        self.cli_handler = YouTubeHandler(download_dir=download_dir)

        # 🆕 New API client (lazy loaded only when needed)
        self._api_client: AsyncYtDlp | None = None

    @property
    def download_dir(self) -> Path:
        """Get current download directory."""
        return self._download_dir

    @download_dir.setter
    def download_dir(self, value: Path) -> None:
        """Set download directory and invalidate API client to force recreation."""
        self._download_dir = value
        # Update CLI handler download directory
        self.cli_handler.download_dir = value
        # Invalidate API client so it gets recreated with new directory
        self._api_client = None

    @property
    def api_client(self) -> AsyncYtDlp:
        """Lazy load API client only when needed."""
        if self._api_client is None:
            from boss_bot.core.downloads.clients import AsyncYtDlp

            # Configure client for YouTube downloads with quality selection
            config = {
                "format": "best[height<=720]",  # Default to 720p
                "writeinfojson": True,  # Write metadata JSON
                "writedescription": True,  # Write description
                "writethumbnail": True,  # Write thumbnail
                "noplaylist": True,  # Single video by default
                "retries": 3,  # Retry on failure
                "fragment_retries": 3,  # Retry fragments
                "merge_output_format": "mp4",  # Prefer mp4 format
            }

            self._api_client = AsyncYtDlp(
                config=config,
                output_dir=self.download_dir,
            )

        return self._api_client

    @api_client.setter
    def api_client(self, client: AsyncYtDlp) -> None:
        """Set API client (for testing).

        Args:
            client: AsyncYtDlp client instance
        """
        self._api_client = client

    @api_client.deleter
    def api_client(self) -> None:
        """Delete API client (for testing cleanup)."""
        self._api_client = None

    @property
    def platform_name(self) -> str:
        """Get platform name for this strategy.

        Returns:
            Platform name
        """
        return "youtube"

    def supports_url(self, url: str) -> bool:
        """Check if this strategy supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if URL is supported by YouTube handler
        """
        return self.cli_handler.supports_url(url)

    async def download(self, url: str, **kwargs) -> MediaMetadata:
        """Download using feature-flagged approach.

        Args:
            url: YouTube URL to download
            **kwargs: Additional download options (quality, format, etc.)

        Returns:
            MediaMetadata with download results
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by YouTube strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_youtube:
            try:
                return await self._download_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"YouTube API download failed, falling back to CLI: {e}")
                    return await self._download_via_cli(url, **kwargs)
                raise
        else:
            return await self._download_via_cli(url, **kwargs)

    async def get_metadata(self, url: str, **kwargs) -> MediaMetadata:
        """Get metadata using feature-flagged approach.

        Args:
            url: YouTube URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata with extracted information
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by YouTube strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_youtube:
            try:
                return await self._get_metadata_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"YouTube API metadata failed, falling back to CLI: {e}")
                    return await self._get_metadata_via_cli(url, **kwargs)
                raise
        else:
            return await self._get_metadata_via_cli(url, **kwargs)

    async def _download_via_cli(self, url: str, **kwargs) -> MediaMetadata:
        """Use existing CLI handler (unchanged).

        Args:
            url: YouTube URL to download
            **kwargs: Download options

        Returns:
            MediaMetadata from CLI handler
        """
        # ✅ Call existing handler in executor to maintain async interface
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.cli_handler.download, url, **kwargs)

        # Convert DownloadResult to MediaMetadata
        if result.success and result.metadata:
            return result.metadata
        elif result.success:
            # Create basic metadata if download succeeded but no metadata extracted
            return MediaMetadata(
                platform="youtube",
                url=url,
                files=result.files,
            )
        else:
            raise RuntimeError(f"CLI download failed: {result.error}")

    async def _get_metadata_via_cli(self, url: str, **kwargs) -> MediaMetadata:
        """Get metadata using CLI handler.

        Args:
            url: YouTube URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata from CLI handler
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cli_handler.get_metadata, url, **kwargs)

    async def _download_via_api(self, url: str, **kwargs) -> MediaMetadata:
        """Use new API client.

        Args:
            url: YouTube URL to download
            **kwargs: Download options

        Returns:
            MediaMetadata from API client
        """
        # Update client configuration with download options
        download_options = {}

        # Quality selection
        quality = kwargs.get("quality", "720p")
        audio_only = kwargs.get("audio_only", False)

        if audio_only:
            download_options.update(
                {
                    "format": "bestaudio",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": kwargs.get("audio_format", "mp3"),
                            "preferredquality": kwargs.get("audio_quality", "192"),
                        }
                    ],
                }
            )
        else:
            if quality == "best":
                download_options["format"] = "best"
            elif quality == "worst":
                download_options["format"] = "worst"
            elif quality in ["4K", "2160p"]:
                download_options["format"] = "best[height<=2160]"
            elif quality in ["1440p", "2K"]:
                download_options["format"] = "best[height<=1440]"
            elif quality in ["1080p", "FHD"]:
                download_options["format"] = "best[height<=1080]"
            elif quality in ["720p", "HD"]:
                download_options["format"] = "best[height<=720]"
            elif quality in ["480p"]:
                download_options["format"] = "best[height<=480]"
            elif quality in ["360p"]:
                download_options["format"] = "best[height<=360]"

        async with self.api_client as client:
            # Download and convert API response to MediaMetadata
            async for item in client.download(url, **download_options):
                return self._convert_api_response_to_metadata(item)

        # If no results, raise an error
        raise RuntimeError("No download results from YouTube API")

    async def _get_metadata_via_api(self, url: str, **kwargs) -> MediaMetadata:
        """Get metadata using API client.

        Args:
            url: YouTube URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata from API client
        """
        async with self.api_client as client:
            # Extract metadata and convert to MediaMetadata
            async for item in client.extract_metadata(url):
                return self._convert_api_response_to_metadata(item)

        # If no results, raise an error
        raise RuntimeError("No metadata results from YouTube API")

    def _convert_api_response_to_metadata(self, api_response: dict[str, Any]) -> MediaMetadata:
        """Convert API response to MediaMetadata object.

        Args:
            api_response: Raw response from AsyncYtDlp

        Returns:
            MediaMetadata object with parsed information
        """
        # Handle uploader field
        uploader = api_response.get("uploader", "Unknown")
        if isinstance(uploader, dict):
            uploader = uploader.get("name", "Unknown")

        return MediaMetadata(
            platform="youtube",
            url=api_response.get("url", ""),
            title=api_response.get("title", ""),
            uploader=uploader,
            upload_date=api_response.get("upload_date", ""),
            duration=api_response.get("duration"),
            view_count=api_response.get("view_count"),
            like_count=api_response.get("like_count"),
            description=api_response.get("description", ""),
            thumbnail_url=api_response.get("thumbnail", ""),
            filename=api_response.get("filename", ""),
            raw_metadata=api_response.get("raw_metadata", api_response),
        )

    def __repr__(self) -> str:
        """String representation."""
        api_enabled = self.feature_flags.use_api_youtube
        fallback_enabled = self.feature_flags.api_fallback_to_cli

        return (
            f"YouTubeDownloadStrategy("
            f"api_enabled={api_enabled}, "
            f"fallback={fallback_enabled}, "
            f"download_dir={self.download_dir}"
            f")"
        )
