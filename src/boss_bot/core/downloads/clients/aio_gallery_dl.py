"""Asynchronous wrapper around gallery-dl.

This class provides an async interface to gallery-dl operations,
running them in a thread pool to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles

from boss_bot.core.downloads.clients.config import GalleryDLConfig

logger = logging.getLogger(__name__)


class AsyncGalleryDL:
    """Asynchronous wrapper around gallery-dl.

    This class provides an async interface to gallery-dl operations,
    running them in a thread pool to avoid blocking the event loop.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_file: Path | None = None,
        cookies_file: Path | None = None,
        cookies_from_browser: str | None = None,
        download_dir: Path | None = None,
        **kwargs: Any,
    ):
        """Initialize AsyncGalleryDL client.

        Args:
            config: Instance configuration dictionary
            config_file: Path to gallery-dl config file
            cookies_file: Path to Netscape cookies file
            cookies_from_browser: Browser name to extract cookies from
            download_dir: Directory for downloads
            **kwargs: Additional configuration options
        """
        self.config = config or {}
        self.config_file = config_file or Path("~/.gallery-dl.conf").expanduser()
        self.download_dir = download_dir or Path("./downloads")
        self._executor: ThreadPoolExecutor | None = None
        self._gallery_dl_config: GalleryDLConfig | None = None

        # Apply cookie settings
        if cookies_file:
            self.config.setdefault("extractor", {})["cookies"] = str(cookies_file)
        elif cookies_from_browser:
            self.config.setdefault("extractor", {})["cookies-from-browser"] = cookies_from_browser

        # Apply download directory
        if download_dir:
            self.config.setdefault("extractor", {})["base-directory"] = str(download_dir)

        # Apply additional kwargs
        if kwargs:
            self.config.update(kwargs)

    async def __aenter__(self) -> AsyncGalleryDL:
        """Async context manager entry."""
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="gallery-dl")
        await self._load_configuration()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._executor:
            self._executor.shutdown(wait=True)

    async def _load_configuration(self) -> None:
        """Load and merge configuration from file and instance settings."""
        try:
            # Start with default configuration
            self._gallery_dl_config = GalleryDLConfig()

            # Load configuration file if it exists
            if self.config_file.exists():
                try:
                    async with aiofiles.open(self.config_file, encoding="utf-8") as f:
                        file_content = await f.read()
                        file_config = json.loads(file_content)

                    # Merge file config with default
                    self._gallery_dl_config = self._gallery_dl_config.merge_with(file_config)
                    logger.debug(f"Loaded gallery-dl config from {self.config_file}")
                except Exception as e:
                    logger.error(f"Error loading gallery-dl config from {self.config_file}: {e}")
                    # Continue with default config

            # Merge with instance config (highest priority)
            if self.config:
                self._gallery_dl_config = self._gallery_dl_config.merge_with(self.config)

            logger.debug("Gallery-dl configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing gallery-dl configuration: {e}")
            # Fall back to minimal configuration
            self._gallery_dl_config = GalleryDLConfig()

    def _get_effective_config(self) -> dict[str, Any]:
        """Get the effective configuration dictionary."""
        if self._gallery_dl_config:
            return self._gallery_dl_config.to_dict()
        return self.config

    async def extract_metadata(self, url: str, **options: Any) -> AsyncIterator[dict[str, Any]]:
        """Extract metadata from a URL asynchronously.

        Args:
            url: URL to extract metadata from
            **options: Additional options for gallery-dl

        Yields:
            Metadata dictionaries for each item found
        """

        def _extract_metadata_sync() -> list[dict[str, Any]]:
            """Synchronous metadata extraction."""
            try:
                import gallery_dl
                from gallery_dl import config, extractor

                # Apply configuration
                effective_config = self._get_effective_config()
                config.load(effective_config)

                # Apply additional options
                if options:
                    config.set(options)

                # Find and create extractor
                extr = extractor.find(url)
                if not extr:
                    raise ValueError(f"No extractor found for URL: {url}")

                # Extract metadata
                metadata_list = []
                for msg in extr:
                    if msg[0] == "url":
                        # URL message: (type, url_info)
                        url_info = msg[1]
                        metadata_list.append(url_info)

                return metadata_list

            except ImportError as e:
                raise RuntimeError(f"gallery-dl is not available: {e}") from e
            except Exception as e:
                logger.error(f"Error extracting metadata from {url}: {e}")
                raise

        # Run in executor to avoid blocking
        if not self._executor:
            raise RuntimeError("AsyncGalleryDL not initialized. Use 'async with' context manager.")

        loop = asyncio.get_event_loop()
        metadata_list = await loop.run_in_executor(self._executor, _extract_metadata_sync)

        # Yield each metadata item
        for metadata in metadata_list:
            yield metadata

    async def download(self, url: str, **options: Any) -> AsyncIterator[dict[str, Any]]:
        """Download content from URL asynchronously.

        Args:
            url: URL to download from
            **options: Additional options for gallery-dl

        Yields:
            Download result dictionaries for each item
        """

        def _download_sync() -> list[dict[str, Any]]:
            """Synchronous download operation."""
            try:
                import gallery_dl
                from gallery_dl import config, job

                # Apply configuration
                effective_config = self._get_effective_config()
                config.load(effective_config)

                # Apply additional options
                if options:
                    config.set(options)

                # Ensure download directory exists
                self.download_dir.mkdir(parents=True, exist_ok=True)

                # Create download job
                download_job = job.DownloadJob(url)

                # Collect results
                results = []

                # Hook into job to capture results
                original_handle_url = download_job.handle_url

                def capture_url_result(url_tuple):
                    """Capture URL processing results."""
                    try:
                        result = original_handle_url(url_tuple)
                        # Convert result to serializable format
                        if hasattr(url_tuple, "__dict__"):
                            result_dict = dict(url_tuple.__dict__)
                        else:
                            result_dict = {
                                "url": getattr(url_tuple, "url", str(url_tuple)),
                                "filename": getattr(url_tuple, "filename", None),
                                "extension": getattr(url_tuple, "extension", None),
                            }
                        results.append(result_dict)
                        return result
                    except Exception as e:
                        logger.error(f"Error processing URL: {e}")
                        results.append(
                            {
                                "url": str(url_tuple),
                                "error": str(e),
                                "success": False,
                            }
                        )
                        raise

                download_job.handle_url = capture_url_result

                # Run the download job
                download_job.run()

                return results

            except ImportError as e:
                raise RuntimeError(f"gallery-dl is not available: {e}") from e
            except Exception as e:
                logger.error(f"Error downloading from {url}: {e}")
                raise

        # Run in executor to avoid blocking
        if not self._executor:
            raise RuntimeError("AsyncGalleryDL not initialized. Use 'async with' context manager.")

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(self._executor, _download_sync)

        # Yield each result
        for result in results:
            yield result

    async def get_extractors(self) -> list[str]:
        """Get list of available extractors.

        Returns:
            List of extractor names
        """

        def _get_extractors_sync() -> list[str]:
            """Get extractors synchronously."""
            try:
                import gallery_dl
                from gallery_dl import extractor

                return [name for name in extractor._modules]
            except ImportError as e:
                raise RuntimeError(f"gallery-dl is not available: {e}") from e

        if not self._executor:
            raise RuntimeError("AsyncGalleryDL not initialized. Use 'async with' context manager.")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, _get_extractors_sync)

    async def test_url(self, url: str) -> bool:
        """Test if URL is supported by any extractor.

        Args:
            url: URL to test

        Returns:
            True if URL is supported, False otherwise
        """

        def _test_url_sync() -> bool:
            """Test URL synchronously."""
            try:
                import gallery_dl
                from gallery_dl import extractor

                return extractor.find(url) is not None
            except ImportError as e:
                raise RuntimeError(f"gallery-dl is not available: {e}") from e
            except Exception:
                return False

        if not self._executor:
            raise RuntimeError("AsyncGalleryDL not initialized. Use 'async with' context manager.")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, _test_url_sync)

    def supports_platform(self, platform: str) -> bool:
        """Check if platform is supported.

        Args:
            platform: Platform name (e.g., 'twitter', 'reddit')

        Returns:
            True if platform is supported
        """
        supported_platforms = {
            "twitter",
            "reddit",
            "instagram",
            "youtube",
            "tiktok",
            "imgur",
            "flickr",
            "deviantart",
            "artstation",
            "pixiv",
        }
        return platform.lower() in supported_platforms

    @property
    def config_dict(self) -> dict[str, Any]:
        """Get current configuration as dictionary."""
        return self._get_effective_config()

    def __repr__(self) -> str:
        """String representation."""
        return f"AsyncGalleryDL(config_file={self.config_file}, download_dir={self.download_dir})"
