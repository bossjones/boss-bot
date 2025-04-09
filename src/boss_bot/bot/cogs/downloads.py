"""Download command cog implementation."""

import uuid
from datetime import datetime

import discord
from discord.ext import commands

from boss_bot.core.core_queue import QueueItem, QueueStatus


class DownloadCog(commands.Cog):
    """Cog for handling download commands."""

    def __init__(self, bot):
        """Initialize download cog."""
        self.bot = bot

    @commands.command(name="dl")
    async def download(self, ctx: commands.Context, url: str):
        """Download media from supported platforms."""
        try:
            # Validate URL
            if not await self.bot.download_manager.validate_url(url):
                await ctx.send("Invalid URL. Please provide a valid Twitter or Reddit URL.")
                return

            # Create download item
            download_id = str(uuid.uuid4())
            queue_item = QueueItem(
                id=download_id,
                url=url,
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                status=QueueStatus.QUEUED,
                created_at=datetime.now(),
            )

            # Add to queue
            try:
                await self.bot.queue_manager.add_download(queue_item)
            except ValueError:
                await ctx.send("Queue is currently full. Please try again later.")
                return

            # Get queue position
            position = self.bot.queue_manager.get_queue_size()

            await ctx.send(f"Download started! Your position in queue: {position}\nUse `$queue` to check queue status.")

        except Exception as e:
            await ctx.send(f"An error occurred: {e!s}")

    @commands.command(name="queue")
    async def queue_status(self, ctx: commands.Context):
        """Show current queue status."""
        status = self.bot.queue_manager.get_queue_status()

        embed = discord.Embed(title="Current Queue Status", color=discord.Color.blue())

        embed.add_field(name="Downloads in Queue", value=status["total_items"], inline=True)
        embed.add_field(
            name="Queue Capacity", value=f"{status['total_items']}/{self.bot.queue_manager.max_queue_size}", inline=True
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Add cog to bot."""
    await bot.add_cog(DownloadCog(bot))
