"""Discord cog for managing the download queue."""

from discord.ext import commands

from boss_bot.bot.client import BossBot


class QueueCog(commands.Cog):
    """Cog for managing the download queue."""

    def __init__(self, bot: BossBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context, page: int = 1):
        """Show the current download queue."""
        queue = self.bot.queue_manager.get_queue()
        if not queue:
            await ctx.send("Queue is empty.")
            return

        items_per_page = 5
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = queue[start_idx:end_idx]

        queue_msg = "Current Queue:\n"
        for i, item in enumerate(page_items, start=start_idx + 1):
            queue_msg += f"{i}. {item['url']}\n"

        total_pages = (len(queue) + items_per_page - 1) // items_per_page
        queue_msg += f"\nPage {page} of {total_pages}"
        await ctx.send(queue_msg)

    @commands.command(name="clear")
    async def clear_queue(self, ctx: commands.Context):
        """Clear the download queue."""
        self.bot.queue_manager.clear_queue()
        await ctx.send("Queue cleared.")

    @commands.command(name="remove")
    async def remove_from_queue(self, ctx: commands.Context, index: int):
        """Remove an item from the queue by its index."""
        try:
            self.bot.queue_manager.remove_from_queue(index - 1)  # Convert to 0-based index
            await ctx.send(f"Removed item {index} from queue.")
        except IndexError:
            await ctx.send("Invalid queue index.")

    @commands.command(name="pause")
    async def pause_queue(self, ctx: commands.Context):
        """Pause the download queue."""
        self.bot.queue_manager.pause_queue()
        await ctx.send("Queue paused.")

    @commands.command(name="resume")
    async def resume_queue(self, ctx: commands.Context):
        """Resume the download queue."""
        self.bot.queue_manager.resume_queue()
        await ctx.send("Queue resumed.")
