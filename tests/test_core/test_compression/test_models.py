"""Tests for compression data models."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from boss_bot.core.compression.models import (
    CompressionError,
    MediaInfo,
    CompressionSettings,
    CompressionResult
)


class TestCompressionError:
    """Tests for CompressionError exception."""

    def test_compression_error_creation(self):
        """Test creating compression error."""
        error = CompressionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_compression_error_inheritance(self):
        """Test that CompressionError inherits from Exception."""
        error = CompressionError("Test")
        assert isinstance(error, Exception)


class TestMediaInfo:
    """Tests for MediaInfo model."""

    def test_media_info_creation_minimal(self):
        """Test creating MediaInfo with minimal fields."""
        info = MediaInfo(
            file_path=Path("/test/file.mp4"),
            file_size_bytes=1024,
            duration_seconds=None,
            format_name="mp4",
            codec_name=None,
            width=None,
            height=None,
            bitrate_kbps=None,
            metadata={}
        )

        assert info.file_path == Path("/test/file.mp4")
        assert info.file_size_bytes == 1024
        assert info.duration_seconds is None
        assert info.format_name == "mp4"
        assert info.codec_name is None
        assert info.width is None
        assert info.height is None
        assert info.bitrate_kbps is None
        assert info.metadata == {}

    def test_media_info_creation_full(self):
        """Test creating MediaInfo with all fields."""
        metadata = {"container": "mp4", "profile": "main"}
        info = MediaInfo(
            file_path=Path("/test/video.mp4"),
            file_size_bytes=50 * 1024 * 1024,
            duration_seconds=120.5,
            format_name="mp4",
            codec_name="h264",
            width=1920,
            height=1080,
            bitrate_kbps=2000,
            metadata=metadata
        )

        assert info.file_path == Path("/test/video.mp4")
        assert info.file_size_bytes == 50 * 1024 * 1024
        assert info.duration_seconds == 120.5
        assert info.format_name == "mp4"
        assert info.codec_name == "h264"
        assert info.width == 1920
        assert info.height == 1080
        assert info.bitrate_kbps == 2000
        assert info.metadata == metadata

    def test_media_info_validation_negative_size(self):
        """Test validation fails for negative file size."""
        with pytest.raises(ValidationError):
            MediaInfo(
                file_path=Path("/test/file.mp4"),
                file_size_bytes=-1024,
                duration_seconds=None,
                format_name="mp4",
                codec_name=None,
                width=None,
                height=None,
                bitrate_kbps=None,
                metadata={}
            )

    def test_media_info_validation_negative_duration(self):
        """Test validation fails for negative duration."""
        with pytest.raises(ValidationError):
            MediaInfo(
                file_path=Path("/test/file.mp4"),
                file_size_bytes=1024,
                duration_seconds=-10.0,
                format_name="mp4",
                codec_name=None,
                width=None,
                height=None,
                bitrate_kbps=None,
                metadata={}
            )


class TestCompressionSettings:
    """Tests for CompressionSettings model."""

    def test_compression_settings_defaults(self):
        """Test default compression settings."""
        settings = CompressionSettings()

        assert settings.target_size_mb == 50
        assert settings.ffmpeg_preset == "slow"
        assert settings.max_concurrent == 3

    def test_compression_settings_custom(self):
        """Test custom compression settings."""
        settings = CompressionSettings(
            target_size_mb=25,
            ffmpeg_preset="fast",
            max_concurrent=5
        )

        assert settings.target_size_mb == 25
        assert settings.ffmpeg_preset == "fast"
        assert settings.max_concurrent == 5

    def test_compression_settings_validation_positive_target_size(self):
        """Test validation requires positive target size."""
        with pytest.raises(ValidationError):
            CompressionSettings(target_size_mb=0)

        with pytest.raises(ValidationError):
            CompressionSettings(target_size_mb=-5)

    def test_compression_settings_validation_positive_max_concurrent(self):
        """Test validation requires positive max concurrent."""
        with pytest.raises(ValidationError):
            CompressionSettings(max_concurrent=0)

        with pytest.raises(ValidationError):
            CompressionSettings(max_concurrent=-1)

    def test_compression_settings_validation_ffmpeg_preset(self):
        """Test validation of ffmpeg preset values."""
        # Valid presets should work
        valid_presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]

        for preset in valid_presets:
            settings = CompressionSettings(ffmpeg_preset=preset)
            assert settings.ffmpeg_preset == preset

        # Invalid preset should fail
        with pytest.raises(ValidationError):
            CompressionSettings(ffmpeg_preset="invalid_preset")


class TestCompressionResult:
    """Tests for CompressionResult model."""

    def test_compression_result_success(self):
        """Test successful compression result."""
        result = CompressionResult(
            success=True,
            input_path=Path("/input/file.mp4"),
            output_path=Path("/output/file_compressed.mp4"),
            original_size_bytes=100 * 1024 * 1024,
            compressed_size_bytes=50 * 1024 * 1024,
            compression_ratio=0.5,
            processing_time_seconds=120.5,
            metadata={"bitrate": "1000kbps"}
        )

        assert result.success is True
        assert result.input_path == Path("/input/file.mp4")
        assert result.output_path == Path("/output/file_compressed.mp4")
        assert result.original_size_bytes == 100 * 1024 * 1024
        assert result.compressed_size_bytes == 50 * 1024 * 1024
        assert result.compression_ratio == 0.5
        assert result.processing_time_seconds == 120.5
        assert result.error_message is None
        assert result.metadata == {"bitrate": "1000kbps"}

    def test_compression_result_failure(self):
        """Test failed compression result."""
        result = CompressionResult(
            success=False,
            input_path=Path("/input/file.mp4"),
            output_path=None,
            original_size_bytes=100 * 1024 * 1024,
            compressed_size_bytes=0,
            compression_ratio=0.0,
            processing_time_seconds=5.0,
            error_message="Compression failed: insufficient bitrate"
        )

        assert result.success is False
        assert result.input_path == Path("/input/file.mp4")
        assert result.output_path is None
        assert result.original_size_bytes == 100 * 1024 * 1024
        assert result.compressed_size_bytes == 0
        assert result.compression_ratio == 0.0
        assert result.processing_time_seconds == 5.0
        assert result.error_message == "Compression failed: insufficient bitrate"
        assert result.metadata == {}

    def test_compression_result_defaults(self):
        """Test compression result with default values."""
        result = CompressionResult(
            success=True,
            input_path=Path("/test/file.mp4"),
            original_size_bytes=1024
        )

        assert result.success is True
        assert result.input_path == Path("/test/file.mp4")
        assert result.output_path is None
        assert result.original_size_bytes == 1024
        assert result.compressed_size_bytes == 0
        assert result.compression_ratio == 0.0
        assert result.processing_time_seconds == 0.0
        assert result.error_message is None
        assert result.metadata == {}

    def test_compression_result_validation_negative_sizes(self):
        """Test validation prevents negative file sizes."""
        with pytest.raises(ValidationError):
            CompressionResult(
                success=True,
                input_path=Path("/test/file.mp4"),
                original_size_bytes=-1024
            )

        with pytest.raises(ValidationError):
            CompressionResult(
                success=True,
                input_path=Path("/test/file.mp4"),
                original_size_bytes=1024,
                compressed_size_bytes=-512
            )

    def test_compression_result_validation_negative_time(self):
        """Test validation prevents negative processing time."""
        with pytest.raises(ValidationError):
            CompressionResult(
                success=True,
                input_path=Path("/test/file.mp4"),
                original_size_bytes=1024,
                processing_time_seconds=-5.0
            )
