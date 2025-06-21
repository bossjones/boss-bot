"""Data models for compression operations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator


class CompressionError(Exception):
    """Exception raised during compression operations."""

    pass


class MediaInfo(BaseModel):
    """Information about a media file."""

    file_path: Path
    file_size_bytes: int
    duration_seconds: float | None = None
    format_name: str
    codec_name: str | None = None
    width: int | None = None
    height: int | None = None
    bitrate_kbps: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v < 0:
            raise ValueError("File size must be non-negative")
        return v

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("Duration must be non-negative")
        return v

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size_bytes / (1024 * 1024)


class CompressionSettings(BaseModel):
    """Settings for compression operation."""

    target_size_mb: int = 50  # Default changed to 50MB, configurable via BossSettings
    video_bitrate_ratio: float = 0.9
    audio_bitrate_ratio: float = 0.1
    min_video_bitrate_kbps: int = 125
    min_audio_bitrate_kbps: int = 32
    min_image_quality: int = 10
    ffmpeg_preset: str = "slow"
    hardware_acceleration: bool = True
    max_concurrent: int = 3

    @field_validator("target_size_mb", "max_concurrent")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("ffmpeg_preset")
    @classmethod
    def validate_ffmpeg_preset(cls, v: str) -> str:
        valid_presets = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
        if v.lower() not in valid_presets:
            raise ValueError(f"Invalid FFmpeg preset. Must be one of {valid_presets}")
        return v.lower()


class CompressionResult(BaseModel):
    """Result of a compression operation."""

    success: bool
    input_path: Path
    output_path: Path | None = None
    original_size_bytes: int
    compressed_size_bytes: int = 0
    compression_ratio: float = 0.0
    processing_time_seconds: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @field_validator("original_size_bytes", "compressed_size_bytes")
    @classmethod
    def validate_size_bytes(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Size must be non-negative")
        return v

    @field_validator("processing_time_seconds")
    @classmethod
    def validate_processing_time(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Processing time must be non-negative")
        return v

    @property
    def original_size_mb(self) -> float:
        """Get original file size in MB."""
        return self.original_size_bytes / (1024 * 1024)

    @property
    def compressed_size_mb(self) -> float:
        """Get compressed file size in MB."""
        return self.compressed_size_bytes / (1024 * 1024)

    @property
    def size_reduction_mb(self) -> float:
        """Get size reduction in MB."""
        return self.original_size_mb - self.compressed_size_mb
