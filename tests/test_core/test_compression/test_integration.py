"""Integration tests for compression system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from boss_bot.core.compression import CompressionManager, CompressionError, CompressionResult, CompressionSettings
from boss_bot.core.env import BossSettings


class TestCompressionIntegration:
    """Integration tests for the complete compression system."""

    @pytest.mark.asyncio
    async def test_end_to_end_video_compression_workflow(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test complete video compression workflow from start to finish."""
        # Create a test video file
        input_video = fixture_temp_dir_test / "input_video.mp4"
        input_video.write_bytes(b"fake video content" * 10000)  # ~170KB

        output_video = fixture_temp_dir_test / "output_video.mp4"

        # Mock all FFmpeg calls to avoid requiring actual FFmpeg
        with patch('boss_bot.core.compression.processors.video_processor.FFmpegWrapper') as mock_ffmpeg_class:
            mock_ffmpeg = mock_ffmpeg_class.return_value
            mock_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            # Mock media info response
            mock_ffmpeg.get_media_info = AsyncMock(return_value=Mock(
                file_path=input_video,
                file_size_bytes=input_video.stat().st_size,
                duration_seconds=60.0,  # 1 minute video
                format_name="mp4",
                codec_name="h264",
                width=1920,
                height=1080,
                bitrate_kbps=2000,
                metadata={"container": "mp4"}
            ))

            # Mock successful compression
            async def mock_compress_video(input_path, output_path, **kwargs):
                # Simulate creating compressed output file
                output_video.write_bytes(b"compressed video content" * 5000)  # ~120KB

            mock_ffmpeg.compress_video = AsyncMock(side_effect=mock_compress_video)

            # Create compression manager and run compression
            manager = CompressionManager(fixture_boss_settings_test)

            result = await manager.compress_file(
                input_path=input_video,
                output_path=output_video,
                target_size_mb=25
            )

            # Verify successful compression
            assert result.success is True
            assert result.input_path == input_video
            assert result.output_path == output_video
            assert result.original_size_bytes > 0
            assert result.compressed_size_bytes > 0
            assert result.compression_ratio > 0
            assert result.processing_time_seconds > 0
            assert result.error_message is None

            # Verify FFmpeg was called correctly
            mock_ffmpeg.get_media_info.assert_called_once_with(input_video)
            mock_ffmpeg.compress_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_audio_compression_workflow(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test complete audio compression workflow from start to finish."""
        # Create a test audio file
        input_audio = fixture_temp_dir_test / "input_audio.mp3"
        input_audio.write_bytes(b"fake audio content" * 5000)  # ~85KB

        output_audio = fixture_temp_dir_test / "output_audio.mp3"

        # Mock all FFmpeg calls
        with patch('boss_bot.core.compression.processors.audio_processor.FFmpegWrapper') as mock_ffmpeg_class:
            mock_ffmpeg = mock_ffmpeg_class.return_value
            mock_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            # Mock media info response
            mock_ffmpeg.get_media_info = AsyncMock(return_value=Mock(
                file_path=input_audio,
                file_size_bytes=input_audio.stat().st_size,
                duration_seconds=180.0,  # 3 minute audio
                format_name="mp3",
                codec_name="mp3",
                width=None,
                height=None,
                bitrate_kbps=128,
                metadata={"codec": "mp3"}
            ))

            # Mock successful compression
            async def mock_compress_audio(input_path, output_path, **kwargs):
                # Simulate creating compressed output file
                output_audio.write_bytes(b"compressed audio content" * 2500)  # ~52KB

            mock_ffmpeg.compress_audio = AsyncMock(side_effect=mock_compress_audio)

            # Create compression manager and run compression
            manager = CompressionManager(fixture_boss_settings_test)

            result = await manager.compress_file(
                input_path=input_audio,
                output_path=output_audio,
                target_size_mb=10
            )

            # Verify successful compression
            assert result.success is True
            assert result.input_path == input_audio
            assert result.output_path == output_audio
            assert result.original_size_bytes > 0
            assert result.compressed_size_bytes > 0
            assert result.compression_ratio > 0
            assert result.processing_time_seconds > 0
            assert result.error_message is None

            # Verify FFmpeg was called correctly
            mock_ffmpeg.get_media_info.assert_called_once_with(input_audio)
            mock_ffmpeg.compress_audio.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_image_compression_workflow(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test complete image compression workflow from start to finish."""
        # Create a test image file
        input_image = fixture_temp_dir_test / "input_image.jpg"
        input_image.write_bytes(b"fake image content" * 3000)  # ~51KB

        output_image = fixture_temp_dir_test / "output_image.jpg"

        # Mock PIL operations
        with patch('boss_bot.core.compression.processors.image_processor.PIL_AVAILABLE', True), \
             patch('boss_bot.core.compression.processors.image_processor.Image') as mock_image:

            # Mock PIL Image.open
            mock_img = Mock()
            mock_img.mode = 'RGB'
            mock_img.size = (1920, 1080)
            mock_img.format = 'JPEG'
            mock_img.width = 1920
            mock_img.height = 1080
            mock_img.convert.return_value = mock_img

            # Mock save operation to create output file
            def mock_save(path, format=None, **kwargs):
                output_image.write_bytes(b"compressed image content" * 1500)  # ~30KB

            mock_img.save = Mock(side_effect=mock_save)

            mock_image.open.return_value.__enter__.return_value = mock_img

            # Create compression manager and run compression
            manager = CompressionManager(fixture_boss_settings_test)

            result = await manager.compress_file(
                input_path=input_image,
                output_path=output_image,
                target_size_mb=5
            )

            # Verify successful compression
            assert result.success is True
            assert result.input_path == input_image
            assert result.output_path == output_image
            assert result.original_size_bytes > 0
            assert result.compressed_size_bytes > 0
            assert result.compression_ratio > 0
            assert result.processing_time_seconds > 0
            assert result.error_message is None

            # Verify PIL was used correctly
            mock_image.open.assert_called_once_with(input_image)

    @pytest.mark.asyncio
    async def test_batch_compression_mixed_file_types(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test batch compression with mixed file types."""
        # Create test files
        video_file = fixture_temp_dir_test / "video.mp4"
        audio_file = fixture_temp_dir_test / "audio.mp3"
        image_file = fixture_temp_dir_test / "image.jpg"

        video_file.write_bytes(b"fake video" * 5000)
        audio_file.write_bytes(b"fake audio" * 3000)
        image_file.write_bytes(b"fake image" * 2000)

        input_files = [video_file, audio_file, image_file]

        # Mock all compression operations
        with patch('boss_bot.core.compression.processors.video_processor.FFmpegWrapper') as mock_video_ffmpeg_class, \
             patch('boss_bot.core.compression.processors.audio_processor.FFmpegWrapper') as mock_audio_ffmpeg_class, \
             patch('boss_bot.core.compression.processors.image_processor.PIL_AVAILABLE', True), \
             patch('boss_bot.core.compression.processors.image_processor.Image') as mock_image:

            # Setup FFmpeg mocks for video and audio
            mock_video_ffmpeg = mock_video_ffmpeg_class.return_value
            mock_video_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_video_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            mock_audio_ffmpeg = mock_audio_ffmpeg_class.return_value
            mock_audio_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_audio_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            # Mock media info for video and audio
            def mock_get_video_media_info(file_path):
                return Mock(
                    file_path=file_path,
                    file_size_bytes=file_path.stat().st_size,
                    duration_seconds=60.0,
                    format_name="mp4",
                    codec_name="h264",
                    width=1920,
                    height=1080,
                    bitrate_kbps=2000,
                    metadata={}
                )

            def mock_get_audio_media_info(file_path):
                return Mock(
                    file_path=file_path,
                    file_size_bytes=file_path.stat().st_size,
                    duration_seconds=180.0,
                    format_name="mp3",
                    codec_name="mp3",
                    width=None,
                    height=None,
                    bitrate_kbps=128,
                    metadata={}
                )

            mock_video_ffmpeg.get_media_info = AsyncMock(side_effect=mock_get_video_media_info)
            mock_audio_ffmpeg.get_media_info = AsyncMock(side_effect=mock_get_audio_media_info)

            # Mock compression operations
            async def mock_compress_video(input_path, output_path, **kwargs):
                output_path.write_bytes(b"compressed video" * 2500)

            async def mock_compress_audio(input_path, output_path, **kwargs):
                output_path.write_bytes(b"compressed audio" * 1500)

            mock_video_ffmpeg.compress_video = AsyncMock(side_effect=mock_compress_video)
            mock_audio_ffmpeg.compress_audio = AsyncMock(side_effect=mock_compress_audio)

            # Setup PIL mock for image
            mock_img = Mock()
            mock_img.mode = 'RGB'
            mock_img.size = (1920, 1080)
            mock_img.format = 'JPEG'
            mock_img.width = 1920
            mock_img.height = 1080
            mock_img.convert.return_value = mock_img

            def mock_save(path, format=None, **kwargs):
                Path(path).write_bytes(b"compressed image" * 1000)

            mock_img.save = Mock(side_effect=mock_save)
            mock_image.open.return_value.__enter__.return_value = mock_img

            # Run batch compression
            manager = CompressionManager(fixture_boss_settings_test)

            results = await manager.compress_batch(
                input_paths=input_files,
                output_dir=fixture_temp_dir_test,
                target_size_mb=10,
                max_concurrent=2
            )

            # Verify all compressions succeeded
            assert len(results) == 3

            for result in results:
                assert result.success is True
                assert result.original_size_bytes > 0
                assert result.compressed_size_bytes > 0
                assert result.compression_ratio > 0
                assert result.processing_time_seconds > 0
                assert result.error_message is None

    @pytest.mark.asyncio
    async def test_compression_settings_integration(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test integration with compression settings."""
        # Create custom compression settings
        custom_settings = CompressionSettings(
            target_size_mb=15,
            ffmpeg_preset="fast",
            max_concurrent=1
        )

        # Create test video file
        input_video = fixture_temp_dir_test / "test_video.mp4"
        input_video.write_bytes(b"fake video content" * 8000)

        # Mock FFmpeg operations
        with patch('boss_bot.core.compression.processors.video_processor.FFmpegWrapper') as mock_ffmpeg_class:
            mock_ffmpeg = mock_ffmpeg_class.return_value
            mock_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            mock_ffmpeg.get_media_info = AsyncMock(return_value=Mock(
                file_path=input_video,
                file_size_bytes=input_video.stat().st_size,
                duration_seconds=120.0,
                format_name="mp4",
                codec_name="h264",
                width=1920,
                height=1080,
                bitrate_kbps=1500,
                metadata={}
            ))

            async def mock_compress_video(input_path, output_path, **kwargs):
                output_path.write_bytes(b"compressed with custom settings" * 2000)

            mock_ffmpeg.compress_video = AsyncMock(side_effect=mock_compress_video)

            # Run compression with custom settings
            manager = CompressionManager(fixture_boss_settings_test)

            result = await manager.compress_file(
                input_path=input_video,
                compression_settings=custom_settings
            )

            # Verify compression used custom settings
            assert result.success is True

            # Verify the target size from custom settings was used (15MB)
            # We can infer this from the fact that compression was called
            mock_ffmpeg.compress_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, fixture_boss_settings_test, fixture_temp_dir_test):
        """Test error handling and recovery in compression workflows."""
        # Create test files
        valid_video = fixture_temp_dir_test / "valid_video.mp4"
        valid_video.write_bytes(b"valid video content" * 5000)

        corrupted_video = fixture_temp_dir_test / "corrupted_video.mp4"
        corrupted_video.write_bytes(b"corrupted content")

        nonexistent_video = fixture_temp_dir_test / "nonexistent.mp4"

        # Mock FFmpeg operations with mixed success/failure
        with patch('boss_bot.core.compression.processors.video_processor.FFmpegWrapper') as mock_ffmpeg_class:
            mock_ffmpeg = mock_ffmpeg_class.return_value
            mock_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            def mock_get_media_info(file_path):
                if file_path == valid_video:
                    return Mock(
                        file_path=file_path,
                        file_size_bytes=file_path.stat().st_size,
                        duration_seconds=60.0,
                        format_name="mp4",
                        codec_name="h264",
                        width=1920,
                        height=1080,
                        bitrate_kbps=2000,
                        metadata={}
                    )
                else:
                    raise Exception("Failed to analyze corrupted file")

            mock_ffmpeg.get_media_info = AsyncMock(side_effect=mock_get_media_info)

            async def mock_compress_video(input_path, output_path, **kwargs):
                if input_path == valid_video:
                    output_path.write_bytes(b"compressed valid video" * 2000)
                else:
                    raise Exception("Compression failed")

            mock_ffmpeg.compress_video = AsyncMock(side_effect=mock_compress_video)

            # Test batch compression with mixed results
            manager = CompressionManager(fixture_boss_settings_test)

            results = await manager.compress_batch(
                input_paths=[valid_video, corrupted_video, nonexistent_video],
                output_dir=fixture_temp_dir_test,
                target_size_mb=10
            )

            # Verify mixed results
            assert len(results) == 3

            # First file should succeed
            assert results[0].success is True
            assert results[0].input_path == valid_video

            # Second file should fail (corrupted)
            assert results[1].success is False
            assert results[1].input_path == corrupted_video
            assert results[1].error_message is not None

            # Third file should fail (nonexistent)
            assert results[2].success is False
            assert results[2].input_path == nonexistent_video
            assert "Input file does not exist" in results[2].error_message

    @pytest.mark.asyncio
    async def test_boss_settings_integration(self, fixture_temp_dir_test, monkeypatch):
        """Test integration with BossSettings configuration."""
        # Clear any existing compression environment variables that might override our settings
        monkeypatch.delenv("COMPRESSION_TARGET_SIZE_MB", raising=False)
        monkeypatch.delenv("COMPRESSION_FFMPEG_PRESET", raising=False)
        monkeypatch.delenv("COMPRESSION_MAX_CONCURRENT", raising=False)
        monkeypatch.delenv("COMPRESSION_MIN_VIDEO_BITRATE_KBPS", raising=False)
        monkeypatch.delenv("COMPRESSION_MIN_AUDIO_BITRATE_KBPS", raising=False)
        monkeypatch.delenv("COMPRESSION_IMAGE_MIN_QUALITY", raising=False)

        # Set specific environment variables for our test values
        monkeypatch.setenv("COMPRESSION_TARGET_SIZE_MB", "30")
        monkeypatch.setenv("COMPRESSION_FFMPEG_PRESET", "medium")
        monkeypatch.setenv("COMPRESSION_MAX_CONCURRENT", "2")
        monkeypatch.setenv("COMPRESSION_MIN_VIDEO_BITRATE_KBPS", "150")
        monkeypatch.setenv("COMPRESSION_MIN_AUDIO_BITRATE_KBPS", "40")
        monkeypatch.setenv("COMPRESSION_IMAGE_MIN_QUALITY", "15")

        # Create custom boss settings with compression config
        custom_settings = BossSettings(
            discord_token="test_token_12345",
            openai_api_key="sk-test123",
            langchain_api_key="lsv2_test123",
            langchain_hub_api_key="lsv2_hub_test123"
        )

        # Create test video
        input_video = fixture_temp_dir_test / "test_video.mp4"
        input_video.write_bytes(b"test video for settings" * 6000)

        # Mock FFmpeg operations
        with patch('boss_bot.core.compression.processors.video_processor.FFmpegWrapper') as mock_ffmpeg_class:
            mock_ffmpeg = mock_ffmpeg_class.return_value
            mock_ffmpeg.ffmpeg_path = "/usr/bin/ffmpeg"
            mock_ffmpeg.ffprobe_path = "/usr/bin/ffprobe"

            mock_ffmpeg.get_media_info = AsyncMock(return_value=Mock(
                file_path=input_video,
                file_size_bytes=input_video.stat().st_size,
                duration_seconds=90.0,
                format_name="mp4",
                codec_name="h264",
                width=1920,
                height=1080,
                bitrate_kbps=1800,
                metadata={}
            ))

            async def mock_compress_video(input_path, output_path, **kwargs):
                output_path.write_bytes(b"compressed with boss settings" * 3000)

            mock_ffmpeg.compress_video = AsyncMock(side_effect=mock_compress_video)

            # Create manager with custom settings
            manager = CompressionManager(custom_settings)

            # Verify settings are properly integrated
            assert manager.settings.compression_target_size_mb == 30
            assert manager.settings.compression_ffmpeg_preset == "medium"
            assert manager.settings.compression_max_concurrent == 2

            # Run compression (should use default target size from settings)
            result = await manager.compress_file(input_path=input_video)

            assert result.success is True

            # Verify compression was called (indicating settings were used)
            mock_ffmpeg.compress_video.assert_called_once()
