"""Discord-specific upload processor with batch handling."""

from __future__ import annotations

import asyncio
from typing import List

import discord
from discord.ext import commands

from boss_bot.core.env import BossSettings
from boss_bot.core.uploads.models import MediaFile, UploadBatch, UploadResult
from boss_bot.core.uploads.utils.batch_processor import BatchProcessor


class DiscordUploadProcessor:
    """Handles Discord-specific upload logic."""

    def __init__(self, settings: BossSettings):
        self.settings = settings
        self.batch_processor = BatchProcessor(settings)
        self.max_files_per_message = 10  # Discord's limit
        self.max_message_size_mb = 25  # Discord's default limit

        # Configurable retry settings
        self.max_retries = 3
        self.retry_delay = 2.0

    async def upload_files(
        self, media_files: list[MediaFile], ctx: commands.Context, platform_name: str
    ) -> UploadResult:
        """Upload media files to Discord in optimized batches.

        Args:
            media_files: List of media files to upload
            ctx: Discord context for sending messages
            platform_name: Name of the platform (for user messages)

        Returns:
            UploadResult with upload statistics and status
        """
        if not media_files:
            return UploadResult(success=True, message="No files to upload", files_processed=0)

        # Create upload batches respecting Discord limits
        batches = self.batch_processor.optimize_batches(media_files)

        if not batches:
            return UploadResult(success=False, message="Failed to create upload batches", files_processed=0)

        successful_uploads = 0
        failed_uploads = 0
        total_files = len(media_files)

        # Process each batch
        for i, batch in enumerate(batches):
            try:
                batch_result = await self._upload_batch(batch, ctx, platform_name, i + 1, len(batches))

                successful_uploads += batch_result.successful_uploads
                failed_uploads += batch_result.failed_uploads

            except Exception as e:
                await ctx.send(f"❌ Batch {i + 1} upload failed: {e}")
                failed_uploads += len(batch.files)

        # Calculate final result
        success_rate = successful_uploads / total_files if total_files > 0 else 0

        return UploadResult(
            success=success_rate > 0.5,  # Success if > 50% uploaded
            message=f"Upload complete: {successful_uploads}/{total_files} files uploaded",
            files_processed=total_files,
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            metadata={"platform": platform_name, "batches_processed": len(batches), "success_rate": success_rate},
        )

    async def _upload_batch(
        self, batch: UploadBatch, ctx: commands.Context, platform_name: str, batch_num: int, total_batches: int
    ) -> UploadResult:
        """Upload a single batch of files.

        Args:
            batch: Upload batch to process
            ctx: Discord context
            platform_name: Platform name for messages
            batch_num: Current batch number
            total_batches: Total number of batches

        Returns:
            UploadResult for this batch
        """
        # Validate batch before upload
        if not self.batch_processor.validate_batch(batch):
            return UploadResult(
                success=False,
                message=f"Batch {batch_num} validation failed",
                files_processed=len(batch.files),
                failed_uploads=len(batch.files),
            )

        # Send batch progress message
        await self._send_batch_progress(ctx, batch, batch_num, total_batches, platform_name)

        # Attempt upload with retries
        for attempt in range(self.max_retries):
            try:
                return await self._attempt_batch_upload(batch, ctx, platform_name)

            except discord.HTTPException as e:
                if "Request entity too large" in str(e):
                    await ctx.send(
                        f"❌ Batch {batch_num} too large for Discord "
                        f"({batch.total_size_mb:.1f}MB). Consider enabling compression."
                    )
                    return UploadResult(
                        success=False,
                        message=f"Batch {batch_num} too large",
                        files_processed=len(batch.files),
                        failed_uploads=len(batch.files),
                        error=str(e),
                    )
                elif e.status == 429:  # Rate limited
                    retry_after = getattr(e, "retry_after", self.retry_delay)
                    if attempt < self.max_retries - 1:
                        await ctx.send(f"⏳ Rate limited. Retrying batch {batch_num} in {retry_after:.1f}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        await ctx.send(f"❌ Rate limit exceeded for batch {batch_num}")
                        return UploadResult(
                            success=False,
                            message="Rate limit exceeded",
                            files_processed=len(batch.files),
                            failed_uploads=len(batch.files),
                            error=str(e),
                        )
                else:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        await ctx.send(f"❌ Upload failed for batch {batch_num}: {e}")
                        return UploadResult(
                            success=False,
                            message=f"HTTP error: {e}",
                            files_processed=len(batch.files),
                            failed_uploads=len(batch.files),
                            error=str(e),
                        )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    await ctx.send(f"❌ Unexpected error in batch {batch_num}: {e}")
                    return UploadResult(
                        success=False,
                        message=f"Unexpected error: {e}",
                        files_processed=len(batch.files),
                        failed_uploads=len(batch.files),
                        error=str(e),
                    )

        # If we get here, all retries failed
        return UploadResult(
            success=False,
            message=f"All retries failed for batch {batch_num}",
            files_processed=len(batch.files),
            failed_uploads=len(batch.files),
        )

    async def _attempt_batch_upload(
        self, batch: UploadBatch, ctx: commands.Context, platform_name: str
    ) -> UploadResult:
        """Attempt to upload a batch of files.

        Args:
            batch: Upload batch
            ctx: Discord context
            platform_name: Platform name

        Returns:
            UploadResult for the upload attempt
        """
        discord_files = []
        failed_file_prep = 0

        # Prepare Discord File objects
        for media_file in batch.files:
            try:
                discord_file = discord.File(media_file.path, filename=media_file.filename)
                discord_files.append(discord_file)
            except Exception as e:
                await ctx.send(f"⚠️ Could not prepare {media_file.filename}: {e}")
                failed_file_prep += 1

        # Upload to Discord if we have files to upload
        if discord_files:
            upload_message = await ctx.send(f"🎯 {platform_name} media files:", files=discord_files)

            successful_uploads = len(discord_files)

            # Send compression metadata if applicable
            await self._send_compression_metadata(ctx, batch)

            return UploadResult(
                success=True,
                message=f"Uploaded {successful_uploads} files",
                files_processed=len(batch.files),
                successful_uploads=successful_uploads,
                failed_uploads=failed_file_prep,
            )
        else:
            return UploadResult(
                success=False,
                message="No files could be prepared for upload",
                files_processed=len(batch.files),
                failed_uploads=len(batch.files),
            )

    async def _send_batch_progress(
        self, ctx: commands.Context, batch: UploadBatch, batch_num: int, total_batches: int, platform_name: str
    ):
        """Send batch progress message to user.

        Args:
            ctx: Discord context
            batch: Upload batch
            batch_num: Current batch number
            total_batches: Total batches
            platform_name: Platform name
        """
        if not getattr(self.settings, "upload_enable_progress_updates", True):
            return

        batch_info = f"📎 Uploading batch {batch_num}/{total_batches}"

        if total_batches > 1:
            # Show preview of files in batch
            file_names = [f.filename for f in batch.files[:3]]
            if len(batch.files) > 3:
                file_names.append(f"... and {len(batch.files) - 3} more")
            batch_info += f": {', '.join(file_names)}"

        batch_info += f" ({batch.total_size_mb:.1f}MB)"

        await ctx.send(batch_info)

    async def _send_compression_metadata(self, ctx: commands.Context, batch: UploadBatch):
        """Send compression metadata for compressed files in batch.

        Args:
            ctx: Discord context
            batch: Upload batch
        """
        compressed_files = [f for f in batch.files if f.is_compressed]

        if compressed_files:
            metadata_lines = []
            for file_info in compressed_files:
                original_name = file_info.original_path.name if file_info.original_path else "unknown"
                metadata_lines.append(f"🗜️ {file_info.filename} (compressed from {original_name})")

            if metadata_lines:
                await ctx.send("ℹ️ **Compression Info:**\n" + "\n".join(metadata_lines))
