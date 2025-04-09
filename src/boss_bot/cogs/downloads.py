"""Discord cog for handling download commands."""

import logging
from typing import Optional

import discord
from discord.ext import commands

from boss_bot.core.env import BossSettings
from boss_bot.storage.quotas import QuotaManager
from boss_bot.storage.validation import FileValidator

logger = logging.getLogger(__name__)


class DownloadCog(commands.Cog, name="Downloads"):
    """Commands for downloading media files."""

    def __init__(self, bot: commands.Bot):
        """Initialize the downloads cog."""
        self.bot = bot
        self.settings = BossSettings()
        self.validator = FileValidator()
        self.quota_manager = QuotaManager()

    @commands.command(name="download", aliases=["dl"])
    @commands.cooldown(1, 5, commands.BucketType.user)  # 1 use per 5 seconds per user
    async def download(self, ctx: commands.Context, url: str, *, filename: str | None = None):
        """Download media from the provided URL.

        Args:
            ctx: The command context
            url: The URL to download from
            filename: Optional custom filename for the download
        """
        # Basic validation
        if not url:
            await ctx.send("Please provide a URL to download from.")
            return

        # Validate URL and filename
        try:
            if filename:
                filename = self.validator.sanitize_filename(filename)

            if not self.validator.is_valid_url(url):
                await ctx.send("Invalid URL provided. Please check the URL and try again.")
                return

        except ValueError as e:
            await ctx.send(f"Invalid filename: {e!s}")
            return

        # Check quotas
        try:
            # We'll estimate 50MB for now since we don't know actual size
            estimated_size = 50 * 1024 * 1024  # 50MB in bytes
            if not self.quota_manager.check_quota(estimated_size):
                await ctx.send("Storage quota exceeded. Please wait for current downloads to complete.")
                return

        except Exception as e:
            logger.error(f"Error checking quotas: {e}", exc_info=True)
            await ctx.send("An error occurred while checking storage quotas. Please try again later.")
            return

        # Add to download queue
        try:
            # Add to queue
            queue_position = await self.bot.queue_manager.add_to_queue(
                url=url, user_id=ctx.author.id, channel_id=ctx.channel.id, filename=filename
            )

            await ctx.send(
                f"Added to download queue at position {queue_position}. You will be notified when the download starts."
            )

        except Exception as e:
            logger.error(f"Error adding to queue: {e}", exc_info=True)
            await ctx.send("An error occurred while adding to queue. Please try again later.")
            return

    @commands.command(name="cancel")
    async def cancel_download(self, ctx: commands.Context, download_id: str):
        """Cancel a download in progress or queued.

        Args:
            ctx: The command context
            download_id: The ID of the download to cancel
        """
        try:
            # Try to cancel from queue first
            if await self.bot.queue_manager.remove_from_queue(download_id, ctx.author.id):
                await ctx.send(f"Download {download_id} removed from queue.")
                return

            # If not in queue, try to cancel active download
            if await self.bot.download_manager.cancel_download(download_id, ctx.author.id):
                await ctx.send(f"Download {download_id} cancelled.")
                return

            await ctx.send(f"Download {download_id} not found or you don't have permission to cancel it.")

        except Exception as e:
            logger.error(f"Error cancelling download: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to cancel the download.")

    @commands.command(name="status")
    async def download_status(self, ctx: commands.Context, download_id: str | None = None):
        """Check the status of downloads.

        Args:
            ctx: The command context
            download_id: Optional specific download ID to check
        """
        try:
            if download_id:
                # Check specific download
                status = await self.bot.download_manager.get_download_status(download_id)
                if status:
                    await ctx.send(f"Download {download_id} status: {status}")
                else:
                    await ctx.send(f"Download {download_id} not found.")
            else:
                # Show overall status
                active = len(await self.bot.download_manager.get_active_downloads())
                queued = self.bot.queue_manager.queue_size
                quota = self.quota_manager.get_quota_status()

                status_msg = (
                    f"📥 Active downloads: {active}/{self.settings.max_concurrent_downloads}\n"
                    f"📋 Queued downloads: {queued}\n"
                    f"💾 Storage quota: {quota}"
                )
                await ctx.send(status_msg)

        except Exception as e:
            logger.error(f"Error getting download status: {e}", exc_info=True)
            await ctx.send("An error occurred while getting download status.")


async def setup(bot: commands.Bot):
    """Add the downloads cog to the bot."""
    await bot.add_cog(DownloadCog(bot))
