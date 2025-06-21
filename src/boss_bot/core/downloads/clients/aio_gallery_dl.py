# pylint: disable=no-member
# pylint: disable=possibly-used-before-assignment
# pyright: reportImportCycles=false
# pyright: reportFunctionMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportInvalidTypeForm=false
# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=consider-using-with, consider-using-min-builtin
"""Asynchronous wrapper around gallery-dl.

This class provides an async interface to gallery-dl operations,
running them in a thread pool to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import tempfile
import traceback
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles

from boss_bot.core.downloads.clients.aio_gallery_dl_utils import get_default_gallery_dl_config_locations
from boss_bot.core.downloads.clients.config import GalleryDLConfig

logger = logging.getLogger(__name__)


class AsyncGalleryDL:
    """Asynchronous wrapper around gallery-dl.

    This class provides an async interface to gallery-dl operations,
    running them in a thread pool to avoid blocking the event loop.

    Configuration is loaded using gallery-dl's native config.load() function
    for maximum compatibility and automatic handling of all config file formats
    and locations. The loaded config is stored in self._gdl_config and used
    throughout the async operations in a thread-safe manner.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_file: Path | None = None,
        cookies_file: Path | None = None,
        cookies_from_browser: str | None = "Firefox",
        download_dir: Path | None = None,
        mtime: bool = False,
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
        self._gdl_config: dict[str, Any] = {}  # Store gallery-dl's loaded config

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
        """Load and merge configuration using gallery-dl's native config loading."""

        def _load_config_sync() -> dict[str, Any]:
            """Synchronously load configuration using gallery-dl's config.load."""
            try:
                from gallery_dl import config as gdl_config

                # Clear any existing configuration to ensure clean state
                gdl_config.clear()

                # Load from default locations (similar to gallery-dl's behavior)
                config_files = None
                if self.config_file and self.config_file.exists():
                    # If we have a specific config file, use it
                    config_files = [str(self.config_file)]

                # Load configuration using gallery-dl's native loader
                gdl_config.load(files=config_files)

                # Get the loaded configuration
                loaded_config = gdl_config._config.copy() if gdl_config._config else {}

                logger.debug(f"loaded_config: {loaded_config}")

                # Merge with instance config (highest priority)
                if self.config:
                    # Use gallery-dl's utility function for proper merging
                    from gallery_dl import util

                    util.combine_dict(loaded_config, self.config)
                    logger.debug(
                        f"loaded_config after merge via (util.combine_dict(loaded_config, self.config): {loaded_config}"
                    )

                return loaded_config

            except ImportError as e:
                logger.error(f"gallery-dl is not available: {e}")
                # Return default config merged with instance config
                default_config = GalleryDLConfig()
                if self.config:
                    default_config = default_config.merge_with(self.config)
                return default_config.to_dict()
            except Exception as e:
                logger.error(f"Error loading gallery-dl configuration: {e}")
                # Return default config merged with instance config
                default_config = GalleryDLConfig()
                if self.config:
                    default_config = default_config.merge_with(self.config)
                return default_config.to_dict()

        try:
            # Run config loading in executor to avoid blocking
            if not self._executor:
                raise RuntimeError("AsyncGalleryDL not initialized properly")

            loop = asyncio.get_event_loop()
            self._gdl_config = await loop.run_in_executor(self._executor, _load_config_sync)

            # Update self.config with the final merged configuration from _gdl_config
            if self._gdl_config:
                self.config = self._gdl_config.copy()
                logger.debug(f"Updated self.config with merged configuration: {self.config}")

            # Also create GalleryDLConfig for validation/compatibility
            try:
                self._gallery_dl_config = (
                    GalleryDLConfig.from_dict(self._gdl_config) if self._gdl_config else GalleryDLConfig()
                )
            except Exception as e:
                logger.warning(f"Could not validate config with GalleryDLConfig: {e}")
                self._gallery_dl_config = GalleryDLConfig()

            logger.debug("Gallery-dl configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing gallery-dl configuration: {e}")
            # Fall back to default configuration merged with instance config
            default_config = GalleryDLConfig()
            if self.config:
                default_config = default_config.merge_with(self.config)
            self._gdl_config = default_config.to_dict()
            self._gallery_dl_config = default_config

            # Update self.config with the fallback configuration
            self.config = self._gdl_config.copy()
            logger.debug(f"Updated self.config with fallback configuration: {self.config}")

    def _get_effective_config(self) -> dict[str, Any]:
        """Get the effective configuration dictionary."""
        # Return the gallery-dl native config if available
        if self._gdl_config:
            return self._gdl_config
        # Fallback to GalleryDLConfig if available
        elif self._gallery_dl_config:
            return self._gallery_dl_config.to_dict()
        # Final fallback to instance config
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
                from gallery_dl import config as gdl_config
                from gallery_dl import extractor

                # Apply configuration in a thread-safe way
                effective_config = self._get_effective_config().copy()

                # Merge additional options into config before loading
                if options:
                    # Merge options into the effective config copy
                    if "extractor" not in effective_config:
                        effective_config["extractor"] = {}
                    effective_config["extractor"].update(options)

                # Clear and load configuration for this thread
                gdl_config.clear()

                # Load using the config dict directly instead of files
                # This is safer for thread isolation
                if effective_config:
                    # Use gallery-dl's internal combine_dict to merge into the global config
                    from gallery_dl import util

                    util.combine_dict(gdl_config._config, effective_config)

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
                from gallery_dl import config as gdl_config
                from gallery_dl import job

                # Apply configuration in a thread-safe way
                effective_config = self._get_effective_config().copy()

                # Merge additional options into config before loading
                if options:
                    # Merge options into the effective config copy
                    if "extractor" not in effective_config:
                        effective_config["extractor"] = {}
                    effective_config["extractor"].update(options)

                # Clear and load configuration for this thread
                gdl_config.clear()

                # Load using the config dict directly instead of files
                # This is safer for thread isolation
                if effective_config:
                    # Use gallery-dl's internal combine_dict to merge into the global config
                    from gallery_dl import util

                    util.combine_dict(gdl_config._config, effective_config)

                # Ensure download directory exists
                self.download_dir.mkdir(parents=True, exist_ok=True)

                # Create download job
                download_job = job.DownloadJob(url)

                # Collect results
                results = []

                # Hook into job to capture results
                original_handle_url = download_job.handle_url

                def capture_url_result(url_tuple, kwdict):
                    """Capture URL processing results."""
                    try:
                        result = original_handle_url(url_tuple, kwdict)
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
                print(f"{e}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print(f"Error Class: {e.__class__}")
                output = f"[UNEXPECTED] {type(e).__name__}: {e}"
                print(output)
                print(f"exc_type: {exc_type}")
                print(f"exc_value: {exc_value}")
                traceback.print_tb(exc_traceback)
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

                # Try different ways to get extractor names
                if hasattr(extractor, "modules") and isinstance(extractor.modules, list):
                    return extractor.modules
                elif hasattr(extractor, "_modules"):
                    return [name for name in extractor._modules]
                else:
                    # Fallback: get all extractor classes
                    extractors = []
                    for name in dir(extractor):
                        obj = getattr(extractor, name)
                        if isinstance(obj, type) and hasattr(obj, "pattern") and name.endswith("Extractor"):
                            extractors.append(name.replace("Extractor", "").lower())
                    return extractors
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
