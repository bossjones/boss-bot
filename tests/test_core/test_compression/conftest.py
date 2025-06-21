"""Test configuration and fixtures for compression module tests."""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from boss_bot.core.env import BossSettings
from boss_bot.core.compression.models import MediaInfo, CompressionSettings
from boss_bot.core.compression.manager import CompressionManager
from boss_bot.core.compression.processors.video_processor import VideoProcessor
from boss_bot.core.compression.processors.audio_processor import AudioProcessor
from boss_bot.core.compression.processors.image_processor import ImageProcessor
from boss_bot.core.compression.utils.ffmpeg_utils import FFmpegWrapper
from boss_bot.core.compression.utils.file_detector import FileTypeDetector


@pytest.fixture(scope="function")
def fixture_compression_settings_test() -> CompressionSettings:
    """Create test compression settings."""
    return CompressionSettings(
        target_size_mb=25,
        ffmpeg_preset="fast",
        max_concurrent=2
    )


@pytest.fixture(scope="function")
def fixture_boss_settings_test() -> BossSettings:
    """Create test BossSettings with compression configuration."""
    return BossSettings(
        discord_token="test_token_12345",
        openai_api_key="sk-test123",
        langchain_api_key="lsv2_test123",
        langchain_hub_api_key="lsv2_hub_test123",
        compression_target_size_mb=50,
        compression_ffmpeg_preset="slow",
        compression_ffmpeg_path="/usr/bin/ffmpeg",
        compression_ffprobe_path="/usr/bin/ffprobe",
        compression_max_concurrent=3,
        compression_min_video_bitrate_kbps=125,
        compression_min_audio_bitrate_kbps=32,
        compression_image_min_quality=10
    )


@pytest.fixture(scope="function")
def fixture_temp_dir_test(tmp_path):
    """Create temporary directory for test files."""
    return tmp_path


@pytest.fixture(scope="function")
def fixture_test_video_file_test(fixture_temp_dir_test):
    """Create a test video file."""
    video_file = fixture_temp_dir_test / "test_video.mp4"
    # Create a minimal file for testing
    video_file.write_bytes(b"fake video content for testing" * 1000)  # ~30KB
    return video_file


@pytest.fixture(scope="function")
def fixture_test_audio_file_test(fixture_temp_dir_test):
    """Create a test audio file."""
    audio_file = fixture_temp_dir_test / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio content for testing" * 500)  # ~15KB
    return audio_file


@pytest.fixture(scope="function")
def fixture_test_image_file_test(fixture_temp_dir_test):
    """Create a test image file."""
    image_file = fixture_temp_dir_test / "test_image.jpg"
    image_file.write_bytes(b"fake image content for testing" * 200)  # ~6KB
    return image_file


@pytest.fixture(scope="function")
def fixture_test_gif_file_test(fixture_temp_dir_test):
    """Create a test GIF file."""
    gif_file = fixture_temp_dir_test / "test_animation.gif"
    gif_file.write_bytes(b"fake gif content for testing" * 300)  # ~9KB
    return gif_file


@pytest.fixture(scope="function")
def fixture_mock_media_info_test() -> MediaInfo:
    """Create mock media info for testing."""
    return MediaInfo(
        file_path=Path("/test/file.mp4"),
        file_size_bytes=50 * 1024 * 1024,  # 50MB
        duration_seconds=120.0,  # 2 minutes
        format_name="mp4",
        codec_name="h264",
        width=1920,
        height=1080,
        bitrate_kbps=2000,
        metadata={"container": "mp4"}
    )


@pytest.fixture(scope="function")
def fixture_mock_ffmpeg_wrapper_test(mocker) -> Mock:
    """Create mock FFmpeg wrapper."""
    mock_wrapper = mocker.Mock(spec=FFmpegWrapper)
    mock_wrapper.ffmpeg_path = "/usr/bin/ffmpeg"
    mock_wrapper.ffprobe_path = "/usr/bin/ffprobe"

    # Mock async methods
    mock_wrapper.get_media_info = mocker.AsyncMock()
    mock_wrapper.compress_video = mocker.AsyncMock()
    mock_wrapper.compress_audio = mocker.AsyncMock()
    mock_wrapper._execute_ffmpeg_command = mocker.AsyncMock()

    return mock_wrapper


@pytest.fixture(scope="function")
def fixture_compression_manager_test(fixture_boss_settings_test, mocker) -> CompressionManager:
    """Create compression manager with mocked dependencies."""
    # Mock the processors to avoid actual FFmpeg calls
    with patch('boss_bot.core.compression.manager.VideoProcessor') as mock_video, \
         patch('boss_bot.core.compression.manager.AudioProcessor') as mock_audio, \
         patch('boss_bot.core.compression.manager.ImageProcessor') as mock_image:

        manager = CompressionManager(fixture_boss_settings_test)

        # Setup mocked processors
        manager.video_processor = mocker.Mock(spec=VideoProcessor)
        manager.audio_processor = mocker.Mock(spec=AudioProcessor)
        manager.image_processor = mocker.Mock(spec=ImageProcessor)

        # Mock processor methods
        manager.video_processor.compress = mocker.AsyncMock()
        manager.video_processor.get_media_info = mocker.AsyncMock()
        manager.video_processor.supported_extensions = ['mp4', 'avi', 'mkv']
        manager.video_processor.min_video_bitrate_kbps = 125
        manager.video_processor.min_audio_bitrate_kbps = 32

        manager.audio_processor.compress = mocker.AsyncMock()
        manager.audio_processor.get_media_info = mocker.AsyncMock()
        manager.audio_processor.supported_extensions = ['mp3', 'wav', 'm4a']
        manager.audio_processor.min_bitrate_kbps = 32

        manager.image_processor.compress = mocker.AsyncMock()
        manager.image_processor.get_media_info = mocker.AsyncMock()
        manager.image_processor.supported_extensions = ['jpg', 'png', 'gif']
        manager.image_processor.min_quality = 10
        manager.image_processor.PIL_AVAILABLE = True

        return manager


@pytest.fixture(scope="function")
def fixture_file_detector_test() -> FileTypeDetector:
    """Create file type detector for testing."""
    return FileTypeDetector()


@pytest.fixture(scope="function")
def fixture_video_processor_test(fixture_boss_settings_test, fixture_mock_ffmpeg_wrapper_test) -> VideoProcessor:
    """Create video processor with mocked FFmpeg wrapper."""
    processor = VideoProcessor(fixture_boss_settings_test)
    processor.ffmpeg = fixture_mock_ffmpeg_wrapper_test
    return processor


@pytest.fixture(scope="function")
def fixture_audio_processor_test(fixture_boss_settings_test, fixture_mock_ffmpeg_wrapper_test) -> AudioProcessor:
    """Create audio processor with mocked FFmpeg wrapper."""
    processor = AudioProcessor(fixture_boss_settings_test)
    processor.ffmpeg = fixture_mock_ffmpeg_wrapper_test
    return processor


@pytest.fixture(scope="function")
def fixture_image_processor_test(fixture_boss_settings_test, fixture_mock_ffmpeg_wrapper_test) -> ImageProcessor:
    """Create image processor with mocked FFmpeg wrapper."""
    processor = ImageProcessor(fixture_boss_settings_test)
    processor.ffmpeg = fixture_mock_ffmpeg_wrapper_test
    return processor


@pytest.fixture(scope="function")
def fixture_mock_pil_image_test(mocker):
    """Create mock PIL Image for testing."""
    mock_image = mocker.Mock()
    mock_image.mode = 'RGB'
    mock_image.size = (1920, 1080)
    mock_image.format = 'JPEG'
    mock_image.width = 1920
    mock_image.height = 1080
    mock_image.save = mocker.Mock()
    mock_image.convert = mocker.Mock(return_value=mock_image)

    return mock_image
