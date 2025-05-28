"""Discord cog for managing the download queue."""

import math

import discord
from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.core.core_queue import QueueItem


class QueueCog(commands.Cog):
    """Cog for managing the download queue."""

    def __init__(self, bot: BossBot):
        """Initialize the cog with bot instance."""
        self.bot = bot
        self.items_per_page = 5

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context, page: int = 1):
        """Show the current download queue.

        Args:
            ctx: The command context
            page: The page number to display (default: 1)
        """
        items = await self.bot.queue_manager.get_queue_items()

        if not items:
            await ctx.send("The download queue is empty.")
            return

        # Calculate pagination
        total_pages = math.ceil(len(items) / self.items_per_page)
        page = min(max(1, page), total_pages)
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = items[start_idx:end_idx]

        # Create embed
        embed = discord.Embed(title="📥 Download Queue", color=discord.Color.blue())

        # Add queue items to embed
        description = ""
        for item in page_items:
            user = self.bot.get_user(item.user_id)
            username = user.name if user else "Unknown User"
            filename = item.filename if hasattr(item, "filename") else "Unnamed"
            description += f"• {filename} (Added by {username})\n"

        embed.description = description
        embed.set_footer(text=f"Page {page}/{total_pages}")

        await ctx.send(embed=embed)

    @commands.command(name="clear")
    async def clear_queue(self, ctx: commands.Context):
        """Clear the download queue.

        Args:
            ctx: The command context
        """
        await self.bot.queue_manager.clear_queue()
        await ctx.send("Download queue cleared.")

    @commands.command(name="remove")
    async def remove_from_queue(self, ctx: commands.Context, download_id: str):
        """Remove a download from the queue.

        Args:
            ctx: The command context
            download_id: The ID of the download to remove
        """
        if await self.bot.queue_manager.remove_from_queue(download_id):
            await ctx.send(f"Download {download_id} removed from queue.")
        else:
            await ctx.send(f"Download {download_id} not found or you don't have permission to remove it.")

    @commands.command(name="pause")
    async def pause_queue(self, ctx: commands.Context):
        """Pause the download queue.

        Args:
            ctx: The command context
        """
        await self.bot.queue_manager.pause_queue()
        await ctx.send("Download queue paused. Current downloads will complete but no new downloads will start.")

    @commands.command(name="resume")
    async def resume_queue(self, ctx: commands.Context):
        """Resume the download queue.

        Args:
            ctx: The command context
        """
        await self.bot.queue_manager.resume_queue()
        await ctx.send("Download queue resumed. New downloads will now start.")

    # Event Handlers
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready."""
        print(f"{type(self).__name__} Cog ready.")

    # Command Error Handlers
    @show_queue.error
    async def queue_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the queue command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in queue command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while showing the queue.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @clear_queue.error
    async def clear_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the clear command."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="Sorry, you need `MANAGE SERVER` permissions to clear the download queue!",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in clear command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while clearing the queue.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @remove_from_queue.error
    async def remove_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the remove command."""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"Please provide a download ID to remove. Usage: `{self.bot.command_prefix}remove <download_id>`",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in remove command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while removing from queue.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @pause_queue.error
    async def pause_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the pause command."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="Sorry, you need `MANAGE SERVER` permissions to pause the download queue!",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in pause command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while pausing the queue.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @resume_queue.error
    async def resume_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the resume command."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="Sorry, you need `MANAGE SERVER` permissions to resume the download queue!",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in resume command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while resuming the queue.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)


async def setup(bot: BossBot):
    """Load the QueueCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(QueueCog(bot))
