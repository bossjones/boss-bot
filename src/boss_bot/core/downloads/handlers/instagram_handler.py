"""Instagram download handler using gallery-dl."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_handler import BaseDownloadHandler, DownloadResult, MediaMetadata


class InstagramHandler(BaseDownloadHandler):
    """Handler for downloading Instagram content using gallery-dl.

    Based on gallery-dl with custom config and cookie support.
    Supports instagram.com URLs for posts, stories, reels, and IGTV.
    Uses Firefox cookies by default and specific user agent for compatibility.
    """

    @property
    def platform_name(self) -> str:
        """Platform name for this handler."""
        return "instagram"

    @property
    def supported_domains(self) -> list[str]:
        """Domains supported by this handler."""
        return ["instagram.com", "www.instagram.com", "m.instagram.com"]

    def _build_gallery_dl_command(self, url: str, **options) -> list[str]:
        """Build gallery-dl command for Instagram downloads.

        Based on the user's CLI command:
        gallery-dl --cookies-from-browser Firefox --no-mtime --user-agent Wget/1.21.1 -v --write-info-json --write-metadata

        Args:
            url: URL to download
            **options: Additional options (metadata_only, cookies, config)

        Returns:
            Command as list of arguments
        """
        cmd = [
            "gallery-dl",
            "--cookies-from-browser",
            "Firefox",  # Use Firefox cookies by default
            "--no-mtime",  # Don't set file modification time
            "--user-agent",
            "Wget/1.21.1",  # Use specific user agent for Instagram
            "-v",  # Verbose output
            "--write-info-json",  # Write metadata to JSON file
            "--write-metadata",  # Write metadata to file
        ]

        # Add custom config file if provided
        config_file = options.get("config_file")
        if config_file:
            cmd.extend(["--config", str(config_file)])

        # Override cookies if custom cookies file provided
        cookies_file = options.get("cookies_file")
        if cookies_file:
            # Remove the default Firefox cookies and use custom file
            if "--cookies-from-browser" in cmd:
                idx = cmd.index("--cookies-from-browser")
                cmd.pop(idx)  # Remove --cookies-from-browser
                cmd.pop(idx)  # Remove Firefox
            cmd.extend(["--cookies", str(cookies_file)])

        # Override user agent if provided
        user_agent = options.get("user_agent")
        if user_agent:
            idx = cmd.index("--user-agent")
            cmd[idx + 1] = user_agent

        # Override browser for cookies if provided
        cookies_browser = options.get("cookies_browser")
        if cookies_browser and not cookies_file:
            idx = cmd.index("Firefox")
            cmd[idx] = cookies_browser

        # Add output directory
        if self.download_dir:
            cmd.extend(["-D", str(self.download_dir)])

        # Add metadata-only mode if requested
        if options.get("metadata_only"):
            cmd.append("--simulate")  # Don't actually download files

        # Add the URL
        cmd.append(url)

        return cmd

    def _extract_metadata_from_info_json(self, info_file: Path, url: str) -> MediaMetadata:
        """Extract metadata from gallery-dl info JSON file.

        Args:
            info_file: Path to the .info.json file
            url: Original URL

        Returns:
            MediaMetadata object with extracted information
        """
        try:
            with open(info_file, encoding="utf-8") as f:
                data = json.load(f)

            # Extract Instagram-specific metadata
            title = data.get("description") or data.get("title", "Instagram Post")
            author = self._extract_author(data)
            filename = data.get("filename") or data.get("_filename")
            upload_date = data.get("date") or data.get("upload_date")

            # Instagram-specific fields
            like_count = data.get("like_count")
            view_count = data.get("view_count") or data.get("video_view_count")
            comment_count = data.get("comment_count")
            post_type = data.get("typename") or data.get("media_type", "post")

            return MediaMetadata(
                url=url,
                title=title,
                author=author,
                platform="instagram",
                filename=filename,
                filesize=data.get("filesize"),
                duration=data.get("duration"),
                upload_date=upload_date,
                view_count=view_count,
                like_count=like_count,
                description=data.get("description"),
                thumbnail_url=data.get("thumbnail"),
                download_method="cli",
                raw_metadata={
                    "post_type": post_type,
                    "comment_count": comment_count,
                    "is_video": data.get("is_video", False),
                    "shortcode": data.get("shortcode"),
                    "post_id": data.get("id"),
                    "owner": data.get("owner", {}).get("username") if data.get("owner") else None,
                },
            )

        except (json.JSONDecodeError, FileNotFoundError) as e:
            # Return basic metadata if JSON parsing fails
            return MediaMetadata(
                url=url,
                title="Instagram Content",
                author="Unknown",
                platform="instagram",
                download_method="cli",
                raw_metadata={"error": str(e)},
            )

    def _extract_author(self, data: dict) -> str:
        """Extract author/uploader from Instagram data.

        Args:
            data: Instagram metadata dict

        Returns:
            Author username
        """
        # Try different fields for author information
        if "owner" in data and isinstance(data["owner"], dict):
            return data["owner"].get("username", "Unknown")
        elif "uploader" in data:
            return data["uploader"]
        elif "username" in data:
            return data["username"]
        elif "user" in data and isinstance(data["user"], dict):
            return data["user"].get("username", "Unknown")
        else:
            return "Unknown"

    def _is_instagram_url(self, url: str) -> bool:
        """Check if URL is a valid Instagram URL.

        Args:
            url: URL to validate

        Returns:
            True if URL is an Instagram URL
        """
        instagram_patterns = [
            r"https?://(?:www\.)?instagram\.com/p/[\w-]+/?",  # Posts
            r"https?://(?:www\.)?instagram\.com/reel/[\w-]+/?",  # Reels
            r"https?://(?:www\.)?instagram\.com/tv/[\w-]+/?",  # IGTV
            r"https?://(?:www\.)?instagram\.com/stories/[\w.-]+/\d+/?",  # Stories
            r"https?://(?:www\.)?instagram\.com/[\w.-]+/?",  # User profiles
        ]

        return any(re.match(pattern, url, re.IGNORECASE) for pattern in instagram_patterns)

    def supports_url(self, url: str) -> bool:
        """Check if this handler supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if URL is supported by Instagram handler
        """
        return self._is_instagram_url(url)

    def _extract_download_info(self, output: str, download_dir: Path) -> dict[str, Any]:
        """Extract download information from gallery-dl output.

        Args:
            output: gallery-dl stdout
            download_dir: Directory where files were downloaded

        Returns:
            Dictionary with download information
        """
        lines = output.strip().split("\n")
        downloaded_files = []
        metadata = {}

        for line in lines:
            if "[download]" in line.lower() and download_dir.name in line:
                # Extract downloaded file path from output
                # Example: [instagram][info] example.jpg
                if "] " in line:
                    potential_file = line.split("] ")[-1].strip()
                    file_path = download_dir / potential_file
                    if file_path.exists():
                        downloaded_files.append(file_path)

        # Look for info.json files in download directory
        info_files = list(download_dir.glob("*.info.json"))
        if info_files:
            try:
                with open(info_files[0], encoding="utf-8") as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # If no files found via parsing, scan directory for recent files
        if not downloaded_files:
            # Get all files in download directory that aren't info.json
            all_files = [f for f in download_dir.iterdir() if f.is_file() and not f.name.endswith(".info.json")]
            # Sort by modification time (most recent first)
            if all_files:
                downloaded_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)

        return {
            "files": downloaded_files,
            "metadata": metadata,
            "raw_output": output,
        }

    def download(self, url: str, **options) -> DownloadResult:
        """Synchronous download of Instagram content.

        Args:
            url: Instagram URL to download
            **options: Additional options (metadata_only, cookies, config)

        Returns:
            DownloadResult with download status and file paths
        """
        if not self.supports_url(url):
            return DownloadResult(
                success=False,
                error=f"URL not supported by Instagram handler: {url}",
            )

        # Build gallery-dl command
        cmd = self._build_gallery_dl_command(url, **options)

        # Run the command
        result = self._run_command(cmd, cwd=self.download_dir)

        if result.success and result.stdout:
            # Extract download information from output
            download_info = self._extract_download_info(result.stdout, self.download_dir)
            result.files = download_info["files"]
            result.metadata = download_info["metadata"]

        return result

    async def adownload(self, url: str, **options) -> DownloadResult:
        """Asynchronous download of Instagram content.

        Args:
            url: Instagram URL to download
            **options: Additional options

        Returns:
            DownloadResult with download status and file paths
        """
        # Run synchronous download in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.download, url, **options)

    def get_metadata(self, url: str, **options) -> MediaMetadata:
        """Extract metadata from Instagram URL without downloading.

        Args:
            url: Instagram URL to extract metadata from
            **options: Additional options

        Returns:
            MediaMetadata object with extracted information
        """
        if not self.supports_url(url):
            return MediaMetadata(
                url=url,
                title="Unsupported URL",
                platform="instagram",
                raw_metadata={"error": "URL not supported by Instagram handler"},
            )

        # Add metadata-only option and run command
        metadata_options = {**options, "metadata_only": True}
        cmd = self._build_gallery_dl_command(url, **metadata_options)

        # Run the command
        result = self._run_command(cmd, cwd=self.download_dir)

        if result.success:
            # Look for info.json files created by gallery-dl
            info_files = list(self.download_dir.glob("*.info.json"))
            if info_files:
                # Use the first info file found
                return self._extract_metadata_from_info_json(info_files[0], url)

        # Fallback: return basic metadata
        return MediaMetadata(
            url=url,
            title="Instagram Content",
            platform="instagram",
            raw_metadata={
                "error": result.error or "Failed to extract metadata",
                "stderr": result.stderr,
            },
        )

    async def aget_metadata(self, url: str, **options) -> MediaMetadata:
        """Asynchronous metadata extraction from Instagram URL.

        Args:
            url: Instagram URL to extract metadata from
            **options: Additional options

        Returns:
            MediaMetadata object with extracted information
        """
        # Run synchronous metadata extraction in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_metadata, url, **options)
