"""Tests for compression manager."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from boss_bot.core.compression.models import CompressionError, CompressionResult, MediaInfo
from boss_bot.core.compression.manager import CompressionManager
from boss_bot.core.compression.utils.file_detector import MediaType


class TestCompressionManager:
    """Tests for CompressionManager class."""

    def test_compression_manager_initialization(self, fixture_compression_manager_test):
        """Test compression manager initialization."""
        manager = fixture_compression_manager_test

        assert manager.video_processor is not None
        assert manager.audio_processor is not None
        assert manager.image_processor is not None
        assert manager.file_detector is not None

    @pytest.mark.asyncio
    async def test_compress_file_video(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_temp_dir_test):
        """Test compressing video file."""
        manager = fixture_compression_manager_test
        output_path = fixture_temp_dir_test / "output.mp4"

        # Mock video processor
        expected_result = CompressionResult(
            success=True,
            input_path=fixture_test_video_file_test,
            output_path=output_path,
            original_size_bytes=30000,
            compressed_size_bytes=15000,
            compression_ratio=0.5,
            processing_time_seconds=5.0
        )
        manager.video_processor.compress.return_value = expected_result

        result = await manager.compress_file(fixture_test_video_file_test, output_path, 25)

        assert result == expected_result
        manager.video_processor.compress.assert_called_once_with(fixture_test_video_file_test, 25, output_path)

    @pytest.mark.asyncio
    async def test_compress_file_audio(self, fixture_compression_manager_test, fixture_test_audio_file_test, fixture_temp_dir_test):
        """Test compressing audio file."""
        manager = fixture_compression_manager_test
        output_path = fixture_temp_dir_test / "output.mp3"

        # Mock audio processor
        expected_result = CompressionResult(
            success=True,
            input_path=fixture_test_audio_file_test,
            output_path=output_path,
            original_size_bytes=15000,
            compressed_size_bytes=8000,
            compression_ratio=0.53,
            processing_time_seconds=2.0
        )
        manager.audio_processor.compress.return_value = expected_result

        result = await manager.compress_file(fixture_test_audio_file_test, output_path, 25)

        assert result == expected_result
        manager.audio_processor.compress.assert_called_once_with(fixture_test_audio_file_test, 25, output_path)

    @pytest.mark.asyncio
    async def test_compress_file_image(self, fixture_compression_manager_test, fixture_test_image_file_test, fixture_temp_dir_test):
        """Test compressing image file."""
        manager = fixture_compression_manager_test
        output_path = fixture_temp_dir_test / "output.jpg"

        # Mock image processor
        expected_result = CompressionResult(
            success=True,
            input_path=fixture_test_image_file_test,
            output_path=output_path,
            original_size_bytes=6000,
            compressed_size_bytes=3000,
            compression_ratio=0.5,
            processing_time_seconds=1.0
        )
        manager.image_processor.compress.return_value = expected_result

        result = await manager.compress_file(fixture_test_image_file_test, output_path, 25)

        assert result == expected_result
        manager.image_processor.compress.assert_called_once_with(fixture_test_image_file_test, 25, output_path)

    @pytest.mark.asyncio
    async def test_compress_file_unsupported_type(self, fixture_compression_manager_test, fixture_temp_dir_test):
        """Test compressing unsupported file type."""
        manager = fixture_compression_manager_test

        # Create unsupported file
        unsupported_file = fixture_temp_dir_test / "document.txt"
        unsupported_file.write_text("This is a text document")
        output_path = fixture_temp_dir_test / "output.txt"

        with pytest.raises(CompressionError) as exc_info:
            await manager.compress_file(unsupported_file, output_path, 25)

        assert "Unsupported file type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compress_file_nonexistent_input(self, fixture_compression_manager_test, fixture_temp_dir_test):
        """Test compressing nonexistent input file."""
        manager = fixture_compression_manager_test

        nonexistent_file = fixture_temp_dir_test / "nonexistent.mp4"
        output_path = fixture_temp_dir_test / "output.mp4"

        with pytest.raises(CompressionError) as exc_info:
            await manager.compress_file(nonexistent_file, output_path, 25)

        assert "Input file does not exist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compress_file_auto_output_path(self, fixture_compression_manager_test, fixture_test_video_file_test):
        """Test compression with auto-generated output path."""
        manager = fixture_compression_manager_test

        # Mock video processor
        expected_output_path = fixture_test_video_file_test.parent / "test_video_compressed.mp4"
        expected_result = CompressionResult(
            success=True,
            input_path=fixture_test_video_file_test,
            output_path=expected_output_path,
            original_size_bytes=30000,
            compressed_size_bytes=15000,
            compression_ratio=0.5,
            processing_time_seconds=5.0
        )
        manager.video_processor.compress.return_value = expected_result

        result = await manager.compress_file(fixture_test_video_file_test, target_size_mb=25)

        assert result == expected_result
        # Verify the auto-generated path was used
        manager.video_processor.compress.assert_called_once_with(
            fixture_test_video_file_test, 25, expected_output_path
        )

    @pytest.mark.asyncio
    async def test_compress_file_with_compression_settings(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_compression_settings_test):
        """Test compression with custom compression settings."""
        manager = fixture_compression_manager_test

        expected_result = CompressionResult(
            success=True,
            input_path=fixture_test_video_file_test,
            output_path=None,
            original_size_bytes=30000,
            compressed_size_bytes=15000,
            compression_ratio=0.5,
            processing_time_seconds=5.0
        )
        manager.video_processor.compress.return_value = expected_result

        result = await manager.compress_file(
            fixture_test_video_file_test,
            compression_settings=fixture_compression_settings_test
        )

        assert result == expected_result
        # Should use target size from settings (25MB)
        manager.video_processor.compress.assert_called_once()
        args = manager.video_processor.compress.call_args[0]
        assert args[1] == 25  # target_size_mb from settings

    @pytest.mark.asyncio
    async def test_get_media_info_video(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_mock_media_info_test):
        """Test getting media info for video file."""
        manager = fixture_compression_manager_test
        manager.video_processor.get_media_info.return_value = fixture_mock_media_info_test

        result = await manager.get_media_info(fixture_test_video_file_test)

        assert result == fixture_mock_media_info_test
        manager.video_processor.get_media_info.assert_called_once_with(fixture_test_video_file_test)

    @pytest.mark.asyncio
    async def test_get_media_info_audio(self, fixture_compression_manager_test, fixture_test_audio_file_test, fixture_mock_media_info_test):
        """Test getting media info for audio file."""
        manager = fixture_compression_manager_test
        manager.audio_processor.get_media_info.return_value = fixture_mock_media_info_test

        result = await manager.get_media_info(fixture_test_audio_file_test)

        assert result == fixture_mock_media_info_test
        manager.audio_processor.get_media_info.assert_called_once_with(fixture_test_audio_file_test)

    @pytest.mark.asyncio
    async def test_get_media_info_unsupported(self, fixture_compression_manager_test, fixture_temp_dir_test):
        """Test getting media info for unsupported file."""
        manager = fixture_compression_manager_test

        unsupported_file = fixture_temp_dir_test / "document.txt"
        unsupported_file.write_text("This is a text document")

        with pytest.raises(CompressionError) as exc_info:
            await manager.get_media_info(unsupported_file)

        assert "Unsupported file type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compress_batch_success(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_test_audio_file_test, fixture_temp_dir_test):
        """Test successful batch compression."""
        manager = fixture_compression_manager_test

        # Mock processors
        video_result = CompressionResult(
            success=True,
            input_path=fixture_test_video_file_test,
            output_path=fixture_temp_dir_test / "test_video_compressed.mp4",
            original_size_bytes=30000,
            compressed_size_bytes=15000,
            compression_ratio=0.5,
            processing_time_seconds=5.0
        )
        audio_result = CompressionResult(
            success=True,
            input_path=fixture_test_audio_file_test,
            output_path=fixture_temp_dir_test / "test_audio_compressed.mp3",
            original_size_bytes=15000,
            compressed_size_bytes=8000,
            compression_ratio=0.53,
            processing_time_seconds=2.0
        )

        manager.video_processor.compress.return_value = video_result
        manager.audio_processor.compress.return_value = audio_result

        results = await manager.compress_batch(
            [fixture_test_video_file_test, fixture_test_audio_file_test],
            output_dir=fixture_temp_dir_test,
            target_size_mb=25
        )

        assert len(results) == 2
        assert results[0] == video_result
        assert results[1] == audio_result

    @pytest.mark.asyncio
    async def test_compress_batch_with_failures(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_temp_dir_test):
        """Test batch compression with some failures."""
        manager = fixture_compression_manager_test

        # Create nonexistent file for testing failure
        nonexistent_file = fixture_temp_dir_test / "nonexistent.mp4"

        # Mock successful compression for existing file
        success_result = CompressionResult(
            success=True,
            input_path=fixture_test_video_file_test,
            output_path=fixture_temp_dir_test / "test_video_compressed.mp4",
            original_size_bytes=30000,
            compressed_size_bytes=15000,
            compression_ratio=0.5,
            processing_time_seconds=5.0
        )
        manager.video_processor.compress.return_value = success_result

        results = await manager.compress_batch(
            [fixture_test_video_file_test, nonexistent_file],
            output_dir=fixture_temp_dir_test,
            target_size_mb=25
        )

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Input file does not exist" in results[1].error_message

    def test_is_supported_file(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_test_audio_file_test, fixture_test_image_file_test, fixture_temp_dir_test):
        """Test checking if file types are supported."""
        manager = fixture_compression_manager_test

        # Supported files
        assert manager.is_supported_file(fixture_test_video_file_test) is True
        assert manager.is_supported_file(fixture_test_audio_file_test) is True
        assert manager.is_supported_file(fixture_test_image_file_test) is True

        # Unsupported file
        unsupported_file = fixture_temp_dir_test / "document.txt"
        assert manager.is_supported_file(unsupported_file) is False

    def test_get_supported_extensions(self, fixture_compression_manager_test):
        """Test getting supported file extensions."""
        manager = fixture_compression_manager_test

        # Get all supported extensions
        all_extensions = manager.get_supported_extensions()
        assert 'mp4' in all_extensions
        assert 'mp3' in all_extensions
        assert 'jpg' in all_extensions

        # Get video extensions only
        video_extensions = manager.get_supported_extensions(MediaType.VIDEO)
        assert 'mp4' in video_extensions
        assert 'mp3' not in video_extensions
        assert 'jpg' not in video_extensions

    def test_get_processor_info(self, fixture_compression_manager_test):
        """Test getting processor information."""
        manager = fixture_compression_manager_test

        info = manager.get_processor_info()

        assert 'video' in info
        assert 'audio' in info
        assert 'image' in info

        # Check video processor info
        video_info = info['video']
        assert video_info['processor'] == 'VideoProcessor'
        assert video_info['min_video_bitrate_kbps'] == 125
        assert video_info['min_audio_bitrate_kbps'] == 32

        # Check audio processor info
        audio_info = info['audio']
        assert audio_info['processor'] == 'AudioProcessor'
        assert audio_info['min_bitrate_kbps'] == 32

        # Check image processor info
        image_info = info['image']
        assert image_info['processor'] == 'ImageProcessor'
        assert image_info['min_quality'] == 10

    def test_generate_output_path(self, fixture_compression_manager_test, fixture_test_video_file_test):
        """Test output path generation."""
        manager = fixture_compression_manager_test

        output_path = manager._generate_output_path(fixture_test_video_file_test)

        expected_path = fixture_test_video_file_test.parent / "test_video_compressed.mp4"
        assert output_path == expected_path

    def test_generate_output_filename(self, fixture_compression_manager_test, fixture_test_video_file_test):
        """Test output filename generation."""
        manager = fixture_compression_manager_test

        filename = manager._generate_output_filename(fixture_test_video_file_test)

        assert filename == "test_video_compressed.mp4"

    @pytest.mark.asyncio
    async def test_estimate_compression_time(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_test_audio_file_test, fixture_test_image_file_test, fixture_temp_dir_test):
        """Test compression time estimation."""
        manager = fixture_compression_manager_test

        # Test video file estimation
        video_time = await manager.estimate_compression_time(fixture_test_video_file_test)
        assert video_time is not None
        assert video_time > 0

        # Test audio file estimation
        audio_time = await manager.estimate_compression_time(fixture_test_audio_file_test)
        assert audio_time is not None
        assert audio_time > 0

        # Test image file estimation
        image_time = await manager.estimate_compression_time(fixture_test_image_file_test)
        assert image_time is not None
        assert image_time > 0

        # Test nonexistent file
        nonexistent_file = fixture_temp_dir_test / "nonexistent.mp4"
        result = await manager.estimate_compression_time(nonexistent_file)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_compression_feasible_success(self, fixture_compression_manager_test, fixture_test_video_file_test, fixture_mock_media_info_test):
        """Test successful compression feasibility validation."""
        manager = fixture_compression_manager_test
        manager.video_processor.get_media_info.return_value = fixture_mock_media_info_test

        is_feasible, reason = await manager.validate_compression_feasible(fixture_test_video_file_test, 25)

        assert is_feasible is True
        assert reason == ""

    @pytest.mark.asyncio
    async def test_validate_compression_feasible_already_small(self, fixture_compression_manager_test, fixture_test_video_file_test):
        """Test validation fails when file is already smaller than target."""
        manager = fixture_compression_manager_test

        # Mock small file
        small_media_info = MediaInfo(
            file_path=fixture_test_video_file_test,
            file_size_bytes=10 * 1024 * 1024,  # 10MB (smaller than 25MB target)
            duration_seconds=120.0,
            format_name="mp4",
            codec_name="h264",
            width=1920,
            height=1080,
            bitrate_kbps=700,
            metadata={}
        )
        manager.video_processor.get_media_info.return_value = small_media_info

        is_feasible, reason = await manager.validate_compression_feasible(fixture_test_video_file_test, 25)

        assert is_feasible is False
        assert "already" in reason and "smaller than target" in reason

    @pytest.mark.asyncio
    async def test_validate_compression_feasible_bitrate_too_low(self, fixture_compression_manager_test, fixture_test_video_file_test):
        """Test validation fails when required bitrate is too low."""
        manager = fixture_compression_manager_test

        # Mock very long video that would require very low bitrate
        long_media_info = MediaInfo(
            file_path=fixture_test_video_file_test,
            file_size_bytes=100 * 1024 * 1024,  # 100MB
            duration_seconds=10000.0,  # Very long duration
            format_name="mp4",
            codec_name="h264",
            width=1920,
            height=1080,
            bitrate_kbps=800,
            metadata={}
        )
        manager.video_processor.get_media_info.return_value = long_media_info

        is_feasible, reason = await manager.validate_compression_feasible(fixture_test_video_file_test, 5)  # Small target

        assert is_feasible is False
        assert "below minimum" in reason
