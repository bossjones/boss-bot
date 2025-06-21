"""Video file compression processor."""

import time
from pathlib import Path
from typing import List

from boss_bot.core.compression.models import CompressionError, CompressionResult, MediaInfo
from boss_bot.core.compression.processors.base_processor import BaseProcessor
from boss_bot.core.compression.utils.bitrate_calculator import BitrateCalculator
from boss_bot.core.compression.utils.ffmpeg_utils import FFmpegWrapper
from boss_bot.core.env import BossSettings


class VideoProcessor(BaseProcessor):
    """Handles video file compression."""

    def __init__(self, settings: BossSettings):
        """Initialize video processor.

        Args:
            settings: Boss-Bot settings
        """
        super().__init__(settings)
        self.supported_extensions = ["mp4", "avi", "mkv", "mov", "flv", "wmv", "webm", "mpeg", "3gp", "m4v"]
        self.min_video_bitrate_kbps = 125
        self.min_audio_bitrate_kbps = 32
        self.video_bitrate_ratio = 0.9  # 90% for video
        self.audio_bitrate_ratio = 0.1  # 10% for audio

        self.ffmpeg = FFmpegWrapper(settings)
        self.bitrate_calc = BitrateCalculator()

    async def compress(self, input_path: Path, target_size_mb: int, output_path: Path) -> CompressionResult:
        """Compress video file using the same logic as bash script.

        Steps:
        1. Get duration using ffprobe
        2. Calculate target bitrate: (target_size_mb * 8 * 1000) / duration
        3. Allocate 90% to video, 10% to audio
        4. Apply minimum bitrate thresholds
        5. Execute ffmpeg compression

        Args:
            input_path: Input video file path
            target_size_mb: Target size in MB
            output_path: Output file path

        Returns:
            CompressionResult with operation details

        Raises:
            CompressionError: If compression fails
        """
        start_time = time.time()
        original_size = input_path.stat().st_size

        try:
            # Step 1: Get media info
            media_info = await self.get_media_info(input_path)

            if not media_info.duration_seconds:
                raise CompressionError(f"Could not determine video duration for {input_path}")

            # Step 2: Calculate bitrates (replicating bash script logic)
            target_bitrate = self._calculate_target_bitrate(target_size_mb, media_info.duration_seconds)

            video_bitrate, audio_bitrate = self.bitrate_calc.allocate_video_audio_bitrates(
                target_bitrate, self.video_bitrate_ratio, self.audio_bitrate_ratio
            )

            # Step 3: Apply minimum thresholds
            is_valid, error_msg = self.bitrate_calc.validate_minimum_bitrates(
                video_bitrate, audio_bitrate, self.min_video_bitrate_kbps, self.min_audio_bitrate_kbps
            )

            if not is_valid:
                raise CompressionError(error_msg)

            # Step 4: Execute ffmpeg compression
            preset = getattr(self.settings, "compression_ffmpeg_preset", "slow")

            await self.ffmpeg.compress_video(
                input_path=input_path,
                output_path=output_path,
                video_bitrate_kbps=video_bitrate,
                audio_bitrate_kbps=audio_bitrate,
                max_bitrate_kbps=target_bitrate,
                preset=preset,
            )

            # Verify output file exists and get size
            if not output_path.exists():
                raise CompressionError(f"Output file was not created: {output_path}")

            compressed_size = output_path.stat().st_size
            processing_time = time.time() - start_time
            compression_ratio = compressed_size / original_size if original_size > 0 else 0

            return CompressionResult(
                success=True,
                input_path=input_path,
                output_path=output_path,
                original_size_bytes=original_size,
                compressed_size_bytes=compressed_size,
                compression_ratio=compression_ratio,
                processing_time_seconds=processing_time,
                metadata={
                    "target_bitrate_kbps": target_bitrate,
                    "video_bitrate_kbps": video_bitrate,
                    "audio_bitrate_kbps": audio_bitrate,
                    "duration_seconds": media_info.duration_seconds,
                    "preset": preset,
                },
            )

        except Exception as e:
            processing_time = time.time() - start_time

            # Clean up partial output file if it exists
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass

            return CompressionResult(
                success=False,
                input_path=input_path,
                output_path=None,
                original_size_bytes=original_size,
                compressed_size_bytes=0,
                compression_ratio=0.0,
                processing_time_seconds=processing_time,
                error_message=str(e),
            )

    async def get_media_info(self, input_path: Path) -> MediaInfo:
        """Get video file information.

        Args:
            input_path: Path to video file

        Returns:
            MediaInfo with video file details

        Raises:
            CompressionError: If file analysis fails
        """
        try:
            return await self.ffmpeg.get_media_info(input_path)
        except Exception as e:
            raise CompressionError(f"Failed to get media info for {input_path}: {e}")

    def _execute_ffmpeg_compression(
        self, input_path: Path, output_path: Path, video_bitrate: int, audio_bitrate: int, target_bitrate: int
    ) -> None:
        """Placeholder for async compatibility.

        This method signature matches the plan but the actual work is done
        in the compress method using FFmpegWrapper.
        """
        # This is handled by the main compress method
        pass
