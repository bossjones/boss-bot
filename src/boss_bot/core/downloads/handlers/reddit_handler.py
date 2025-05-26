"""Reddit download handler using gallery-dl."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_handler import BaseDownloadHandler, DownloadResult, MediaMetadata


class RedditHandler(BaseDownloadHandler):
    """Handler for downloading Reddit content using gallery-dl.

    Based on gallery-dl with custom config and cookie support.
    Supports reddit.com URLs for posts, galleries, and videos.
    """

    @property
    def platform_name(self) -> str:
        """Platform name for this handler."""
        return "reddit"

    @property
    def supported_domains(self) -> list[str]:
        """Domains supported by this handler."""
        return ["reddit.com", "www.reddit.com", "old.reddit.com"]

    def _build_gallery_dl_command(self, url: str, **options) -> list[str]:
        """Build gallery-dl command for Reddit downloads.

        Args:
            url: URL to download
            **options: Additional options (metadata_only, cookies, config)

        Returns:
            Command as list of arguments
        """
        cmd = [
            "gallery-dl",
            "--no-mtime",  # Don't set file modification time
            "-v",  # Verbose output
            "--write-info-json",  # Write metadata to JSON file
            "--write-metadata",  # Write metadata to file
        ]

        # Add custom config file if provided
        config_file = options.get("config_file")
        if config_file:
            cmd.extend(["--config", str(config_file)])

        # Add cookies file if provided
        cookies_file = options.get("cookies_file")
        if cookies_file:
            cmd.extend(["--cookies", str(cookies_file)])

        # Add metadata-only option if requested
        if options.get("metadata_only", False):
            cmd.append("--simulate")

        cmd.append(url)
        return cmd

    def download(self, url: str, **options) -> DownloadResult:
        """Download Reddit content synchronously.

        Args:
            url: Reddit URL to download
            **options: Additional options (metadata_only, cookies, config)

        Returns:
            DownloadResult with files and metadata
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by {self.platform_name} handler: {url}")

        cmd = self._build_gallery_dl_command(url, **options)

        stdout, stderr, returncode = self._run_command(cmd)

        if returncode != 0:
            raise RuntimeError(f"gallery-dl failed with return code {returncode}: {stderr}")

        # If metadata-only, don't look for downloaded files
        if options.get("metadata_only", False):
            metadata = self._extract_metadata_from_stdout(stdout)
            return DownloadResult(
                success=True,
                files=[],
                metadata=metadata,
                stdout=stdout,
                stderr=stderr,
            )

        # Find downloaded files
        downloaded_files = self._find_downloaded_files()

        # Extract metadata from downloaded JSON files
        metadata = self._extract_metadata_from_files(downloaded_files)

        return DownloadResult(
            success=True,
            files=downloaded_files,
            metadata=metadata,
            stdout=stdout,
            stderr=stderr,
        )

    async def adownload(self, url: str, **options) -> DownloadResult:
        """Download Reddit content asynchronously.

        Args:
            url: Reddit URL to download
            **options: Additional options (metadata_only, cookies, config)

        Returns:
            DownloadResult with files and metadata
        """
        if not self.supports_url(url):
            raise ValueError(f"URL not supported by {self.platform_name} handler: {url}")

        cmd = self._build_gallery_dl_command(url, **options)

        stdout, stderr, returncode = await self._arun_command(cmd)

        if returncode != 0:
            raise RuntimeError(f"gallery-dl failed with return code {returncode}: {stderr}")

        # If metadata-only, don't look for downloaded files
        if options.get("metadata_only", False):
            metadata = self._extract_metadata_from_stdout(stdout)
            return DownloadResult(
                success=True,
                files=[],
                metadata=metadata,
                stdout=stdout,
                stderr=stderr,
            )

        # Find downloaded files
        downloaded_files = self._find_downloaded_files()

        # Extract metadata from downloaded JSON files
        metadata = self._extract_metadata_from_files(downloaded_files)

        return DownloadResult(
            success=True,
            files=downloaded_files,
            metadata=metadata,
            stdout=stdout,
            stderr=stderr,
        )

    def get_metadata(self, url: str, **options) -> MediaMetadata | None:
        """Get metadata for Reddit content without downloading.

        Args:
            url: Reddit URL to analyze
            **options: Additional options (cookies, config)

        Returns:
            MediaMetadata if successful, None if failed
        """
        try:
            options["metadata_only"] = True
            result = self.download(url, **options)
            return result.metadata
        except Exception:
            return None

    async def aget_metadata(self, url: str, **options) -> MediaMetadata | None:
        """Get metadata for Reddit content asynchronously without downloading.

        Args:
            url: Reddit URL to analyze
            **options: Additional options (cookies, config)

        Returns:
            MediaMetadata if successful, None if failed
        """
        try:
            options["metadata_only"] = True
            result = await self.adownload(url, **options)
            return result.metadata
        except Exception:
            return None

    def supports_url(self, url: str) -> bool:
        """Check if URL is supported by this handler.

        Args:
            url: URL to check

        Returns:
            True if URL is supported, False otherwise
        """
        if not url:
            return False

        # Match Reddit URLs
        reddit_pattern = r"https?://(www\.|old\.)?reddit\.com/r/[\w\d_]+/comments/[\w\d]+/"
        return bool(re.match(reddit_pattern, url))

    def _find_downloaded_files(self) -> list[Path]:
        """Find files downloaded by gallery-dl in the output directory.

        Returns:
            List of downloaded file paths
        """
        downloaded_files = []

        # Look for files in the output directory
        if self.output_dir.exists():
            # Reddit content typically downloaded to reddit/<subreddit>/ structure
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    downloaded_files.append(file_path)

        return downloaded_files

    def _extract_metadata_from_files(self, files: list[Path]) -> MediaMetadata | None:
        """Extract metadata from downloaded JSON files.

        Args:
            files: List of downloaded files

        Returns:
            MediaMetadata if JSON metadata found, None otherwise
        """
        # Look for JSON metadata files
        json_files = [f for f in files if f.suffix == ".json"]

        if not json_files:
            return None

        # Use the first JSON file found
        json_file = json_files[0]

        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                return self._parse_metadata(data)
        except (OSError, json.JSONDecodeError):
            return None

    def _extract_metadata_from_stdout(self, stdout: str) -> MediaMetadata | None:
        """Extract metadata from gallery-dl stdout output.

        Args:
            stdout: Command stdout output

        Returns:
            MediaMetadata if extractable, None otherwise
        """
        # For Reddit, metadata extraction from stdout is limited
        # We rely primarily on JSON files
        return None

    def _parse_metadata(self, data: dict[str, Any]) -> MediaMetadata:
        """Parse gallery-dl JSON metadata into MediaMetadata.

        Args:
            data: Raw JSON metadata from gallery-dl

        Returns:
            Parsed MediaMetadata object
        """
        # Extract relevant fields from Reddit gallery-dl output
        title = data.get("title", "")
        author = data.get("author", "")
        if isinstance(author, dict):
            author = author.get("name", str(author))

        description = data.get("description") or data.get("selftext", "")

        # Reddit-specific fields
        subreddit = data.get("subreddit", "")
        score = data.get("score", 0)
        num_comments = data.get("num_comments", 0)
        created_utc = data.get("created_utc")

        return MediaMetadata(
            title=title,
            uploader=author,
            description=description,
            duration=None,  # Reddit posts don't have duration
            view_count=None,  # Reddit uses score instead
            like_count=score,
            upload_date=created_utc,
            thumbnail=data.get("thumbnail"),
            platform="reddit",
            url=data.get("url", ""),
            raw_metadata={
                "subreddit": subreddit,
                "score": score,
                "num_comments": num_comments,
                "created_utc": created_utc,
                "post_hint": data.get("post_hint"),
                "domain": data.get("domain"),
                "permalink": data.get("permalink"),
            },
        )
