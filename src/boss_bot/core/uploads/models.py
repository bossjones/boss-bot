"""Data models for upload functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MediaType(Enum):
    """Types of media files we can handle."""

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class MediaFile:
    """Represents a media file ready for upload."""

    path: Path
    filename: str
    size_bytes: int
    media_type: MediaType
    is_compressed: bool = False
    original_path: Path | None = None

    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class UploadBatch:
    """A batch of files to upload together."""

    files: list[MediaFile]
    total_size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_size_mb(self) -> float:
        """Get total batch size in MB."""
        return self.total_size_bytes / (1024 * 1024)


@dataclass
class SizeAnalysis:
    """Analysis of file sizes for upload planning."""

    acceptable_files: list[MediaFile]  # Files that fit Discord limits
    oversized_files: list[MediaFile]  # Files that need compression
    total_files: int
    total_size_mb: float


@dataclass
class UploadResult:
    """Result of an upload operation."""

    success: bool
    message: str
    files_processed: int
    successful_uploads: int = 0
    failed_uploads: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
