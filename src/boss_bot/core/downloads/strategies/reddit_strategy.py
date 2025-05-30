"""Reddit download strategy with CLI/API choice."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
from boss_bot.core.downloads.handlers.reddit_handler import RedditHandler
from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy

if TYPE_CHECKING:
    from boss_bot.core.downloads.clients import AsyncGalleryDL
    from boss_bot.core.downloads.handlers.base_handler import DownloadResult

logger = logging.getLogger(__name__)


class RedditDownloadStrategy(BaseDownloadStrategy):
    """Strategy for Reddit downloads with CLI/API choice.

    This strategy implements the choice between CLI (existing RedditHandler)
    and API-direct (AsyncGalleryDL) approaches based on feature flags.
    """

    def __init__(self, feature_flags: DownloadFeatureFlags, download_dir: Path):
        """Initialize Reddit strategy.

        Args:
            feature_flags: Feature flags for download implementation choice
            download_dir: Directory where downloads should be saved
        """
        super().__init__(download_dir)
        self.feature_flags = feature_flags

        # ✅ Keep existing handler (no changes to existing functionality)
        self.cli_handler = RedditHandler(download_dir=download_dir)

        # 🆕 New API client (lazy loaded only when needed)
        self._api_client: AsyncGalleryDL | None = None

    @property
    def api_client(self) -> AsyncGalleryDL:
        """Lazy load API client only when needed."""
        if self._api_client is None:
            from boss_bot.core.downloads.clients import AsyncGalleryDL

            # Configure client for Reddit downloads
            config = {
                "extractor": {
                    "base-directory": str(self.download_dir),
                    "reddit": {
                        "comments": 0,
                        "morecomments": False,
                        "date-min": 0,
                        "date-max": 253402210800,
                        "recursion": 0,
                        "videos": True,
                    },
                }
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
        return "reddit"

    def supports_url(self, url: str) -> bool:
        """Check if strategy supports URL.

        Args:
            url: URL to check

        Returns:
            True if URL is a Reddit URL
        """
        return self.cli_handler.supports_url(url)

    async def download(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Download using feature-flagged approach.

        Args:
            url: Reddit URL to download from
            **kwargs: Additional download options

        Returns:
            MediaMetadata object with download results

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If download fails and no fallback is available
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by Reddit strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_reddit:
            try:
                logger.info(f"Using API-direct approach for Reddit download: {url}")
                return await self._download_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"API download failed, falling back to CLI: {e}")
                    return await self._download_via_cli(url, **kwargs)
                logger.error(f"API download failed with no fallback: {e}")
                raise
        else:
            logger.info(f"Using CLI approach for Reddit download: {url}")
            return await self._download_via_cli(url, **kwargs)

    async def get_metadata(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Get metadata using feature-flagged approach.

        Args:
            url: Reddit URL to get metadata from
            **kwargs: Additional metadata options

        Returns:
            MediaMetadata object with metadata

        Raises:
            ValueError: If URL is not supported
            RuntimeError: If metadata extraction fails
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by Reddit strategy: {url}")

        # Feature flag: choose implementation
        if self.feature_flags.use_api_reddit:
            try:
                logger.info(f"Using API-direct approach for Reddit metadata: {url}")
                return await self._get_metadata_via_api(url, **kwargs)
            except Exception as e:
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"API metadata extraction failed, falling back to CLI: {e}")
                    return await self._get_metadata_via_cli(url, **kwargs)
                logger.error(f"API metadata extraction failed with no fallback: {e}")
                raise
        else:
            logger.info(f"Using CLI approach for Reddit metadata: {url}")
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
        download_result = await loop.run_in_executor(None, self.cli_handler.download, url, **kwargs)

        # Convert DownloadResult to MediaMetadata
        return self._convert_download_result_to_metadata(download_result, url)

    async def _get_metadata_via_cli(self, url: str, **kwargs: Any) -> MediaMetadata:
        """Use existing CLI handler for metadata (unchanged).

        Args:
            url: URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata from CLI handler

        Raises:
            RuntimeError: If metadata extraction fails
        """
        # ✅ Call existing handler in executor to maintain async interface
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(None, self.cli_handler.get_metadata, url, **kwargs)

        if metadata is None:
            raise RuntimeError(f"Failed to extract metadata from {url} using CLI handler")

        return metadata

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

    def _convert_download_result_to_metadata(self, download_result: DownloadResult, url: str) -> MediaMetadata:
        """Convert DownloadResult to MediaMetadata format.

        Args:
            download_result: Result from handler download
            url: Original URL

        Returns:
            MediaMetadata with download information
        """
        from boss_bot.core.downloads.handlers.base_handler import MediaMetadata

        if not download_result.success:
            return MediaMetadata(url=url, platform="reddit", download_method="cli", error=download_result.error)

        # Extract metadata from files if available
        metadata_dict = download_result.metadata or {}

        # Build MediaMetadata with file information
        return MediaMetadata(
            title=metadata_dict.get("title"),
            description=metadata_dict.get("description"),
            uploader=metadata_dict.get("uploader") or metadata_dict.get("author"),
            upload_date=metadata_dict.get("upload_date"),
            duration=metadata_dict.get("duration"),
            view_count=metadata_dict.get("view_count"),
            like_count=metadata_dict.get("like_count") or metadata_dict.get("score"),
            comment_count=metadata_dict.get("comment_count") or metadata_dict.get("num_comments"),
            url=url,
            thumbnail=metadata_dict.get("thumbnail"),
            platform="reddit",
            file_size=metadata_dict.get("file_size"),
            format=metadata_dict.get("format"),
            tags=metadata_dict.get("tags"),
            raw_metadata=metadata_dict,
            download_method="cli",
            filename=str(download_result.files[0]) if download_result.files else None,
            files=[str(f) for f in download_result.files] if download_result.files else [],
        )

    def _convert_api_response_to_metadata(self, api_response: dict, url: str) -> MediaMetadata:
        """Convert API response to MediaMetadata format.

        Args:
            api_response: Response from gallery-dl API
            url: Original URL

        Returns:
            MediaMetadata object
        """
        # Extract common fields from gallery-dl response
        title = api_response.get("title") or api_response.get("description", "Reddit Content")
        author = api_response.get("uploader") or api_response.get("author", "Unknown")

        # Handle author field (can be string or dict)
        if isinstance(author, dict):
            author_name = author.get("name") or author.get("username") or "Unknown"
        else:
            author_name = str(author)

        # Extract file information
        filename = api_response.get("filename")
        if not filename and "url" in api_response:
            # Generate filename from URL if not provided
            import os

            filename = os.path.basename(api_response["url"]) or "reddit_content"

        # Extract Reddit-specific metadata
        upload_date = api_response.get("upload_date") or api_response.get("date")
        subreddit = api_response.get("subreddit")
        score = api_response.get("score")  # Reddit upvotes
        num_comments = api_response.get("num_comments")

        # Map Reddit score to like_count for consistency
        like_count = score

        return MediaMetadata(
            url=url,
            title=title,
            author=author_name,
            platform="reddit",
            filename=filename,
            filesize=api_response.get("filesize"),
            duration=api_response.get("duration"),
            upload_date=upload_date,
            view_count=None,  # Reddit doesn't typically provide view counts
            like_count=like_count,
            description=api_response.get("description") or api_response.get("selftext"),
            thumbnail_url=api_response.get("thumbnail"),
            download_method="api",  # Mark as API download
            # Reddit-specific metadata
            raw_metadata={
                "subreddit": subreddit,
                "score": score,
                "num_comments": num_comments,
                "permalink": api_response.get("permalink"),
                "post_id": api_response.get("id"),
            },
        )

    def __repr__(self) -> str:
        """String representation."""
        api_enabled = self.feature_flags.use_api_reddit
        fallback_enabled = self.feature_flags.api_fallback_to_cli
        return (
            f"RedditDownloadStrategy("
            f"api_enabled={api_enabled}, "
            f"fallback_enabled={fallback_enabled}, "
            f"download_dir={self.download_dir}"
            f")"
        )
