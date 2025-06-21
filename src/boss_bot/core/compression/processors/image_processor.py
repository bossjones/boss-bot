"""Image file compression processor."""

import asyncio
import time
from pathlib import Path
from typing import List, Tuple

from boss_bot.core.compression.models import CompressionError, CompressionResult, MediaInfo
from boss_bot.core.compression.processors.base_processor import BaseProcessor
from boss_bot.core.compression.utils.ffmpeg_utils import FFmpegWrapper
from boss_bot.core.env import BossSettings

try:
    from PIL import Image, ImageFile

    PIL_AVAILABLE = True
    # Enable loading of truncated images
    ImageFile.LOAD_TRUNCATED_IMAGES = True
except ImportError:
    PIL_AVAILABLE = False


class ImageProcessor(BaseProcessor):
    """Handles image file compression."""

    def __init__(self, settings: BossSettings):
        """Initialize image processor.

        Args:
            settings: Boss-Bot settings
        """
        super().__init__(settings)
        self.supported_extensions = ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]
        self.min_quality = 10  # Minimum quality percentage

        self.ffmpeg = FFmpegWrapper(settings)

    async def compress(self, input_path: Path, target_size_mb: int, output_path: Path) -> CompressionResult:
        """Compress image file using PIL/Pillow or ffmpeg.

        Steps:
        1. For static images: Use PIL with quality adjustment
        2. For animated images (GIF): Use ffmpeg
        3. Progressive quality reduction until target size is reached

        Args:
            input_path: Input image file path
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
            if input_path.suffix.lower() == ".gif":
                return await self._compress_animated_image(input_path, output_path, target_size_mb)
            else:
                return await self._compress_static_image(input_path, output_path, target_size_mb)

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

    async def _compress_static_image(
        self, input_path: Path, output_path: Path, target_size_mb: int
    ) -> CompressionResult:
        """Compress static image using PIL.

        Args:
            input_path: Input image path
            output_path: Output image path
            target_size_mb: Target size in MB

        Returns:
            CompressionResult
        """
        start_time = time.time()
        original_size = input_path.stat().st_size
        target_size_bytes = target_size_mb * 1024 * 1024

        if not PIL_AVAILABLE:
            raise CompressionError("PIL/Pillow not available for image compression")

        # Load image
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for JPEG output)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Determine output format
                output_format = "JPEG"
                if output_path.suffix.lower() in [".png"]:
                    output_format = "PNG"
                elif output_path.suffix.lower() in [".webp"]:
                    output_format = "WEBP"

                # Try progressive quality reduction
                quality, compressed_size = await self._find_optimal_quality(
                    img, output_path, output_format, target_size_bytes
                )

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
                        "final_quality": quality,
                        "format": output_format,
                        "original_mode": img.mode,
                        "dimensions": img.size,
                    },
                )

        except Exception as e:
            raise CompressionError(f"Failed to compress static image: {e}")

    async def _find_optimal_quality(
        self, img: "Image.Image", output_path: Path, output_format: str, target_size_bytes: int
    ) -> tuple[int, int]:
        """Find optimal quality setting for target size.

        Args:
            img: PIL Image object
            output_path: Output file path
            output_format: Output format (JPEG, PNG, WEBP)
            target_size_bytes: Target size in bytes

        Returns:
            Tuple of (final_quality, final_size_bytes)
        """
        # Start with high quality and reduce progressively
        for quality in range(95, self.min_quality - 1, -5):
            # Save with current quality
            save_kwargs = {}
            if output_format in ["JPEG", "WEBP"]:
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True

            img.save(output_path, format=output_format, **save_kwargs)

            # Check file size
            current_size = output_path.stat().st_size
            if current_size <= target_size_bytes:
                return quality, current_size

        # If we can't reach target size, use minimum quality
        save_kwargs = {}
        if output_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = self.min_quality
            save_kwargs["optimize"] = True

        img.save(output_path, format=output_format, **save_kwargs)
        final_size = output_path.stat().st_size

        return self.min_quality, final_size

    async def _compress_animated_image(
        self, input_path: Path, output_path: Path, target_size_mb: int
    ) -> CompressionResult:
        """Compress animated image (GIF) using ffmpeg.

        Args:
            input_path: Input GIF path
            output_path: Output GIF path
            target_size_mb: Target size in MB

        Returns:
            CompressionResult
        """
        start_time = time.time()
        original_size = input_path.stat().st_size
        target_size_bytes = target_size_mb * 1024 * 1024

        # Use ffmpeg for animated images
        # Calculate bitrate based on duration (if available)
        try:
            media_info = await self.ffmpeg.get_media_info(input_path)

            if media_info.duration_seconds:
                # Calculate target bitrate like video
                target_bitrate = self._calculate_target_bitrate(target_size_mb, media_info.duration_seconds)
            else:
                # Fallback: estimate based on file size
                target_bitrate = max(100, int(target_size_mb * 8 * 1000 / 10))  # Assume 10 second duration

            # Use ffmpeg to compress GIF
            cmd = [
                self.ffmpeg.ffmpeg_path,
                "-i",
                str(input_path),
                "-vf",
                "scale=iw*0.8:ih*0.8",  # Reduce size by 20%
                "-r",
                "15",  # Reduce frame rate
                "-y",
                str(output_path),
            ]

            await self.ffmpeg._execute_ffmpeg_command(cmd)

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
                    "method": "ffmpeg",
                    "target_bitrate_kbps": target_bitrate,
                    "duration_seconds": media_info.duration_seconds,
                },
            )

        except Exception as e:
            raise CompressionError(f"Failed to compress animated image: {e}")

    async def get_media_info(self, input_path: Path) -> MediaInfo:
        """Get image file information.

        Args:
            input_path: Path to image file

        Returns:
            MediaInfo with image file details

        Raises:
            CompressionError: If file analysis fails
        """
        try:
            file_size = input_path.stat().st_size

            # For animated images, use ffmpeg
            if input_path.suffix.lower() == ".gif":
                return await self.ffmpeg.get_media_info(input_path)

            # For static images, use PIL if available
            if PIL_AVAILABLE:
                try:
                    with Image.open(input_path) as img:
                        return MediaInfo(
                            file_path=input_path,
                            file_size_bytes=file_size,
                            duration_seconds=None,
                            format_name=img.format or "unknown",
                            codec_name=None,
                            width=img.width,
                            height=img.height,
                            bitrate_kbps=None,
                            metadata={
                                "mode": img.mode,
                                "has_transparency": img.mode in ("RGBA", "LA", "P"),
                            },
                        )
                except Exception:
                    # Fallback to basic file info
                    pass

            # Basic fallback info
            return MediaInfo(
                file_path=input_path,
                file_size_bytes=file_size,
                duration_seconds=None,
                format_name=input_path.suffix.lstrip(".").upper(),
                codec_name=None,
                width=None,
                height=None,
                bitrate_kbps=None,
                metadata={},
            )

        except Exception as e:
            raise CompressionError(f"Failed to get media info for {input_path}: {e}")
