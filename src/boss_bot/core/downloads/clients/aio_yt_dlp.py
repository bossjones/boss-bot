"""Asynchronous wrapper around yt-dlp for video downloads."""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AsyncYtDlp:
    """Asynchronous wrapper around yt-dlp.

    This class provides an async interface to yt-dlp operations,
    running them in a thread pool to avoid blocking the event loop.

    Based on the same patterns as AsyncGalleryDL but adapted for yt-dlp.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_file: Path | None = None,
        cookies_file: Path | None = None,
        output_dir: Path | None = None,
        **kwargs,
    ):
        """Initialize AsyncYtDlp client.

        Args:
            config: yt-dlp configuration dictionary
            config_file: Path to yt-dlp config file
            cookies_file: Path to cookies file
            output_dir: Output directory for downloads
            **kwargs: Additional yt-dlp options
        """
        self.config = config or {}
        self.config_file = config_file
        self.cookies_file = cookies_file
        self.output_dir = output_dir
        self.extra_options = kwargs
        self._yt_dlp = None

    async def __aenter__(self) -> AsyncYtDlp:
        """Async context manager entry."""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self._cleanup()

    async def _initialize(self) -> None:
        """Initialize yt-dlp with configuration."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._setup_yt_dlp)

    def _setup_yt_dlp(self) -> None:
        """Setup yt-dlp instance (runs in thread pool)."""
        try:
            import yt_dlp
        except ImportError as e:
            raise ImportError("yt-dlp is required for YouTube downloads. Install it with: pip install yt-dlp") from e

        # Build yt-dlp options
        options = {
            # Default options for video quality and format
            "format": "best[height<=720]",  # Default to 720p for reasonable file sizes
            "writeinfojson": True,  # Write metadata JSON
            "writedescription": True,  # Write description
            "writethumbnail": True,  # Write thumbnail
            "noplaylist": True,  # Single video by default
            "retries": 3,  # Retry on failure
            "fragment_retries": 3,  # Retry fragments
        }

        # Add output directory
        if self.output_dir:
            options["outtmpl"] = str(self.output_dir / "%(uploader)s/%(title)s.%(ext)s")

        # Add cookies file
        if self.cookies_file:
            options["cookiefile"] = str(self.cookies_file)

        # Merge with provided config
        if self.config:
            options.update(self.config)

        # Add extra options
        options.update(self.extra_options)

        # Create yt-dlp instance
        self._yt_dlp = yt_dlp.YoutubeDL(options)

    async def _cleanup(self) -> None:
        """Cleanup yt-dlp instance."""
        if self._yt_dlp:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._close_yt_dlp)

    def _close_yt_dlp(self) -> None:
        """Close yt-dlp instance (runs in thread pool)."""
        if hasattr(self._yt_dlp, "close"):
            self._yt_dlp.close()

    async def extract_info(self, url: str, download: bool = True) -> dict[str, Any]:
        """Extract information from URL.

        Args:
            url: Video URL to extract info from
            download: Whether to download the video

        Returns:
            Dictionary with video information

        Raises:
            RuntimeError: If extraction fails
        """
        if not self._yt_dlp:
            raise RuntimeError("AsyncYtDlp not initialized. Use async context manager.")

        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(None, self._extract_info_sync, url, download)
            return result
        except Exception as e:
            logger.error(f"Failed to extract info from {url}: {e}")
            raise RuntimeError(f"yt-dlp extraction failed: {e}") from e

    def _extract_info_sync(self, url: str, download: bool) -> dict[str, Any]:
        """Synchronous info extraction (runs in thread pool)."""
        return self._yt_dlp.extract_info(url, download=download)

    async def download(self, url: str, **options) -> AsyncIterator[dict[str, Any]]:
        """Download video from URL.

        Args:
            url: Video URL to download
            **options: Additional download options

        Yields:
            Dictionary with download progress and file information
        """
        if not self._yt_dlp:
            raise RuntimeError("AsyncYtDlp not initialized. Use async context manager.")

        # Update options for this download
        if options:
            original_params = self._yt_dlp.params.copy()
            self._yt_dlp.params.update(options)

        try:
            # Extract info and download
            info = await self.extract_info(url, download=True)

            # Yield the result
            yield {
                "extractor": "youtube",
                "url": url,
                "info": info,
                "title": info.get("title", ""),
                "uploader": info.get("uploader", ""),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "filename": info.get("_filename", ""),
            }

        finally:
            # Restore original options
            if options:
                self._yt_dlp.params = original_params

    async def extract_metadata(self, url: str) -> AsyncIterator[dict[str, Any]]:
        """Extract metadata without downloading.

        Args:
            url: Video URL to extract metadata from

        Yields:
            Dictionary with video metadata
        """
        if not self._yt_dlp:
            raise RuntimeError("AsyncYtDlp not initialized. Use async context manager.")

        try:
            # Extract info without downloading
            info = await self.extract_info(url, download=False)

            # Yield metadata
            yield {
                "extractor": "youtube",
                "url": url,
                "title": info.get("title", ""),
                "uploader": info.get("uploader", ""),
                "description": info.get("description", ""),
                "duration": info.get("duration"),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "thumbnail": info.get("thumbnail", ""),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "raw_metadata": info,
            }

        except Exception as e:
            logger.error(f"Failed to extract metadata from {url}: {e}")
            raise RuntimeError(f"yt-dlp metadata extraction failed: {e}") from e

    async def get_formats(self, url: str) -> list[dict[str, Any]]:
        """Get available formats for a video.

        Args:
            url: Video URL to get formats for

        Returns:
            List of available formats

        Raises:
            RuntimeError: If format extraction fails
        """
        if not self._yt_dlp:
            raise RuntimeError("AsyncYtDlp not initialized. Use async context manager.")

        try:
            info = await self.extract_info(url, download=False)
            return info.get("formats", [])
        except Exception as e:
            logger.error(f"Failed to get formats for {url}: {e}")
            raise RuntimeError(f"yt-dlp format extraction failed: {e}") from e

    def supports_url(self, url: str) -> bool:
        """Check if yt-dlp supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if supported, False otherwise
        """
        try:
            import yt_dlp

            extractors = yt_dlp.extractor.gen_extractor_classes()

            for extractor_class in extractors:
                if hasattr(extractor_class, "suitable") and extractor_class.suitable(url):
                    return True
            return False
        except ImportError:
            return False
        except Exception:
            return False

    async def test_url(self, url: str) -> bool:
        """Test if URL can be processed by yt-dlp.

        Args:
            url: URL to test

        Returns:
            True if URL can be processed, False otherwise
        """
        if not self._yt_dlp:
            await self._initialize()

        try:
            await self.extract_info(url, download=False)
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation."""
        config_info = f"config_file={self.config_file}" if self.config_file else "no_config"
        cookies_info = f"cookies={self.cookies_file}" if self.cookies_file else "no_cookies"
        output_info = f"output_dir={self.output_dir}" if self.output_dir else "no_output_dir"

        return f"AsyncYtDlp({config_info}, {cookies_info}, {output_info})"
