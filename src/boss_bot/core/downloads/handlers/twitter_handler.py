"""Twitter/X download handler using gallery-dl."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_handler import BaseDownloadHandler, DownloadResult, MediaMetadata


class TwitterHandler(BaseDownloadHandler):
    """Handler for downloading Twitter/X content using gallery-dl.

    Based on shell alias: gallery-dl --no-mtime -v --write-info-json --write-metadata "${url}"
    Supports both twitter.com and x.com domains.
    """

    @property
    def platform_name(self) -> str:
        """Platform name for this handler."""
        return "twitter"

    @property
    def supported_domains(self) -> list[str]:
        """Domains supported by this handler."""
        return ["twitter.com", "x.com"]

    def _build_gallery_dl_command(self, url: str, **options) -> list[str]:
        """Build gallery-dl command based on the dlt alias.

        Args:
            url: URL to download
            **options: Additional options (unused for MVP)

        Returns:
            Command as list of arguments
        """
        cmd = [
            "gallery-dl",
            "--no-mtime",  # Don't set file modification time
            "-v",  # Verbose output
            "--write-info-json",  # Write metadata to JSON file
            "--write-metadata",  # Write metadata to file
            url,
        ]
        return cmd

    def download(self, url: str, **options) -> DownloadResult:
        """Synchronous download of Twitter content.

        Args:
            url: Twitter/X URL to download
            **options: Additional download options

        Returns:
            DownloadResult with download status and files
        """
        if not self.supports_url(url):
            return DownloadResult(success=False, error=f"URL not supported by TwitterHandler: {url}")

        cmd = self._build_gallery_dl_command(url, **options)
        result = self._run_command(cmd)

        if result.success:
            # Find downloaded files
            result.files = self._find_downloaded_files(url)
            # Extract metadata from JSON files
            result.metadata = self._extract_metadata_from_files(result.files)

        return result

    async def adownload(self, url: str, **options) -> DownloadResult:
        """Asynchronous download of Twitter content.

        Args:
            url: Twitter/X URL to download
            **options: Additional download options

        Returns:
            DownloadResult with download status and files
        """
        if not self.supports_url(url):
            return DownloadResult(success=False, error=f"URL not supported by TwitterHandler: {url}")

        cmd = self._build_gallery_dl_command(url, **options)
        result = await self._arun_command(cmd)

        if result.success:
            # Find downloaded files
            result.files = self._find_downloaded_files(url)
            # Extract metadata from JSON files
            result.metadata = self._extract_metadata_from_files(result.files)

        return result

    def get_metadata(self, url: str) -> MediaMetadata:
        """Extract metadata without downloading content.

        Args:
            url: Twitter/X URL to extract metadata from

        Returns:
            MediaMetadata object with extracted information
        """
        if not self.supports_url(url):
            return MediaMetadata(url=url, platform="twitter", raw_metadata={"error": f"URL not supported: {url}"})

        # Use gallery-dl with --simulate to get metadata only
        cmd = ["gallery-dl", "--simulate", "--dump-json", url]

        result = self._run_command(cmd)

        if result.success and result.stdout:
            try:
                # Parse JSON output from gallery-dl
                metadata_lines = result.stdout.strip().split("\n")
                for line in metadata_lines:
                    if line.strip():
                        data = json.loads(line)
                        return self._parse_metadata(data, url)
            except (json.JSONDecodeError, KeyError) as e:
                return MediaMetadata(
                    url=url, platform="twitter", raw_metadata={"error": f"Failed to parse metadata: {e}"}
                )

        return MediaMetadata(
            url=url, platform="twitter", raw_metadata={"error": result.error or "Failed to extract metadata"}
        )

    async def aget_metadata(self, url: str) -> MediaMetadata:
        """Async metadata extraction without downloading.

        Args:
            url: Twitter/X URL to extract metadata from

        Returns:
            MediaMetadata object with extracted information
        """
        if not self.supports_url(url):
            return MediaMetadata(url=url, platform="twitter", raw_metadata={"error": f"URL not supported: {url}"})

        # Use gallery-dl with --simulate to get metadata only
        cmd = ["gallery-dl", "--simulate", "--dump-json", url]

        result = await self._arun_command(cmd)

        if result.success and result.stdout:
            try:
                # Parse JSON output from gallery-dl
                metadata_lines = result.stdout.strip().split("\n")
                for line in metadata_lines:
                    if line.strip():
                        data = json.loads(line)
                        return self._parse_metadata(data, url)
            except (json.JSONDecodeError, KeyError) as e:
                return MediaMetadata(
                    url=url, platform="twitter", raw_metadata={"error": f"Failed to parse metadata: {e}"}
                )

        return MediaMetadata(
            url=url, platform="twitter", raw_metadata={"error": result.error or "Failed to extract metadata"}
        )

    def _find_downloaded_files(self, url: str) -> list[Path]:
        """Find files downloaded by gallery-dl.

        Args:
            url: Original URL that was downloaded

        Returns:
            List of downloaded file paths
        """
        files = []

        # gallery-dl typically creates subdirectories based on the site
        # Look for common patterns in the download directory
        for pattern in ["**/*twitter*", "**/*x.com*", "**/*.json", "**/*.jpg", "**/*.png", "**/*.mp4"]:
            files.extend(self.download_dir.glob(pattern))

        # Filter to only recent files (within last 5 minutes)
        # This is a heuristic to find files from this download session
        import time

        recent_threshold = time.time() - 300  # 5 minutes ago

        recent_files = []
        for file_path in files:
            if file_path.stat().st_mtime > recent_threshold:
                recent_files.append(file_path)

        return recent_files

    def _extract_metadata_from_files(self, files: list[Path]) -> dict[str, Any] | None:
        """Extract metadata from downloaded JSON files.

        Args:
            files: List of downloaded files

        Returns:
            Extracted metadata dictionary
        """
        # Look for JSON files containing metadata
        json_files = [f for f in files if f.suffix == ".json"]

        if not json_files:
            return None

        # Use the first JSON file found
        try:
            with open(json_files[0], encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def _parse_metadata(self, data: dict[str, Any], url: str) -> MediaMetadata:
        """Parse gallery-dl JSON output into MediaMetadata.

        Args:
            data: JSON data from gallery-dl
            url: Original URL

        Returns:
            Parsed MediaMetadata object
        """
        # gallery-dl JSON structure varies, but common fields:
        return MediaMetadata(
            title=data.get("content", data.get("description", "")),
            description=data.get("content", ""),
            uploader=data.get("author", {}).get("name") if isinstance(data.get("author"), dict) else data.get("author"),
            upload_date=data.get("date", data.get("created_at")),
            url=url,
            platform="twitter",
            thumbnail=data.get("avatar") or data.get("profile_image_url"),
            view_count=data.get("retweet_count"),
            like_count=data.get("favorite_count"),
            raw_metadata=data,
        )

    def supports_url(self, url: str) -> bool:
        """Check if URL is a Twitter/X URL.

        Args:
            url: URL to check

        Returns:
            True if URL is supported
        """
        # Enhanced URL validation for Twitter/X
        twitter_patterns = [
            r"twitter\.com/[^/]+/status/\d+",
            r"x\.com/[^/]+/status/\d+",
            r"twitter\.com/[^/]+$",
            r"x\.com/[^/]+$",
        ]

        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in twitter_patterns)
