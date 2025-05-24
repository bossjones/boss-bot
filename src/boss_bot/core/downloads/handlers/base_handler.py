"""Base download handler for all media download implementations."""

from __future__ import annotations

import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    files: list[Path] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    stderr: str | None = None
    stdout: str | None = None
    return_code: int | None = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.files is None:
            self.files = []


@dataclass
class MediaMetadata:
    """Metadata extracted from media URLs."""

    title: str | None = None
    description: str | None = None
    uploader: str | None = None
    upload_date: str | None = None
    duration: float | None = None
    view_count: int | None = None
    like_count: int | None = None
    url: str | None = None
    thumbnail: str | None = None
    platform: str | None = None
    file_size: int | None = None
    format: str | None = None
    raw_metadata: dict[str, Any] | None = None


class BaseDownloadHandler(ABC):
    """Abstract base class for all download handlers.

    Provides sync and async methods for downloading media content
    and extracting metadata from various platforms.
    """

    def __init__(self, download_dir: Path | None = None):
        """Initialize the handler with optional download directory.

        Args:
            download_dir: Directory to save downloads. Defaults to current directory.
        """
        self.download_dir = download_dir or Path.cwd()
        self.download_dir.mkdir(exist_ok=True, parents=True)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform this handler supports (e.g., 'twitter', 'youtube')."""
        pass

    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """List of domains this handler supports (e.g., ['twitter.com', 'x.com'])."""
        pass

    @abstractmethod
    def download(self, url: str, **options) -> DownloadResult:
        """Synchronous download of media content.

        Args:
            url: URL to download
            **options: Platform-specific download options

        Returns:
            DownloadResult with download status and file paths
        """
        pass

    @abstractmethod
    async def adownload(self, url: str, **options) -> DownloadResult:
        """Asynchronous download of media content (prefixed with 'a').

        Args:
            url: URL to download
            **options: Platform-specific download options

        Returns:
            DownloadResult with download status and file paths
        """
        pass

    @abstractmethod
    def get_metadata(self, url: str) -> MediaMetadata:
        """Extract metadata without downloading content.

        Args:
            url: URL to extract metadata from

        Returns:
            MediaMetadata object with extracted information
        """
        pass

    @abstractmethod
    async def aget_metadata(self, url: str) -> MediaMetadata:
        """Async metadata extraction without downloading.

        Args:
            url: URL to extract metadata from

        Returns:
            MediaMetadata object with extracted information
        """
        pass

    def supports_url(self, url: str) -> bool:
        """Check if this handler supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if this handler supports the URL
        """
        return any(domain in url.lower() for domain in self.supported_domains)

    def _run_command(self, cmd: list[str], cwd: Path | None = None) -> DownloadResult:
        """Run a subprocess command and return structured result.

        Args:
            cmd: Command to run as list of arguments
            cwd: Working directory for command

        Returns:
            DownloadResult with command output and status
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.download_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            return DownloadResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                error=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired as e:
            return DownloadResult(
                success=False, error=f"Command timed out after 300 seconds: {' '.join(cmd)}", stderr=str(e)
            )
        except Exception as e:
            return DownloadResult(success=False, error=f"Command failed: {e}", stderr=str(e))

    async def _arun_command(self, cmd: list[str], cwd: Path | None = None) -> DownloadResult:
        """Async version of _run_command.

        Args:
            cmd: Command to run as list of arguments
            cwd: Working directory for command

        Returns:
            DownloadResult with command output and status
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, cwd=cwd or self.download_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,  # 5 minute timeout
            )

            return DownloadResult(
                success=process.returncode == 0,
                stdout=stdout.decode() if stdout else None,
                stderr=stderr.decode() if stderr else None,
                return_code=process.returncode,
                error=stderr.decode() if process.returncode != 0 and stderr else None,
            )

        except TimeoutError:
            return DownloadResult(success=False, error=f"Command timed out after 300 seconds: {' '.join(cmd)}")
        except Exception as e:
            return DownloadResult(success=False, error=f"Command failed: {e}", stderr=str(e))
