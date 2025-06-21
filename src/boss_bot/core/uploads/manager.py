"""Main upload manager for coordinating media file uploads."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from discord.ext import commands

from boss_bot.core.compression.manager import CompressionManager
from boss_bot.core.env import BossSettings
from boss_bot.core.uploads.models import MediaFile, UploadResult
from boss_bot.core.uploads.processors.discord_processor import DiscordUploadProcessor
from boss_bot.core.uploads.utils.file_detector import MediaFileDetector
from boss_bot.core.uploads.utils.size_analyzer import FileSizeAnalyzer


class UploadManager:
    """Manages the complete upload workflow with compression integration."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.compression_manager = CompressionManager(settings)
        self.discord_processor = DiscordUploadProcessor(settings)
        self.file_detector = MediaFileDetector()
        self.size_analyzer = FileSizeAnalyzer(settings)

    async def process_downloaded_files(
        self, download_dir: Path, ctx: commands.Context, platform_name: str
    ) -> UploadResult:
        """Main entry point: Process all files in download directory.

        Workflow:
        1. Detect media files in directory
        2. Analyze file sizes to determine upload strategy
        3. Compress oversized files using compression manager
        4. Upload files to Discord in optimized batches
        5. Handle failures gracefully with user feedback

        Args:
            download_dir: Directory containing downloaded files
            ctx: Discord context for sending messages
            platform_name: Name of the platform (e.g., "Twitter/X", "YouTube")

        Returns:
            UploadResult with comprehensive upload statistics
        """
        try:
            # Step 1: Find all media files in download directory
            media_files = await self.file_detector.find_media_files(download_dir)

            if not media_files:
                return UploadResult(success=False, message="No media files found to upload", files_processed=0)

            # Step 2: Analyze file sizes and categorize
            size_analysis = await self.size_analyzer.analyze_files(media_files)

            await ctx.send(
                f"📊 Found {size_analysis.total_files} media files ({size_analysis.total_size_mb:.1f}MB total)"
            )

            if size_analysis.oversized_files:
                await ctx.send(f"🗜️ {len(size_analysis.oversized_files)} files need compression")

            # Step 3: Compress files that exceed Discord limits
            compressed_files = await self._compress_oversized_files(size_analysis.oversized_files, ctx, platform_name)

            # Step 4: Prepare final upload list
            upload_files = size_analysis.acceptable_files + compressed_files

            if not upload_files:
                return UploadResult(
                    success=False,
                    message="No files available for upload after processing",
                    files_processed=size_analysis.total_files,
                )

            # Step 5: Upload to Discord in batches
            upload_result = await self.discord_processor.upload_files(upload_files, ctx, platform_name)

            # Add processing metadata
            upload_result.metadata.update(
                {
                    "original_files": size_analysis.total_files,
                    "compression_attempts": len(size_analysis.oversized_files),
                    "successful_compressions": len(compressed_files),
                    "total_original_size_mb": size_analysis.total_size_mb,
                }
            )

            return upload_result

        except Exception as e:
            error_msg = f"Upload processing failed: {e}"
            await ctx.send(f"❌ {error_msg}")

            return UploadResult(success=False, message=error_msg, error=str(e), files_processed=0)

    async def _compress_oversized_files(
        self, oversized_files: list[MediaFile], ctx: commands.Context, platform_name: str
    ) -> list[MediaFile]:
        """Compress files that are too large for Discord.

        Args:
            oversized_files: List of files that exceed Discord size limits
            ctx: Discord context for user feedback
            platform_name: Platform name for messages

        Returns:
            List of successfully compressed MediaFile objects
        """
        compressed_files = []

        for media_file in oversized_files:
            await ctx.send(
                f"🗜️ Compressing {media_file.filename} "
                f"({media_file.size_mb:.1f}MB → target: {self.size_analyzer.discord_limit_mb}MB)"
            )

            try:
                # Calculate target size slightly under Discord limit
                target_size_mb = self.size_analyzer.discord_limit_mb * 0.95

                compression_result = await self.compression_manager.compress_file(
                    media_file.path, target_size_mb=target_size_mb, output_dir=media_file.path.parent
                )

                if compression_result.success:
                    # Create new MediaFile for compressed version
                    compressed_media = MediaFile(
                        path=compression_result.output_path,
                        filename=compression_result.output_path.name,
                        size_bytes=compression_result.compressed_size_bytes,
                        media_type=media_file.media_type,
                        is_compressed=True,
                        original_path=media_file.path,
                    )
                    compressed_files.append(compressed_media)

                    await ctx.send(
                        f"✅ Compressed successfully! "
                        f"({compression_result.original_size_bytes // (1024 * 1024)}MB → "
                        f"{compression_result.compressed_size_bytes // (1024 * 1024)}MB, "
                        f"ratio: {compression_result.compression_ratio:.2f})"
                    )
                else:
                    await ctx.send(
                        f"❌ Compression failed for {media_file.filename}: "
                        f"{compression_result.error_message or 'Unknown error'}"
                    )

                    # Note: Could implement fallback storage here in the future
                    await ctx.send("💡 Consider using external storage or lower quality settings")

            except Exception as e:
                await ctx.send(f"❌ Compression error for {media_file.filename}: {e}")

        return compressed_files

    async def upload_single_file(
        self, file_path: Path, ctx: commands.Context, platform_name: str = "Unknown"
    ) -> UploadResult:
        """Upload a single file with compression if needed.

        Args:
            file_path: Path to the file to upload
            ctx: Discord context
            platform_name: Platform name for messages

        Returns:
            UploadResult for the single file upload
        """
        if not file_path.exists() or not file_path.is_file():
            return UploadResult(success=False, message=f"File not found: {file_path}", files_processed=0)

        # Create temporary directory containing just this file
        temp_dir = file_path.parent

        return await self.process_downloaded_files(temp_dir, ctx, platform_name)

    async def get_upload_preview(self, download_dir: Path) -> dict:
        """Get a preview of what would be uploaded without actually uploading.

        Args:
            download_dir: Directory to analyze

        Returns:
            Dictionary with upload preview information
        """
        media_files = await self.file_detector.find_media_files(download_dir)

        if not media_files:
            return {
                "total_files": 0,
                "total_size_mb": 0.0,
                "acceptable_files": 0,
                "files_needing_compression": 0,
                "estimated_batches": 0,
            }

        size_analysis = await self.size_analyzer.analyze_files(media_files)

        # Estimate batches
        estimated_batches = len(self.discord_processor.batch_processor.optimize_batches(size_analysis.acceptable_files))

        return {
            "total_files": size_analysis.total_files,
            "total_size_mb": size_analysis.total_size_mb,
            "acceptable_files": len(size_analysis.acceptable_files),
            "files_needing_compression": len(size_analysis.oversized_files),
            "estimated_batches": estimated_batches,
            "media_types": {
                file_type.value: len([f for f in media_files if f.media_type == file_type])
                for file_type in {f.media_type for f in media_files}
            },
        }
