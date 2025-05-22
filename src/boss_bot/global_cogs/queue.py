"""Discord cog for managing the download queue."""

import logging
from typing import Optional

import discord
from discord.ext import commands

from boss_bot.core.env import BossSettings

logger = logging.getLogger(__name__)


class QueueCog(commands.Cog, name="Queue"):
    """Commands for managing the download queue."""

    def __init__(self, bot: commands.Bot):
        """Initialize the queue cog."""
        self.bot = bot
        self.settings = BossSettings()

    @commands.command(name="queue", aliases=["q"])
    async def show_queue(self, ctx: commands.Context, page: int | None = 1):
        """Show the current download queue.

        Args:
            ctx: The command context
            page: Optional page number for paginated results
        """
        try:
            # Get queue items
            queue_items = await self.bot.queue_manager.get_queue_items()

            if not queue_items:
                await ctx.send("The download queue is empty.")
                return

            # Calculate pagination
            items_per_page = 5
            total_pages = (len(queue_items) + items_per_page - 1) // items_per_page
            page = max(1, min(page, total_pages))
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page

            # Format queue items
            queue_list = []
            for idx, item in enumerate(queue_items[start_idx:end_idx], start=start_idx + 1):
                user = self.bot.get_user(item.user_id)
                username = user.name if user else "Unknown User"

                queue_list.append(f"{idx}. {item.filename or item.url} (Added by: {username}, ID: {item.download_id})")

            # Create embed
            embed = discord.Embed(title="Download Queue", description="\n".join(queue_list), color=discord.Color.blue())
            embed.set_footer(text=f"Page {page}/{total_pages} | Total items: {len(queue_items)}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing queue: {e}", exc_info=True)
            await ctx.send("An error occurred while getting queue information.")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_queue(self, ctx: commands.Context):
        """Clear the entire download queue (requires manage messages permission)."""
        try:
            await self.bot.queue_manager.clear_queue()
            await ctx.send("Download queue cleared.")

        except Exception as e:
            logger.error(f"Error clearing queue: {e}", exc_info=True)
            await ctx.send("An error occurred while clearing the queue.")

    @commands.command(name="remove")
    async def remove_from_queue(self, ctx: commands.Context, download_id: str):
        """Remove a specific item from the queue.

        Args:
            ctx: The command context
            download_id: The ID of the download to remove
        """
        try:
            if await self.bot.queue_manager.remove_from_queue(download_id, ctx.author.id):
                await ctx.send(f"Download {download_id} removed from queue.")
            else:
                await ctx.send(f"Download {download_id} not found or you don't have permission to remove it.")

        except Exception as e:
            logger.error(f"Error removing from queue: {e}", exc_info=True)
            await ctx.send("An error occurred while removing from queue.")

    @commands.command(name="pause")
    @commands.has_permissions(manage_messages=True)
    async def pause_queue(self, ctx: commands.Context):
        """Pause the download queue (requires manage messages permission)."""
        try:
            await self.bot.queue_manager.pause_queue()
            await ctx.send("Download queue paused. Current downloads will complete but no new downloads will start.")

        except Exception as e:
            logger.error(f"Error pausing queue: {e}", exc_info=True)
            await ctx.send("An error occurred while pausing the queue.")

    @commands.command(name="resume")
    @commands.has_permissions(manage_messages=True)
    async def resume_queue(self, ctx: commands.Context):
        """Resume the download queue (requires manage messages permission)."""
        try:
            await self.bot.queue_manager.resume_queue()
            await ctx.send("Download queue resumed. New downloads will now start.")

        except Exception as e:
            logger.error(f"Error resuming queue: {e}", exc_info=True)
            await ctx.send("An error occurred while resuming the queue.")


async def setup(bot: commands.Bot):
    """Add the queue cog to the bot."""
    await bot.add_cog(QueueCog(bot))
