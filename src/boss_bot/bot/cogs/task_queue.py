"""Queue command cog implementation."""

import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


class QueueCog(commands.Cog):
    """Cog for handling queue-related commands."""

    def __init__(self, bot):
        """Initialize queue cog."""
        self.bot = bot

    @commands.command(name="clearqueue")
    @has_permissions(administrator=True)
    async def clear_queue(self, ctx: commands.Context):
        """Clear the entire download queue. Admin only."""
        try:
            # Create new empty queue
            self.bot.queue_manager.queue = asyncio.Queue(maxsize=self.bot.queue_manager.max_queue_size)
            await ctx.send("Queue cleared successfully.")
        except Exception as e:
            await ctx.send(f"Failed to clear queue: {e!s}")

    @commands.command(name="cancel")
    async def cancel_download(self, ctx: commands.Context, download_id: str):
        """Cancel a specific download."""
        try:
            # Check if download exists and belongs to user
            download = self.bot.download_manager.active_downloads.get(download_id)
            if not download:
                await ctx.send("Download not found.")
                return

            if download["user_id"] != ctx.author.id and not ctx.author.guild_permissions.administrator:
                await ctx.send("You can only cancel your own downloads.")
                return

            # Remove from active downloads
            self.bot.download_manager.active_downloads.pop(download_id)
            await ctx.send(f"Download {download_id} cancelled.")

        except Exception as e:
            await ctx.send(f"Failed to cancel download: {e!s}")

    @commands.command(name="queue")
    async def queue_status(self, ctx: commands.Context):
        """Show detailed queue status."""
        try:
            status = self.bot.queue_manager.get_queue_status()

            embed = discord.Embed(
                title="Current Queue Status",
                description="Current downloads and queue information",
                color=discord.Color.blue(),
            )

            # Queue stats
            embed.add_field(name="Downloads in Queue", value=status["total_items"], inline=True)
            embed.add_field(
                name="Queue Capacity",
                value=f"{status['total_items']}/{self.bot.queue_manager.max_queue_size}",
                inline=True,
            )

            # Active downloads
            active_count = len(self.bot.download_manager.active_downloads)
            embed.add_field(name="Active Downloads", value=active_count, inline=True)

            # Add footer with command help
            embed.set_footer(text="Use $dl <url> to add to queue | $cancel <id> to cancel a download")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Failed to get queue status: {e!s}")

    @clear_queue.error
    async def clear_queue_error(self, ctx: commands.Context, error):
        """Handle errors in clear_queue command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to clear the queue.")
        else:
            await ctx.send(f"An error occurred: {error!s}")


async def setup(bot):
    """Add cog to bot."""
    await bot.add_cog(QueueCog(bot))
