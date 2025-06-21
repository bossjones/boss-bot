"""Instagram download strategy with CLI/API choice."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from boss_bot.core.downloads.clients.config.gallery_dl_validator import InstagramConfigValidator
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.handlers.instagram_handler import InstagramHandler
from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy

if TYPE_CHECKING:
    from boss_bot.core.downloads.clients import AsyncGalleryDL

logger = logging.getLogger(__name__)


class InstagramDownloadStrategy(BaseDownloadStrategy):
    """Strategy for Instagram downloads with CLI/API choice.

    This strategy implements the choice between CLI (existing InstagramHandler)
    and API-direct (AsyncGalleryDL) approaches based on feature flags.
    """

    def __init__(self, feature_flags: DownloadFeatureFlags, download_dir: Path):
        """Initialize Instagram strategy.

        Args:
            feature_flags: Feature flags for download implementation choice
            download_dir: Directory where downloads should be saved
        """
        # Initialize with internal variable to allow property override
        self._download_dir = download_dir
        self.feature_flags = feature_flags

        # ✅ Keep existing handler (no changes to existing functionality)
        self.cli_handler = InstagramHandler(download_dir=download_dir)

        # 🆕 New API client (lazy loaded only when needed)
        self._api_client: AsyncGalleryDL | None = None

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
    def api_client(self) -> AsyncGalleryDL:
        """Lazy load API client only when needed."""
        if self._api_client is None:
            from boss_bot.core.downloads.clients import AsyncGalleryDL

            # Configure client for Instagram downloads with specific settings
            # Based on the user's CLI command preferences
            config = {
                "extractor": {
                    "base-directory": str(self.download_dir),
                    "archive": f"{self.download_dir}/.archive.sqlite3",
                    "path-restrict": "auto",
                    "path-extended": True,
                    "instagram": {
                        "videos": True,
                        "include": "all",
                        "highlights": False,  # Don't download highlights by default
                        "stories": False,  # Don't download stories by default
                        "filename": "{username}_{shortcode}_{num}.{extension}",
                        "directory": ["instagram", "{username}"],
                        "sleep-request": 8.0,
                        "cookies-from-browser": "firefox",  # Use Firefox cookies by default
                        "user-agent": "Wget/1.21.1",  # Specific user agent for Instagram
                    },
                },
                "downloader": {
                    "retries": 4,
                    "timeout": 30.0,
                    "part": True,
                },
                "output": {
                    "progress": True,
                    "mode": "auto",
                },
            }

            self._api_client = AsyncGalleryDL(config=config, download_dir=self.download_dir)
        return self._api_client

    @api_client.setter
    def api_client(self, value: AsyncGalleryDL | None) -> None:
        """Set the API client (for testing purposes)."""
        self._api_client = value

    @api_client.deleter
    def api_client(self) -> None:
        """Delete the API client (for testing cleanup)."""
        self._api_client = None

    @property
    def platform_name(self) -> str:
        """Get platform name for this strategy."""
        return "instagram"

    def supports_url(self, url: str) -> bool:
        """Check if strategy supports URL.

        Args:
            url: URL to check

        Returns:
            True if URL is an Instagram URL
        """
        return self.cli_handler.supports_url(url)

    def validate_config(self, config: dict[str, Any] | None = None, verbose: bool = False) -> tuple[bool, list[str]]:
        """Validate Instagram configuration.

        Args:
            config: Configuration to validate. If None, loads from gallery-dl.
            verbose: If True, prints detailed validation information

        Returns:
            Tuple of (is_valid, issues_list)
        """
        try:
            result = InstagramConfigValidator.validate_config(config)
            if verbose:
                if result.is_valid:
                    print("✅ Instagram configuration is valid")
                else:
                    print("❌ Instagram configuration has issues:")
                    for issue in result.issues:
                        print(f"  - {issue}")
            return result.is_valid, result.issues
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False, [f"Validation error: {e}"]

    def check_config(self, verbose: bool = False) -> bool:
        """Check Instagram configuration with detailed output.

        Args:
            verbose: If True, prints detailed configuration check

        Returns:
            True if configuration is valid
        """
        try:
            return InstagramConfigValidator.check_instagram_config(verbose=verbose)
        except Exception as e:
            logger.error(f"Configuration check failed: {e}")
            if verbose:
                print(f"❌ Configuration check failed: {e}")
            return False

    def print_config_summary(self) -> None:
        """Print current Instagram configuration summary."""
        try:
            InstagramConfigValidator.print_config_summary()
        except Exception as e:
            logger.error(f"Failed to print config summary: {e}")
            print(f"❌ Failed to print config summary: {e}")

    async def download(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Download using feature-flagged approach.

        Args:
            url: Instagram URL to download from
            **kwargs: Additional download options

        Returns:
            MediaMetadata object with download results

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If download fails and no fallback is available
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by Instagram strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_instagram:
            try:
                logger.info(f"Using API-direct approach for Instagram download: {url}")
                return await self._download_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"API download failed, falling back to CLI: {e}")
                    return await self._download_via_cli(url, **kwargs)
                logger.error(f"API download failed with no fallback: {e}")
                raise
        else:
            logger.info(f"Using CLI approach for Instagram download: {url}")
            return await self._download_via_cli(url, **kwargs)

    async def get_metadata(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Get metadata using feature-flagged approach.

        Args:
            url: Instagram URL to get metadata from
            **kwargs: Additional metadata options

        Returns:
            MediaMetadata object with metadata

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If metadata extraction fails
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by Instagram strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_instagram:
            try:
                logger.info(f"Using API-direct approach for Instagram metadata: {url}")
                return await self._get_metadata_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"API metadata extraction failed, falling back to CLI: {e}")
                    return await self._get_metadata_via_cli(url, **kwargs)
                logger.error(f"API metadata extraction failed with no fallback: {e}")
                raise
        else:
            logger.info(f"Using CLI approach for Instagram metadata: {url}")
            return await self._get_metadata_via_cli(url, **kwargs)

    async def _download_via_cli(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Use existing CLI handler (unchanged).

        Args:
            url: URL to download
            **kwargs: Additional options

        Returns:
            MediaMetadata from CLI handler
        """
        # ✅ Call existing handler in executor to maintain async interface
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cli_handler.download, url, **kwargs)

    async def _get_metadata_via_cli(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Use existing CLI handler for metadata (unchanged).

        Args:
            url: URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata from CLI handler
        """
        # ✅ Call existing handler in executor to maintain async interface
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cli_handler.get_metadata, url, **kwargs)

    async def _download_via_api(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Use new API client for download.

        Args:
            url: URL to download
            **kwargs: Additional options

        Returns:
            MediaMetadata converted from API response
        """
        async with self.api_client as client:
            # Collect download results
            results = []
            async for item in client.download(url, **kwargs):
                results.append(item)

            if not results:
                raise RuntimeError(f"No content downloaded from {url}")

            # Convert first result to MediaMetadata
            return self._convert_api_response_to_metadata(results[0], url)

    async def _get_metadata_via_api(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Use new API client for metadata extraction.

        Args:
            url: URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata converted from API response
        """
        async with self.api_client as client:
            # Extract metadata
            metadata_items = []
            async for item in client.extract_metadata(url, **kwargs):
                metadata_items.append(item)

            if not metadata_items:
                raise RuntimeError(f"No metadata extracted from {url}")

            # Convert first metadata item to MediaMetadata
            return self._convert_api_response_to_metadata(metadata_items[0], url)

    def _convert_api_response_to_metadata(self, api_response: dict, url: str) -> MediaMetadata:
        """Convert API response to MediaMetadata format.

        Args:
            api_response: Response from gallery-dl API
            url: Original URL

        Returns:
            MediaMetadata object
        """
        # Extract common fields from gallery-dl response
        title = api_response.get("description") or api_response.get("title", "Instagram Content")
        author = api_response.get("uploader") or api_response.get("username", "Unknown")

        # Handle author field (can be string or dict)
        if isinstance(author, dict):
            author_name = author.get("username") or author.get("full_name") or "Unknown"
        else:
            author_name = str(author)

        # Extract file information
        filename = api_response.get("filename")
        if not filename and "url" in api_response:
            # Generate filename from URL if not provided
            import os

            filename = os.path.basename(api_response["url"]) or "instagram_content"

        # Extract Instagram-specific metadata
        upload_date = api_response.get("upload_date") or api_response.get("date")
        like_count = api_response.get("like_count")
        view_count = api_response.get("view_count") or api_response.get("video_view_count")
        comment_count = api_response.get("comment_count")
        post_type = api_response.get("typename") or api_response.get("media_type", "post")
        shortcode = api_response.get("shortcode")
        is_video = api_response.get("is_video", False)

        return MediaMetadata(
            url=url,
            title=title,
            author=author_name,
            platform="instagram",
            filename=filename,
            filesize=api_response.get("filesize"),
            duration=api_response.get("duration"),
            upload_date=upload_date,
            view_count=view_count,
            like_count=like_count,
            description=api_response.get("description"),
            thumbnail_url=api_response.get("thumbnail"),
            download_method="api",  # Mark as API download
            # Instagram-specific metadata
            raw_metadata={
                "post_type": post_type,
                "comment_count": comment_count,
                "is_video": is_video,
                "shortcode": shortcode,
                "post_id": api_response.get("id"),
                "owner": api_response.get("owner", {}).get("username") if api_response.get("owner") else None,
            },
        )

    def __repr__(self) -> str:
        """String representation."""
        api_enabled = self.feature_flags.use_api_instagram
        fallback_enabled = self.feature_flags.api_fallback_to_cli
        return (
            f"InstagramDownloadStrategy("
            f"api_enabled={api_enabled}, "
            f"fallback_enabled={fallback_enabled}, "
            f"download_dir={self.download_dir}"
            f")"
        )
