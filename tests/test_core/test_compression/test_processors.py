"""Tests for compression processors."""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from boss_bot.core.compression.models import CompressionError, CompressionResult, MediaInfo
from boss_bot.core.compression.processors.base_processor import BaseProcessor
from boss_bot.core.compression.processors.video_processor import VideoProcessor
from boss_bot.core.compression.processors.audio_processor import AudioProcessor
from boss_bot.core.compression.processors.image_processor import ImageProcessor


class TestBaseProcessor:
    """Tests for BaseProcessor abstract class."""

    def test_base_processor_supports_file_extensions(self, fixture_boss_settings_test):
        """Test base processor file extension checking."""
        class TestProcessor(BaseProcessor):
            def __init__(self, settings):
                super().__init__(settings)
                self.supported_extensions = ['mp4', 'avi']

            async def compress(self, input_path, target_size_mb, output_path):
                pass

            async def get_media_info(self, input_path):
                pass

        processor = TestProcessor(fixture_boss_settings_test)

        assert processor.supports_file(Path("test.mp4")) is True
        assert processor.supports_file(Path("test.avi")) is True
        assert processor.supports_file(Path("test.mp3")) is False
        assert processor.supports_file(Path("test.MP4")) is True  # Case insensitive

    def test_base_processor_calculate_target_bitrate(self, fixture_boss_settings_test):
        """Test bitrate calculation in base processor."""
        class TestProcessor(BaseProcessor):
            def __init__(self, settings):
                super().__init__(settings)
                self.supported_extensions = ['mp4']

            async def compress(self, input_path, target_size_mb, output_path):
                pass

            async def get_media_info(self, input_path):
                pass

        processor = TestProcessor(fixture_boss_settings_test)

        # Test with 25MB target for 100 seconds: (25-2) * 8 * 1000 / 100 = 1840
        bitrate = processor._calculate_target_bitrate(25, 100.0)
        assert bitrate == 1840


class TestVideoProcessor:
    """Tests for VideoProcessor class."""

    @pytest.mark.asyncio
    async def test_video_processor_initialization(self, fixture_boss_settings_test):
        """Test video processor initialization."""
        processor = VideoProcessor(fixture_boss_settings_test)

        assert 'mp4' in processor.supported_extensions
        assert 'avi' in processor.supported_extensions
        assert 'mkv' in processor.supported_extensions
        assert processor.min_video_bitrate_kbps == 125
        assert processor.min_audio_bitrate_kbps == 32
        assert processor.video_bitrate_ratio == 0.9
        assert processor.audio_bitrate_ratio == 0.1

    @pytest.mark.asyncio
    async def test_video_processor_compress_success(self, fixture_video_processor_test, fixture_test_video_file_test, fixture_temp_dir_test, fixture_mock_media_info_test):
        """Test successful video compression."""
        processor = fixture_video_processor_test
        output_path = fixture_temp_dir_test / "output.mp4"

        # Mock media info and ffmpeg operations
        processor.ffmpeg.get_media_info.return_value = fixture_mock_media_info_test
        processor.ffmpeg.compress_video = AsyncMock()

        # Create output file to simulate successful compression
        output_path.write_bytes(b"compressed video content" * 1000)  # ~24KB

        result = await processor.compress(fixture_test_video_file_test, 25, output_path)

        assert result.success is True
        assert result.input_path == fixture_test_video_file_test
        assert result.output_path == output_path
        assert result.original_size_bytes > 0
        assert result.compressed_size_bytes > 0
        assert result.compression_ratio > 0
        assert result.processing_time_seconds > 0
        assert result.error_message is None

        # Verify ffmpeg was called with correct parameters
        processor.ffmpeg.compress_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_video_processor_compress_no_duration(self, fixture_video_processor_test, fixture_test_video_file_test, fixture_temp_dir_test):
        """Test video compression fails when no duration available."""
        processor = fixture_video_processor_test
        output_path = fixture_temp_dir_test / "output.mp4"

        # Mock media info without duration
        media_info = MediaInfo(
            file_path=fixture_test_video_file_test,
            file_size_bytes=1024,
            duration_seconds=None,  # No duration
            format_name="mp4",
            codec_name="h264",
            width=1920,
            height=1080,
            bitrate_kbps=2000,
            metadata={}
        )
        processor.ffmpeg.get_media_info.return_value = media_info

        result = await processor.compress(fixture_test_video_file_test, 25, output_path)

        assert result.success is False
        assert "Could not determine video duration" in result.error_message

    @pytest.mark.asyncio
    async def test_video_processor_compress_bitrate_too_low(self, fixture_video_processor_test, fixture_test_video_file_test, fixture_temp_dir_test):
        """Test video compression fails when calculated bitrate is too low."""
        processor = fixture_video_processor_test
        output_path = fixture_temp_dir_test / "output.mp4"

        # Mock media info with very long duration to cause low bitrate
        media_info = MediaInfo(
            file_path=fixture_test_video_file_test,
            file_size_bytes=1024,
            duration_seconds=10000.0,  # Very long duration
            format_name="mp4",
            codec_name="h264",
            width=1920,
            height=1080,
            bitrate_kbps=2000,
            metadata={}
        )
        processor.ffmpeg.get_media_info.return_value = media_info

        result = await processor.compress(fixture_test_video_file_test, 5, output_path)  # Small target size

        assert result.success is False
        assert "below minimum" in result.error_message

    @pytest.mark.asyncio
    async def test_video_processor_get_media_info(self, fixture_video_processor_test, fixture_test_video_file_test, fixture_mock_media_info_test):
        """Test getting video media info."""
        processor = fixture_video_processor_test
        processor.ffmpeg.get_media_info.return_value = fixture_mock_media_info_test

        result = await processor.get_media_info(fixture_test_video_file_test)

        assert result == fixture_mock_media_info_test
        processor.ffmpeg.get_media_info.assert_called_once_with(fixture_test_video_file_test)


class TestAudioProcessor:
    """Tests for AudioProcessor class."""

    @pytest.mark.asyncio
    async def test_audio_processor_initialization(self, fixture_boss_settings_test):
        """Test audio processor initialization."""
        processor = AudioProcessor(fixture_boss_settings_test)

        assert 'mp3' in processor.supported_extensions
        assert 'wav' in processor.supported_extensions
        assert 'm4a' in processor.supported_extensions
        assert processor.min_bitrate_kbps == 32

    @pytest.mark.asyncio
    async def test_audio_processor_compress_success(self, fixture_audio_processor_test, fixture_test_audio_file_test, fixture_temp_dir_test):
        """Test successful audio compression."""
        processor = fixture_audio_processor_test
        output_path = fixture_temp_dir_test / "output.mp3"

        # Mock media info
        media_info = MediaInfo(
            file_path=fixture_test_audio_file_test,
            file_size_bytes=15 * 1024,  # 15KB
            duration_seconds=60.0,
            format_name="mp3",
            codec_name="mp3",
            width=None,
            height=None,
            bitrate_kbps=128,
            metadata={}
        )
        processor.ffmpeg.get_media_info.return_value = media_info
        processor.ffmpeg.compress_audio = AsyncMock()

        # Create output file to simulate successful compression
        output_path.write_bytes(b"compressed audio content" * 500)  # ~12KB

        result = await processor.compress(fixture_test_audio_file_test, 25, output_path)

        assert result.success is True
        assert result.input_path == fixture_test_audio_file_test
        assert result.output_path == output_path
        assert result.original_size_bytes > 0
        assert result.compressed_size_bytes > 0
        assert result.compression_ratio > 0
        assert result.processing_time_seconds > 0
        assert result.error_message is None

        # Verify ffmpeg was called
        processor.ffmpeg.compress_audio.assert_called_once()

    @pytest.mark.asyncio
    async def test_audio_processor_compress_bitrate_too_low(self, fixture_audio_processor_test, fixture_test_audio_file_test, fixture_temp_dir_test):
        """Test audio compression fails when calculated bitrate is too low."""
        processor = fixture_audio_processor_test
        output_path = fixture_temp_dir_test / "output.mp3"

        # Mock media info with very long duration to cause low bitrate
        media_info = MediaInfo(
            file_path=fixture_test_audio_file_test,
            file_size_bytes=1024,
            duration_seconds=5000.0,  # Very long duration
            format_name="mp3",
            codec_name="mp3",
            width=None,
            height=None,
            bitrate_kbps=128,
            metadata={}
        )
        processor.ffmpeg.get_media_info.return_value = media_info

        result = await processor.compress(fixture_test_audio_file_test, 2, output_path)  # Small target size

        assert result.success is False
        assert "below minimum" in result.error_message

    @pytest.mark.asyncio
    async def test_audio_processor_get_media_info(self, fixture_audio_processor_test, fixture_test_audio_file_test, fixture_mock_media_info_test):
        """Test getting audio media info."""
        processor = fixture_audio_processor_test
        processor.ffmpeg.get_media_info.return_value = fixture_mock_media_info_test

        result = await processor.get_media_info(fixture_test_audio_file_test)

        assert result == fixture_mock_media_info_test
        processor.ffmpeg.get_media_info.assert_called_once_with(fixture_test_audio_file_test)


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    @pytest.mark.asyncio
    async def test_image_processor_initialization(self, fixture_boss_settings_test):
        """Test image processor initialization."""
        processor = ImageProcessor(fixture_boss_settings_test)

        assert 'jpg' in processor.supported_extensions
        assert 'png' in processor.supported_extensions
        assert 'gif' in processor.supported_extensions
        assert processor.min_quality == 10

    @pytest.mark.asyncio
    async def test_image_processor_compress_static_image(self, fixture_image_processor_test, fixture_test_image_file_test, fixture_temp_dir_test, fixture_mock_pil_image_test, mocker):
        """Test compressing static image with PIL."""
        processor = fixture_image_processor_test
        output_path = fixture_temp_dir_test / "output.jpg"

        # Mock PIL Image.open
        mock_open = mocker.patch('boss_bot.core.compression.processors.image_processor.Image.open')
        mock_open.return_value.__enter__.return_value = fixture_mock_pil_image_test

        # Mock the _find_optimal_quality method to simulate successful compression
        processor._find_optimal_quality = AsyncMock(return_value=(85, 5000))  # quality 85, 5KB

        result = await processor.compress(fixture_test_image_file_test, 25, output_path)

        assert result.success is True
        assert result.input_path == fixture_test_image_file_test
        assert result.output_path == output_path
        assert result.original_size_bytes > 0
        assert result.compressed_size_bytes == 5000
        assert result.compression_ratio > 0
        assert result.processing_time_seconds > 0
        assert result.error_message is None
        assert result.metadata["final_quality"] == 85

    @pytest.mark.asyncio
    async def test_image_processor_compress_gif(self, fixture_image_processor_test, fixture_test_gif_file_test, fixture_temp_dir_test, fixture_mock_media_info_test):
        """Test compressing animated GIF with ffmpeg."""
        processor = fixture_image_processor_test
        output_path = fixture_temp_dir_test / "output.gif"

        # Mock ffmpeg operations for GIF
        processor.ffmpeg.get_media_info.return_value = fixture_mock_media_info_test
        processor.ffmpeg._execute_ffmpeg_command = AsyncMock()

        # Create output file to simulate successful compression
        output_path.write_bytes(b"compressed gif content" * 100)  # ~2KB

        result = await processor.compress(fixture_test_gif_file_test, 25, output_path)

        assert result.success is True
        assert result.input_path == fixture_test_gif_file_test
        assert result.output_path == output_path
        assert result.compressed_size_bytes > 0
        assert result.metadata["method"] == "ffmpeg"

    @pytest.mark.asyncio
    async def test_image_processor_compress_pil_not_available(self, fixture_boss_settings_test, fixture_test_image_file_test, fixture_temp_dir_test, mocker):
        """Test image compression fails when PIL is not available."""
        # Mock PIL_AVAILABLE to False
        with patch('boss_bot.core.compression.processors.image_processor.PIL_AVAILABLE', False):
            processor = ImageProcessor(fixture_boss_settings_test)
            output_path = fixture_temp_dir_test / "output.jpg"

            result = await processor.compress(fixture_test_image_file_test, 25, output_path)

            assert result.success is False
            assert "PIL/Pillow not available" in result.error_message

    @pytest.mark.asyncio
    async def test_image_processor_get_media_info_static(self, fixture_image_processor_test, fixture_test_image_file_test, fixture_mock_pil_image_test, mocker):
        """Test getting media info for static image."""
        processor = fixture_image_processor_test

        # Mock PIL Image.open
        mock_open = mocker.patch('boss_bot.core.compression.processors.image_processor.Image.open')
        mock_open.return_value.__enter__.return_value = fixture_mock_pil_image_test

        result = await processor.get_media_info(fixture_test_image_file_test)

        assert result.file_path == fixture_test_image_file_test
        assert result.file_size_bytes > 0
        assert result.duration_seconds is None
        assert result.format_name == 'JPEG'
        assert result.width == 1920
        assert result.height == 1080

    @pytest.mark.asyncio
    async def test_image_processor_get_media_info_gif(self, fixture_image_processor_test, fixture_test_gif_file_test, fixture_mock_media_info_test):
        """Test getting media info for animated GIF."""
        processor = fixture_image_processor_test
        processor.ffmpeg.get_media_info.return_value = fixture_mock_media_info_test

        result = await processor.get_media_info(fixture_test_gif_file_test)

        assert result == fixture_mock_media_info_test
        processor.ffmpeg.get_media_info.assert_called_once_with(fixture_test_gif_file_test)

    @pytest.mark.asyncio
    async def test_image_processor_find_optimal_quality(self, fixture_image_processor_test, fixture_mock_pil_image_test, fixture_temp_dir_test):
        """Test finding optimal quality for image compression."""
        processor = fixture_image_processor_test
        output_path = fixture_temp_dir_test / "test_output.jpg"
        target_size = 10 * 1024  # 10KB target

        # Create the file first so stat() works
        output_path.write_bytes(b"test content")

        # Mock the save method to simulate different file sizes based on quality
        original_save = fixture_mock_pil_image_test.save
        call_count = 0

        def mock_save(path, format=None, **kwargs):
            nonlocal call_count
            call_count += 1

            # First few calls create larger files, later calls create smaller files
            if call_count <= 3:
                path.write_bytes(b"large content" * 1200)  # ~15KB
            else:
                path.write_bytes(b"small content" * 800)   # ~10KB

        fixture_mock_pil_image_test.save = mock_save

        quality, size = await processor._find_optimal_quality(
            fixture_mock_pil_image_test, output_path, "JPEG", target_size
        )

        assert quality <= 95
        assert quality >= processor.min_quality
        assert size <= target_size or quality == processor.min_quality
