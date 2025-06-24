"""YouTube download strategy with CLI/API choice."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

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
        logger.debug(f"Initializing YouTubeDownloadStrategy with download_dir={download_dir}")
        logger.debug(
            f"Feature flags: api_enabled={feature_flags.use_api_youtube}, fallback_enabled={feature_flags.api_fallback_to_cli}"
        )
        # Initialize with internal variable to allow property override
        self._download_dir = download_dir
        self.feature_flags = feature_flags

        # ✅ Keep existing handler (no changes to existing functionality)
        logger.debug("Initializing CLI handler (YouTubeHandler)")
        self.cli_handler = YouTubeHandler(download_dir=download_dir)

        # 🆕 New API client (lazy loaded only when needed)
        self._api_client: AsyncYtDlp | None = None
        logger.debug("YouTube strategy initialization complete")

    @property
    def download_dir(self) -> Path:
        """Get current download directory."""
        return self._download_dir

    @download_dir.setter
    def download_dir(self, value: Path) -> None:
        """Set download directory and invalidate API client to force recreation."""
        logger.debug(f"Updating download directory from {self._download_dir} to {value}")
        self._download_dir = value
        # Update CLI handler download directory
        self.cli_handler.download_dir = value
        logger.debug("Updated CLI handler download directory")
        # Invalidate API client so it gets recreated with new directory
        if self._api_client is not None:
            logger.debug("Invalidating API client due to directory change")
        self._api_client = None

    def _get_youtube_config(self) -> dict[str, Any]:
        """Get optimized yt-dlp configuration for Discord workflow."""
        logger.debug(f"Generating yt-dlp configuration for download_dir={self.download_dir}")
        config = {
            # Directory structure using yt-dlp's built-in outtmpl
            "outtmpl": {
                "default": f"{self.download_dir}/yt-dlp/youtube/%(uploader|Unknown)s/%(title).100s-%(id)s.%(ext)s",
                "infojson": f"{self.download_dir}/yt-dlp/youtube/%(uploader|Unknown)s/%(title).100s-%(id)s.info.json",
                "thumbnail": f"{self.download_dir}/yt-dlp/youtube/%(uploader|Unknown)s/%(title).100s-%(id)s.%(ext)s",
                "description": f"{self.download_dir}/yt-dlp/youtube/%(uploader|Unknown)s/%(title).100s-%(id)s.description",
            },
            # Quality ladder optimized for Discord limits (25MB default, 50MB boost)
            "format": "best[height<=720][filesize<50M]/best[height<=480][filesize<25M]/best[height<=360][filesize<10M]",
            # Metadata preservation
            "writeinfojson": True,
            "writedescription": True,
            "writethumbnail": True,
            "writesubtitles": False,  # Skip subtitles for Discord uploads
            # Performance optimization
            "noplaylist": True,
            "ignoreerrors": False,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 120,
            "read_timeout": 300,
            # Discord-friendly video settings
            "merge_output_format": "mp4",
            "postprocessor_args": ["-movflags", "+faststart"],  # Web-optimized MP4
        }
        logger.debug(f"Generated yt-dlp config with outtmpl: {config['outtmpl']['default']}")
        logger.debug(f"Format selector: {config['format']}")
        return config

    @property
    def api_client(self) -> AsyncYtDlp:
        """Lazy load API client only when needed."""
        if self._api_client is None:
            logger.debug("Creating new AsyncYtDlp API client")
            from boss_bot.core.downloads.clients import AsyncYtDlp

            # Use enhanced configuration
            config = self._get_youtube_config()
            logger.debug(f"API client config keys: {list(config.keys())}")

            self._api_client = AsyncYtDlp(
                config=config,
                output_dir=self.download_dir,
            )
            logger.debug(f"AsyncYtDlp client created with output_dir={self.download_dir}")
        else:
            logger.debug("Reusing existing AsyncYtDlp API client")

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
        """Download using feature-flagged approach with deduplication.

        Args:
            url: YouTube URL to download
            **kwargs: Additional download options (quality, format, force_redownload, etc.)

        Returns:
            MediaMetadata with download results
        """
        logger.debug(f"Starting YouTube download for URL: {url}")
        logger.debug(f"Download options: {kwargs}")
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by YouTube strategy: {url}")

        # Check for duplicates unless force_redownload is specified
        logger.debug("Checking for duplicate downloads")
        duplicate_check = self._check_deduplication(url, **kwargs)
        if duplicate_check:
            logger.info(f"Skipping duplicate download: {url}")
            return duplicate_check

        # Feature flag: choose implementation with performance tracking
        logger.debug(
            f"Selecting download method - API enabled: {self.feature_flags.use_api_youtube}, Fallback enabled: {self.feature_flags.api_fallback_to_cli}"
        )
        start_time = time.time()
        download_method = "unknown"

        try:
            if self.feature_flags.use_api_youtube:
                try:
                    logger.debug("Attempting API-based download")
                    download_method = "api"
                    metadata = await self._download_via_api(url, **kwargs)
                    logger.debug("API download successful")
                except Exception as e:
                    logger.debug(f"API download failed: {e}")
                    if self.feature_flags.api_fallback_to_cli:
                        logger.warning(f"YouTube API download failed, falling back to CLI: {e}")
                        logger.debug("Attempting CLI fallback")
                        download_method = "cli_fallback"
                        metadata = await self._download_via_cli(url, **kwargs)
                        logger.debug("CLI fallback successful")
                    else:
                        logger.error("API download failed and fallback disabled")
                        raise
            else:
                logger.debug("Using CLI-based download (API disabled)")
                download_method = "cli"
                metadata = await self._download_via_cli(url, **kwargs)
                logger.debug("CLI download successful")

            # Add performance metrics to metadata
            download_duration = time.time() - start_time
            metadata.download_method = download_method

            # Log performance metrics
            logger.info(f"YouTube download completed in {download_duration:.2f}s using {download_method} method")

            # Record successful download for deduplication
            if not metadata.error:
                video_id = self._extract_youtube_video_id(url)
                if video_id:
                    self._record_download(video_id, metadata)
                    # Store performance metrics in history
                    self._record_performance_metrics(video_id, download_duration, download_method)

            return metadata

        except Exception as e:
            # Log failed download performance
            download_duration = time.time() - start_time
            logger.error(f"YouTube download failed after {download_duration:.2f}s using {download_method} method: {e}")
            # Don't record failed downloads
            raise

    async def get_metadata(self, url: str, **kwargs) -> MediaMetadata:
        """Get metadata using feature-flagged approach.

        Args:
            url: YouTube URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata with extracted information
        """
        logger.debug(f"Getting YouTube metadata for URL: {url}")
        logger.debug(f"Metadata options: {kwargs}")
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by YouTube strategy: {url}")

        # Feature flag: choose implementation
        logger.debug(
            f"Selecting metadata method - API enabled: {self.feature_flags.use_api_youtube}, Fallback enabled: {self.feature_flags.api_fallback_to_cli}"
        )
        if self.feature_flags.use_api_youtube:
            try:
                logger.debug("Attempting API-based metadata extraction")
                metadata = await self._get_metadata_via_api(url, **kwargs)
                logger.debug("API metadata extraction successful")
                return metadata
            except Exception as e:
                logger.debug(f"API metadata extraction failed: {e}")
                if self.feature_flags.api_fallback_to_cli:
                    logger.warning(f"YouTube API metadata failed, falling back to CLI: {e}")
                    logger.debug("Attempting CLI fallback for metadata")
                    metadata = await self._get_metadata_via_cli(url, **kwargs)
                    logger.debug("CLI metadata fallback successful")
                    return metadata
                else:
                    logger.error("API metadata extraction failed and fallback disabled")
                    raise
        else:
            logger.debug("Using CLI-based metadata extraction (API disabled)")
            metadata = await self._get_metadata_via_cli(url, **kwargs)
            logger.debug("CLI metadata extraction successful")
            return metadata

    async def _download_via_cli(self, url: str, **kwargs) -> MediaMetadata:
        """Use existing CLI handler (unchanged).

        Args:
            url: YouTube URL to download
            **kwargs: Download options

        Returns:
            MediaMetadata from CLI handler
        """
        logger.debug(f"Starting CLI download for URL: {url}")
        logger.debug(f"CLI download options: {kwargs}")
        # ✅ Call existing handler in executor to maintain async interface
        loop = asyncio.get_event_loop()
        logger.debug("Executing CLI handler in thread pool")
        result = await loop.run_in_executor(None, self.cli_handler.download, url, **kwargs)
        logger.debug(f"CLI handler completed - success: {result.success}")

        # Convert DownloadResult to MediaMetadata
        if result.success and result.metadata:
            logger.debug(f"CLI download successful with metadata - title: {result.metadata.title}")
            return result.metadata
        elif result.success:
            logger.debug("CLI download successful but no metadata, creating basic metadata")
            # Create basic metadata if download succeeded but no metadata extracted
            return MediaMetadata(
                platform="youtube",
                url=url,
                files=result.files,
            )
        else:
            logger.error(f"CLI download failed: {result.error}")
            raise RuntimeError(f"CLI download failed: {result.error}")

    async def _get_metadata_via_cli(self, url: str, **kwargs) -> MediaMetadata:
        """Get metadata using CLI handler.

        Args:
            url: YouTube URL to get metadata from
            **kwargs: Additional options

        Returns:
            MediaMetadata from CLI handler
        """
        logger.debug(f"Getting metadata via CLI for URL: {url}")
        logger.debug(f"CLI metadata options: {kwargs}")
        loop = asyncio.get_event_loop()
        logger.debug("Executing CLI metadata extraction in thread pool")
        result = await loop.run_in_executor(None, self.cli_handler.get_metadata, url, **kwargs)
        logger.debug(f"CLI metadata extraction complete - title: {result.title if result else 'None'}")
        return result

    async def _download_via_api(self, url: str, **kwargs) -> MediaMetadata:
        """Use new API client with enhanced error handling.

        Args:
            url: YouTube URL to download
            **kwargs: Download options

        Returns:
            MediaMetadata from API client
        """
        return await self._download_via_api_with_fallbacks(url, **kwargs)

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

    def _sanitize_channel_name(self, uploader: str) -> str:
        """Clean channel name for filesystem compatibility.

        Args:
            uploader: Raw uploader/channel name from yt-dlp

        Returns:
            Filesystem-safe channel name

        Examples:
            "MrBeast" -> "MrBeast"
            "Channel: Name/Test" -> "Channel_Name_Test"
            "[Deleted]" -> "Unknown_Channel"
        """
        if not uploader or uploader.lower() in ["unknown", "[deleted]", "na"]:
            return "Unknown_Channel"

        # Remove/replace problematic characters for filesystem
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", uploader)
        sanitized = re.sub(r"[\[\]]", "", sanitized)  # Remove brackets
        sanitized = sanitized.strip(". ")  # Remove leading/trailing dots/spaces
        sanitized = re.sub(r"_+", "_", sanitized)  # Collapse multiple underscores

        return sanitized[:100]  # Limit length for filesystem compatibility

    def _extract_youtube_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL for fallback naming.

        Args:
            url: YouTube URL (video, shorts, embed, etc.)

        Returns:
            Video ID or None if not extractable

        Examples:
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "https://youtu.be/dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "https://www.youtube.com/shorts/iJw5lVbIwao" -> "iJw5lVbIwao"
        """
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([^&\n?#]+)",
            r"youtube\.com/embed/([^&\n?#]+)",
            r"youtube\.com/v/([^&\n?#]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _extract_channel_info_from_metadata(self, metadata: dict[str, Any]) -> tuple[str, str]:
        """Extract reliable channel information from yt-dlp metadata.

        Args:
            metadata: Raw yt-dlp metadata dictionary

        Returns:
            Tuple of (channel_name, channel_id) with fallbacks applied

        Priority order:
            1. uploader (display name) - most user-friendly
            2. channel (formal name) - alternative display name
            3. uploader_id (channel ID) - guaranteed unique
            4. "Unknown_Channel" - ultimate fallback
        """
        # Extract channel name with priority fallbacks
        channel_name = None
        for field in ["uploader", "channel", "uploader_id"]:
            if metadata.get(field):
                channel_name = str(metadata[field])
                break

        if not channel_name:
            channel_name = "Unknown_Channel"

        # Sanitize for filesystem compatibility
        sanitized_name = self._sanitize_channel_name(channel_name)

        # Extract channel ID for deduplication support
        channel_id = metadata.get("uploader_id", metadata.get("channel_id", "unknown"))

        return sanitized_name, channel_id

    def _get_deduplication_file(self) -> Path:
        """Get path to deduplication tracking file.

        Returns:
            Path to JSON file storing download history
        """
        return self.download_dir / ".yt_download_history.json"

    def _load_download_history(self) -> dict[str, dict[str, Any]]:
        """Load download history from file.

        Returns:
            Dictionary mapping video IDs to download metadata
        """
        history_file = self._get_deduplication_file()
        if not history_file.exists():
            return {}

        try:
            with open(history_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load download history: {e}")
            return {}

    def _save_download_history(self, history: dict[str, dict[str, Any]]) -> None:
        """Save download history to file.

        Args:
            history: Dictionary mapping video IDs to download metadata
        """
        history_file = self._get_deduplication_file()
        history_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning(f"Failed to save download history: {e}")

    def _record_download(self, video_id: str, metadata: MediaMetadata) -> None:
        """Record a successful download in history.

        Args:
            video_id: YouTube video ID
            metadata: Download metadata
        """
        history = self._load_download_history()

        history[video_id] = {
            "title": metadata.title,
            "uploader": metadata.uploader,
            "download_date": datetime.now().isoformat(),
            "url": metadata.url,
            "files": metadata.files or [],
            "download_method": metadata.download_method or "unknown",
        }

        # Keep only last 1000 entries to prevent file from growing too large
        if len(history) > 1000:
            # Remove oldest entries
            sorted_items = sorted(history.items(), key=lambda x: x[1].get("download_date", ""), reverse=True)
            history = dict(sorted_items[:1000])

        self._save_download_history(history)

    def _record_performance_metrics(self, video_id: str, duration: float, method: str) -> None:
        """Record performance metrics for a download.

        Args:
            video_id: YouTube video ID
            duration: Download duration in seconds
            method: Download method used (api, cli, cli_fallback)
        """
        metrics_file = self.download_dir / ".yt_performance_metrics.json"

        # Load existing metrics
        metrics = {}
        if metrics_file.exists():
            try:
                with open(metrics_file, encoding="utf-8") as f:
                    metrics = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load performance metrics: {e}")
                metrics = {}

        # Add new metric
        metrics[video_id] = {"duration": duration, "method": method, "timestamp": datetime.now().isoformat()}

        # Keep only last 500 entries to prevent file from growing too large
        if len(metrics) > 500:
            sorted_items = sorted(metrics.items(), key=lambda x: x[1].get("timestamp", ""), reverse=True)
            metrics = dict(sorted_items[:500])

        # Save metrics
        try:
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning(f"Failed to save performance metrics: {e}")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for YouTube downloads.

        Returns:
            Dictionary with performance statistics
        """
        metrics_file = self.download_dir / ".yt_performance_metrics.json"

        if not metrics_file.exists():
            return {
                "total_downloads": 0,
                "avg_duration": 0.0,
                "method_breakdown": {},
                "fastest_download": None,
                "slowest_download": None,
            }

        try:
            with open(metrics_file, encoding="utf-8") as f:
                metrics = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load performance metrics: {e}")
            return {"error": "Failed to load metrics"}

        if not metrics:
            return {
                "total_downloads": 0,
                "avg_duration": 0.0,
                "method_breakdown": {},
                "fastest_download": None,
                "slowest_download": None,
            }

        # Calculate statistics
        durations = [metric["duration"] for metric in metrics.values()]
        methods = [metric["method"] for metric in metrics.values()]

        method_breakdown = {}
        for method in methods:
            method_breakdown[method] = method_breakdown.get(method, 0) + 1

        # Find fastest and slowest
        sorted_by_duration = sorted(metrics.items(), key=lambda x: x[1]["duration"])
        fastest = sorted_by_duration[0] if sorted_by_duration else None
        slowest = sorted_by_duration[-1] if sorted_by_duration else None

        return {
            "total_downloads": len(metrics),
            "avg_duration": sum(durations) / len(durations) if durations else 0.0,
            "method_breakdown": method_breakdown,
            "fastest_download": {
                "video_id": fastest[0],
                "duration": fastest[1]["duration"],
                "method": fastest[1]["method"],
            }
            if fastest
            else None,
            "slowest_download": {
                "video_id": slowest[0],
                "duration": slowest[1]["duration"],
                "method": slowest[1]["method"],
            }
            if slowest
            else None,
        }

    def _is_video_downloaded(self, video_id: str) -> dict[str, Any] | None:
        """Check if video has been downloaded before.

        Args:
            video_id: YouTube video ID to check

        Returns:
            Download metadata if found, None otherwise
        """
        history = self._load_download_history()
        return history.get(video_id)

    def _check_deduplication(self, url: str, **kwargs) -> MediaMetadata | None:
        """Check if video should be skipped due to deduplication.

        Args:
            url: YouTube URL to check
            **kwargs: Download options (may include force_redownload)

        Returns:
            MediaMetadata with existing info if duplicate, None if should download
        """
        # Allow bypassing deduplication
        if kwargs.get("force_redownload", False):
            return None

        # Extract video ID
        video_id = self._extract_youtube_video_id(url)
        if not video_id:
            return None

        # Check if already downloaded
        existing_download = self._is_video_downloaded(video_id)
        if not existing_download:
            return None

        logger.info(f"Video {video_id} already downloaded on {existing_download.get('download_date')}")

        # Return metadata indicating duplicate
        return MediaMetadata(
            platform="youtube",
            url=url,
            title=existing_download.get("title", ""),
            uploader=existing_download.get("uploader", ""),
            files=existing_download.get("files", []),
            download_method=existing_download.get("download_method", ""),
            error=None,
            raw_metadata={"duplicate": True, "original_download": existing_download},
        )

    async def _download_via_api_with_fallbacks(self, url: str, **kwargs) -> MediaMetadata:
        """Enhanced API download with YouTube-specific error handling.

        Args:
            url: YouTube URL to download
            **kwargs: Download options

        Returns:
            MediaMetadata from API client

        Raises:
            RuntimeError: If download fails after all retry attempts
        """
        logger.debug(f"Starting API download with fallbacks for URL: {url}")
        # Update client configuration with download options
        download_options = {}

        # Quality selection
        quality = kwargs.get("quality", "720p")
        audio_only = kwargs.get("audio_only", False)
        logger.debug(f"Download options - quality: {quality}, audio_only: {audio_only}")

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

        max_retries = 3
        retry_delay = 2.0
        logger.debug(f"Starting download attempts with max_retries={max_retries}, initial_delay={retry_delay}s")

        for attempt in range(max_retries):
            logger.debug(f"Download attempt {attempt + 1}/{max_retries}")
            try:
                logger.debug("Acquiring API client for download")
                async with self.api_client as client:
                    logger.debug(f"Starting download with options: {download_options}")
                    # Download and convert API response to MediaMetadata
                    async for item in client.download(url, **download_options):
                        logger.debug("Download successful, converting response to metadata")
                        result = self._convert_api_response_to_metadata(item)
                        logger.debug(f"Metadata conversion complete - title: {result.title}")
                        return result

                # If no results, raise an error
                logger.error("No download results from YouTube API")
                raise RuntimeError("No download results from YouTube API")

            except Exception as e:
                logger.debug(f"Download attempt {attempt + 1} failed with error: {e}")
                error_message = str(e).lower()

                # Check for YouTube-specific errors that shouldn't be retried
                youtube_fatal_errors = [
                    "video unavailable",
                    "private video",
                    "deleted video",
                    "video not found",
                    "age restricted",
                    "copyright",
                    "account terminated",
                    "channel doesn't exist",
                    "livestream",
                    "premiere",
                ]

                is_fatal = any(fatal_error in error_message for fatal_error in youtube_fatal_errors)
                logger.debug(f"Error classification - fatal: {is_fatal}, message: {error_message}")

                if is_fatal:
                    logger.warning(f"YouTube fatal error detected, not retrying: {e}")
                    raise RuntimeError(f"YouTube video not accessible: {e}")

                # For non-fatal errors, retry with exponential backoff
                if attempt < max_retries - 1:
                    logger.warning(
                        f"YouTube API download attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}"
                    )
                    logger.debug(f"Sleeping for {retry_delay}s before retry")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    logger.debug(f"Next retry delay will be {retry_delay}s")
                else:
                    logger.error(f"YouTube API download failed after {max_retries} attempts: {e}")
                    raise RuntimeError(f"YouTube download failed after {max_retries} attempts: {e}")

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
