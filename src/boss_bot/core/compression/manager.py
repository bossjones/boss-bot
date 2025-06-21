"""Main compression manager class."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from boss_bot.core.compression.models import CompressionError, CompressionResult, CompressionSettings, MediaInfo
from boss_bot.core.compression.processors.audio_processor import AudioProcessor
from boss_bot.core.compression.processors.image_processor import ImageProcessor
from boss_bot.core.compression.processors.video_processor import VideoProcessor
from boss_bot.core.compression.utils.file_detector import FileTypeDetector, MediaType
from boss_bot.core.env import BossSettings


class CompressionManager:
    """Main compression manager that orchestrates all compression operations."""

    def __init__(self, settings: BossSettings):
        """Initialize compression manager.

        Args:
            settings: Boss-Bot settings
        """
        self.settings = settings
        self.file_detector = FileTypeDetector()

        # Initialize processors
        self.video_processor = VideoProcessor(settings)
        self.audio_processor = AudioProcessor(settings)
        self.image_processor = ImageProcessor(settings)

    async def compress_file(
        self,
        input_path: Path,
        output_path: Path | None = None,
        target_size_mb: int | None = None,
        compression_settings: CompressionSettings | None = None,
    ) -> CompressionResult:
        """Compress a media file.

        This is the main entry point for compression operations. It automatically
        detects the file type and routes to the appropriate processor.

        Args:
            input_path: Path to input file
            output_path: Optional output path (auto-generated if not provided)
            target_size_mb: Target size in MB (uses default if not provided)
            compression_settings: Optional compression settings

        Returns:
            CompressionResult with operation details

        Raises:
            CompressionError: If compression fails or file type is unsupported
        """
        if not input_path.exists():
            raise CompressionError(f"Input file does not exist: {input_path}")

        # Use compression settings or create default
        if compression_settings is None:
            compression_settings = CompressionSettings()

        # Use target size from settings if not provided
        if target_size_mb is None:
            target_size_mb = compression_settings.target_size_mb

        # Generate output path if not provided
        if output_path is None:
            output_path = self._generate_output_path(input_path)

        # Detect file type and route to appropriate processor
        media_type = self.file_detector.get_media_type(input_path)

        if media_type == MediaType.VIDEO:
            return await self.video_processor.compress(input_path, target_size_mb, output_path)
        elif media_type == MediaType.AUDIO:
            return await self.audio_processor.compress(input_path, target_size_mb, output_path)
        elif media_type == MediaType.IMAGE:
            return await self.image_processor.compress(input_path, target_size_mb, output_path)
        else:
            raise CompressionError(f"Unsupported file type: {input_path.suffix}")

    async def get_media_info(self, input_path: Path) -> MediaInfo:
        """Get media file information.

        Args:
            input_path: Path to media file

        Returns:
            MediaInfo with file details

        Raises:
            CompressionError: If file analysis fails or type is unsupported
        """
        if not input_path.exists():
            raise CompressionError(f"Input file does not exist: {input_path}")

        # Detect file type and route to appropriate processor
        media_type = self.file_detector.get_media_type(input_path)

        if media_type == MediaType.VIDEO:
            return await self.video_processor.get_media_info(input_path)
        elif media_type == MediaType.AUDIO:
            return await self.audio_processor.get_media_info(input_path)
        elif media_type == MediaType.IMAGE:
            return await self.image_processor.get_media_info(input_path)
        else:
            raise CompressionError(f"Unsupported file type: {input_path.suffix}")

    async def compress_batch(
        self,
        input_paths: list[Path],
        output_dir: Path | None = None,
        target_size_mb: int | None = None,
        max_concurrent: int = 3,
    ) -> list[CompressionResult]:
        """Compress multiple files concurrently.

        Args:
            input_paths: List of input file paths
            output_dir: Optional output directory (uses input directory if not provided)
            target_size_mb: Target size in MB for all files
            max_concurrent: Maximum number of concurrent compressions

        Returns:
            List of CompressionResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def compress_single(input_path: Path) -> CompressionResult:
            async with semaphore:
                try:
                    output_path = None
                    if output_dir:
                        output_path = output_dir / self._generate_output_filename(input_path)

                    return await self.compress_file(
                        input_path=input_path, output_path=output_path, target_size_mb=target_size_mb
                    )
                except Exception as e:
                    # Return failed result instead of raising
                    return CompressionResult(
                        success=False,
                        input_path=input_path,
                        output_path=None,
                        original_size_bytes=input_path.stat().st_size if input_path.exists() else 0,
                        compressed_size_bytes=0,
                        compression_ratio=0.0,
                        processing_time_seconds=0.0,
                        error_message=str(e),
                    )

        # Execute all compressions concurrently
        tasks = [compress_single(path) for path in input_paths]
        return await asyncio.gather(*tasks)

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported for compression.

        Args:
            file_path: Path to file

        Returns:
            True if file type is supported
        """
        return self.file_detector.is_supported_file(file_path)

    def get_supported_extensions(self, media_type: MediaType | None = None) -> list[str]:
        """Get list of supported file extensions.

        Args:
            media_type: Optional filter by media type

        Returns:
            List of supported extensions
        """
        extensions = self.file_detector.get_supported_extensions(media_type)
        return sorted(extensions)

    def get_processor_info(self) -> dict[str, Any]:
        """Get information about available processors.

        Returns:
            Dictionary with processor information
        """
        return {
            "video": {
                "processor": "VideoProcessor",
                "extensions": sorted(self.video_processor.supported_extensions),
                "min_video_bitrate_kbps": self.video_processor.min_video_bitrate_kbps,
                "min_audio_bitrate_kbps": self.video_processor.min_audio_bitrate_kbps,
            },
            "audio": {
                "processor": "AudioProcessor",
                "extensions": sorted(self.audio_processor.supported_extensions),
                "min_bitrate_kbps": self.audio_processor.min_bitrate_kbps,
            },
            "image": {
                "processor": "ImageProcessor",
                "extensions": sorted(self.image_processor.supported_extensions),
                "min_quality": self.image_processor.min_quality,
                "pil_available": getattr(self.image_processor, "PIL_AVAILABLE", False),
            },
        }

    def _generate_output_path(self, input_path: Path) -> Path:
        """Generate output file path based on input path.

        Args:
            input_path: Input file path

        Returns:
            Generated output path
        """
        stem = input_path.stem
        suffix = input_path.suffix
        parent = input_path.parent

        # Add compressed suffix to filename
        return parent / f"{stem}_compressed{suffix}"

    def _generate_output_filename(self, input_path: Path) -> str:
        """Generate output filename based on input path.

        Args:
            input_path: Input file path

        Returns:
            Generated output filename
        """
        stem = input_path.stem
        suffix = input_path.suffix

        # Add compressed suffix to filename
        return f"{stem}_compressed{suffix}"

    async def estimate_compression_time(self, input_path: Path) -> float | None:
        """Estimate compression time based on file size and type.

        This is a rough estimate based on typical compression speeds.

        Args:
            input_path: Path to input file

        Returns:
            Estimated time in seconds, or None if cannot estimate
        """
        if not input_path.exists():
            return None

        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        media_type = self.file_detector.get_media_type(input_path)

        # Rough estimates based on typical compression speeds
        # These are very approximate and depend on hardware
        if media_type == MediaType.VIDEO:
            # Video: ~1-2 MB/minute on average hardware
            return file_size_mb * 60  # seconds
        elif media_type == MediaType.AUDIO:
            # Audio: ~10-20 MB/minute
            return file_size_mb * 3  # seconds
        elif media_type == MediaType.IMAGE:
            # Images: very fast
            return max(1, file_size_mb * 0.1)  # seconds
        else:
            return None

    async def validate_compression_feasible(self, input_path: Path, target_size_mb: int) -> tuple[bool, str]:
        """Validate if compression to target size is feasible.

        Args:
            input_path: Path to input file
            target_size_mb: Target size in MB

        Returns:
            Tuple of (is_feasible, reason_if_not)
        """
        if not input_path.exists():
            return False, "Input file does not exist"

        try:
            media_info = await self.get_media_info(input_path)
            media_type = self.file_detector.get_media_type(input_path)

            # Check if file is already smaller than target
            current_size_mb = media_info.file_size_bytes / (1024 * 1024)
            if current_size_mb <= target_size_mb:
                return False, f"File is already {current_size_mb:.1f}MB, smaller than target {target_size_mb}MB"

            # For video/audio, check if minimum bitrates are achievable
            if media_type in [MediaType.VIDEO, MediaType.AUDIO] and media_info.duration_seconds:
                # Calculate what bitrate would be needed
                buffer_mb = 2
                effective_size_mb = max(1, target_size_mb - buffer_mb)
                required_bitrate = int(effective_size_mb * 8 * 1000 / media_info.duration_seconds)

                if media_type == MediaType.VIDEO:
                    # For video, need at least 125kbps for video + 32kbps for audio
                    min_total_bitrate = 125 + 32  # 157kbps minimum
                    if required_bitrate < min_total_bitrate:
                        return (
                            False,
                            f"Required bitrate {required_bitrate}kbps is below minimum {min_total_bitrate}kbps",
                        )

                elif media_type == MediaType.AUDIO:
                    # For audio, need at least 32kbps
                    min_bitrate = 32
                    if required_bitrate < min_bitrate:
                        return False, f"Required bitrate {required_bitrate}kbps is below minimum {min_bitrate}kbps"

            return True, ""

        except Exception as e:
            return False, f"Error validating compression: {e}"
