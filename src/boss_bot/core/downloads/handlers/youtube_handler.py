"""YouTube download handler using yt-dlp."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from .base_handler import BaseDownloadHandler, DownloadResult, MediaMetadata


class YouTubeHandler(BaseDownloadHandler):
    """Handler for downloading YouTube content using yt-dlp.

    Based on yt-dlp with quality selection and format options.
    Supports youtube.com and youtu.be URLs for videos, playlists, and channels.
    Provides quality selection (720p, 1080p, best) and format options (mp4, webm, audio-only).
    """

    @property
    def platform_name(self) -> str:
        """Platform name for this handler."""
        return "youtube"

    @property
    def supported_domains(self) -> list[str]:
        """Domains supported by this handler."""
        return [
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "music.youtube.com",
        ]

    def _build_yt_dlp_command(self, url: str, **options) -> list[str]:
        """Build yt-dlp command for YouTube downloads.

        Default command structure with quality and format options:
        yt-dlp --format "best[height<=720]" --write-info-json --write-description --write-thumbnail

        Args:
            url: URL to download
            **options: Additional options (quality, format, audio_only, metadata_only, etc.)

        Returns:
            Command as list of arguments
        """
        cmd = ["yt-dlp"]

        # Quality selection (default to 720p for reasonable file sizes)
        quality = options.get("quality", "720p")
        audio_only = options.get("audio_only", False)

        if audio_only:
            # Audio-only extraction
            cmd.extend(
                [
                    "--format",
                    "bestaudio",
                    "--extract-audio",
                    "--audio-format",
                    options.get("audio_format", "mp3"),
                    "--audio-quality",
                    options.get("audio_quality", "192K"),
                ]
            )
        else:
            # Video with quality selection
            if quality == "best":
                cmd.extend(["--format", "best"])
            elif quality == "worst":
                cmd.extend(["--format", "worst"])
            elif quality in ["4K", "2160p"]:
                cmd.extend(["--format", "best[height<=2160]"])
            elif quality in ["1440p", "2K"]:
                cmd.extend(["--format", "best[height<=1440]"])
            elif quality in ["1080p", "FHD"]:
                cmd.extend(["--format", "best[height<=1080]"])
            elif quality in ["720p", "HD"]:
                cmd.extend(["--format", "best[height<=720]"])
            elif quality in ["480p"]:
                cmd.extend(["--format", "best[height<=480]"])
            elif quality in ["360p"]:
                cmd.extend(["--format", "best[height<=360]"])
            else:
                # Default to 720p if unknown quality
                cmd.extend(["--format", "best[height<=720]"])

            # Prefer mp4 format for better compatibility
            preferred_format = options.get("video_format", "mp4")
            if preferred_format:
                cmd.extend(["--merge-output-format", preferred_format])

        # Metadata options
        cmd.extend(
            [
                "--write-info-json",  # Write video metadata to JSON file
                "--write-description",  # Write video description to file
                "--write-thumbnail",  # Download thumbnail
            ]
        )

        # Output directory
        if self.download_dir:
            cmd.extend(["--output", str(self.download_dir / "%(uploader)s/%(title)s.%(ext)s")])

        # Playlist handling
        if options.get("no_playlist", True):
            cmd.append("--no-playlist")  # Download single video, not entire playlist
        else:
            cmd.append("--yes-playlist")  # Download entire playlist

        # Rate limiting and retries
        cmd.extend(
            [
                "--retries",
                str(options.get("retries", 3)),
                "--fragment-retries",
                str(options.get("fragment_retries", 3)),
            ]
        )

        # Additional user options
        if options.get("subtitle_langs"):
            cmd.extend(["--write-subs", "--sub-langs", options["subtitle_langs"]])

        if options.get("cookies_file"):
            cmd.extend(["--cookies", str(options["cookies_file"])])

        if options.get("user_agent"):
            cmd.extend(["--user-agent", options["user_agent"]])

        # Verbose output if requested
        if options.get("verbose", False):
            cmd.append("--verbose")

        # Metadata-only mode
        if options.get("metadata_only", False):
            cmd.extend(["--skip-download", "--write-info-json"])

        cmd.append(url)
        return cmd

    def supports_url(self, url: str) -> bool:
        """Check if this handler supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if URL is supported, False otherwise
        """
        # YouTube URL patterns
        patterns = [
            r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",  # Standard video
            r"^https?://(?:www\.)?youtube\.com/embed/[\w-]+",  # Embed URL
            r"^https?://(?:www\.)?youtube\.com/v/[\w-]+",  # Old format
            r"^https?://youtu\.be/[\w-]+",  # Short URL
            r"^https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+",  # Playlist
            r"^https?://(?:www\.)?youtube\.com/channel/[\w-]+",  # Channel
            r"^https?://(?:www\.)?youtube\.com/user/[\w-]+",  # User channel
            r"^https?://(?:www\.)?youtube\.com/c/[\w-]+",  # Custom URL
            r"^https?://(?:www\.)?youtube\.com/@[\w-]+",  # Handle format
            r"^https?://(?:music\.)?youtube\.com/watch\?v=[\w-]+",  # YouTube Music
        ]

        return any(re.match(pattern, url, re.IGNORECASE) for pattern in patterns)

    def download(self, url: str, **options) -> DownloadResult:
        """Download content from YouTube URL.

        Args:
            url: YouTube URL to download
            **options: Download options (quality, format, etc.)

        Returns:
            DownloadResult with success status and file paths
        """
        if not self.supports_url(url):
            return DownloadResult(
                success=False,
                error=f"URL not supported by {self.platform_name} handler: {url}",
            )

        try:
            cmd = self._build_yt_dlp_command(url, **options)
            result = self._run_command(cmd)

            if result.returncode == 0:
                # Find downloaded files
                files = self._find_downloaded_files(url, **options)
                metadata = self._extract_metadata_from_files(files) if files else None

                return DownloadResult(
                    success=True,
                    files=files,
                    metadata=metadata,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                )
            else:
                return DownloadResult(
                    success=False,
                    error=f"yt-dlp command failed with return code {result.returncode}",
                    stderr=result.stderr,
                    stdout=result.stdout,
                    return_code=result.returncode,
                )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=f"yt-dlp command failed: {e}",
            )

    async def adownload(self, url: str, **options) -> DownloadResult:
        """Async version of download method.

        Args:
            url: YouTube URL to download
            **options: Download options

        Returns:
            DownloadResult with success status and file paths
        """
        if not self.supports_url(url):
            return DownloadResult(
                success=False,
                error=f"URL not supported by {self.platform_name} handler: {url}",
            )

        try:
            cmd = self._build_yt_dlp_command(url, **options)
            result = await self._arun_command(cmd)

            if result.returncode == 0:
                # Find downloaded files
                files = self._find_downloaded_files(url, **options)
                metadata = self._extract_metadata_from_files(files) if files else None

                return DownloadResult(
                    success=True,
                    files=files,
                    metadata=metadata,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                )
            else:
                return DownloadResult(
                    success=False,
                    error=f"yt-dlp command failed with return code {result.returncode}",
                    stderr=result.stderr,
                    stdout=result.stdout,
                    return_code=result.returncode,
                )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=f"yt-dlp command failed: {e}",
            )

    def get_metadata(self, url: str, **options) -> MediaMetadata:
        """Extract metadata from YouTube URL without downloading.

        Args:
            url: YouTube URL to extract metadata from
            **options: Additional options

        Returns:
            MediaMetadata object with extracted information
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by {self.platform_name} handler: {url}")

        try:
            # Use metadata-only mode
            options_copy = options.copy()
            options_copy["metadata_only"] = True

            cmd = self._build_yt_dlp_command(url, **options_copy)
            result = self._run_command(cmd)

            if result.returncode == 0:
                # Find and parse JSON files
                files = self._find_downloaded_files(url, **options_copy)
                return self._extract_metadata_from_files(files) or MediaMetadata(
                    platform=self.platform_name,
                    url=url,
                )
            else:
                raise RuntimeError(f"yt-dlp metadata extraction failed: {result.stderr}")

        except Exception as e:
            raise RuntimeError(f"Error extracting metadata from YouTube: {e}") from e

    async def aget_metadata(self, url: str, **options) -> MediaMetadata:
        """Async version of get_metadata method.

        Args:
            url: YouTube URL to extract metadata from
            **options: Additional options

        Returns:
            MediaMetadata object with extracted information
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by {self.platform_name} handler: {url}")

        try:
            # Use metadata-only mode
            options_copy = options.copy()
            options_copy["metadata_only"] = True

            cmd = self._build_yt_dlp_command(url, **options_copy)
            result = await self._arun_command(cmd)

            if result.returncode == 0:
                # Find and parse JSON files
                files = self._find_downloaded_files(url, **options_copy)
                return self._extract_metadata_from_files(files) or MediaMetadata(
                    platform=self.platform_name,
                    url=url,
                )
            else:
                raise RuntimeError(f"yt-dlp metadata extraction failed: {result.stderr}")

        except Exception as e:
            raise RuntimeError(f"Error extracting metadata from YouTube: {e}") from e

    def _find_downloaded_files(self, url: str, **options) -> list[Path]:
        """Find files downloaded by yt-dlp.

        Args:
            url: Original URL
            **options: Download options

        Returns:
            List of downloaded file paths
        """
        if not self.download_dir or not self.download_dir.exists():
            return []

        files = []

        # Look for video files, info files, and thumbnails
        for pattern in [
            "*.mp4",
            "*.webm",
            "*.mkv",
            "*.mp3",
            "*.m4a",
            "*.info.json",
            "*.description",
            "*.jpg",
            "*.png",
            "*.webp",
        ]:
            files.extend(self.download_dir.rglob(pattern))

        # Sort by modification time (most recent first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files

    def _extract_metadata_from_files(self, files: list[Path]) -> MediaMetadata | None:
        """Extract metadata from downloaded files.

        Args:
            files: List of downloaded files

        Returns:
            MediaMetadata object or None if extraction fails
        """
        if not files:
            return None

        # Look for .info.json file
        info_files = [f for f in files if f.suffix == ".json" and ".info" in f.name]

        if not info_files:
            return MediaMetadata(
                platform=self.platform_name,
                title="",
                description="",
                uploader="",
                upload_date="",
                thumbnail="",
                url="",
                format="",
                author="",
                filename="",
                thumbnail_url="",
                download_method="",
            )

        try:
            info_file = info_files[0]
            with open(info_file, encoding="utf-8") as f:
                data = json.load(f)

            return self._parse_metadata(data)

        except (OSError, json.JSONDecodeError) as e:
            # Log error but don't fail completely
            return MediaMetadata(
                platform=self.platform_name,
                title="",
                description="",
                uploader="",
                upload_date="",
                thumbnail="",
                url="",
                format="",
                author="",
                filename="",
                thumbnail_url="",
                download_method="",
                error=f"Failed to parse metadata: {e}",
            )

    def _parse_metadata(self, data: dict[str, Any]) -> MediaMetadata:
        """Parse yt-dlp JSON metadata into MediaMetadata object.

        Args:
            data: Raw metadata dictionary from yt-dlp

        Returns:
            MediaMetadata object with parsed information
        """
        # Extract uploader info
        uploader = data.get("uploader") or data.get("channel")
        if isinstance(uploader, dict):
            uploader = uploader.get("name", "Unknown")
        elif not isinstance(uploader, str):
            uploader = "Unknown"

        return MediaMetadata(
            platform=self.platform_name,
            url=data.get("webpage_url", ""),
            title=data.get("title", ""),
            uploader=uploader,
            upload_date=data.get("upload_date", ""),
            duration=data.get("duration"),
            view_count=data.get("view_count"),
            like_count=data.get("like_count"),
            comment_count=data.get("comment_count"),
            description=data.get("description", ""),
            thumbnail_url=data.get("thumbnail", ""),
            tags=data.get("tags"),
            raw_metadata=data,
        )
