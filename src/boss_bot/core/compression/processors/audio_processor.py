"""Audio file compression processor."""

import time
from pathlib import Path
from typing import List

from boss_bot.core.compression.models import CompressionError, CompressionResult, MediaInfo
from boss_bot.core.compression.processors.base_processor import BaseProcessor
from boss_bot.core.compression.utils.bitrate_calculator import BitrateCalculator
from boss_bot.core.compression.utils.ffmpeg_utils import FFmpegWrapper
from boss_bot.core.env import BossSettings


class AudioProcessor(BaseProcessor):
    """Handles audio file compression."""

    def __init__(self, settings: BossSettings):
        """Initialize audio processor.

        Args:
            settings: Boss-Bot settings
        """
        super().__init__(settings)
        self.supported_extensions = ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma"]
        self.min_bitrate_kbps = 32

        self.ffmpeg = FFmpegWrapper(settings)
        self.bitrate_calc = BitrateCalculator()

    async def compress(self, input_path: Path, target_size_mb: int, output_path: Path) -> CompressionResult:
        """Compress audio file using the same logic as bash script.

        Steps:
        1. Get duration using ffprobe
        2. Calculate target bitrate: (target_size_mb * 8 * 1000) / duration
        3. Apply minimum bitrate threshold
        4. Execute ffmpeg compression with libmp3lame

        Args:
            input_path: Input audio file path
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
                raise CompressionError(f"Could not determine audio duration for {input_path}")

            # Step 2: Calculate target bitrate
            target_bitrate = self._calculate_target_bitrate(target_size_mb, media_info.duration_seconds)

            # Step 3: Apply minimum threshold
            if target_bitrate < self.min_bitrate_kbps:
                raise CompressionError(
                    f"Target bitrate {target_bitrate}kbps is below minimum {self.min_bitrate_kbps}kbps"
                )

            # Step 4: Execute ffmpeg compression
            await self.ffmpeg.compress_audio(
                input_path=input_path, output_path=output_path, bitrate_kbps=target_bitrate
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
                    "duration_seconds": media_info.duration_seconds,
                    "codec": "libmp3lame",
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
        """Get audio file information.

        Args:
            input_path: Path to audio file

        Returns:
            MediaInfo with audio file details

        Raises:
            CompressionError: If file analysis fails
        """
        try:
            return await self.ffmpeg.get_media_info(input_path)
        except Exception as e:
            raise CompressionError(f"Failed to get media info for {input_path}: {e}")

    def _execute_ffmpeg_compression(self, input_path: Path, output_path: Path, target_bitrate: int) -> None:
        """Placeholder for async compatibility.

        This method signature matches the plan but the actual work is done
        in the compress method using FFmpegWrapper.
        """
        # This is handled by the main compress method
        pass
