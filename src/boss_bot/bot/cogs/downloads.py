"""Discord cog for handling downloads."""

from discord.ext import commands

from boss_bot.bot.client import BossBot


class DownloadCog(commands.Cog):
    """Cog for handling downloads."""

    def __init__(self, bot: BossBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="download")
    async def download(self, ctx: commands.Context, url: str):
        """Download a video from a URL."""
        if not self.bot.download_manager.validate_url(url):
            await ctx.send("Invalid URL provided.")
            return

        try:
            await self.bot.queue_manager.add_to_queue(url, ctx.author.id, ctx.channel.id)
            await ctx.send(f"Added {url} to download queue.")
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """Show the current download status."""
        active_downloads = self.bot.download_manager.get_active_downloads()
        queue_size = self.bot.queue_manager.get_queue_size()
        await ctx.send(f"Active downloads: {active_downloads}\nQueue size: {queue_size}")


async def setup(bot: BossBot):
    """Load the DownloadCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(DownloadCog(bot))
