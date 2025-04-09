"""Discord bot client implementation."""

import discord
from discord.ext import commands

from boss_bot.core.queue import QueueManager
from boss_bot.downloaders.base import DownloadManager


class BossBot(commands.Bot):
    """Main Discord bot class for Boss-Bot."""

    def __init__(self):
        """Initialize the bot with required configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize base bot
        super().__init__(
            command_prefix="$", intents=intents, description="Boss-Bot: A Discord Media Download Assistant"
        )

        # Initialize services
        self.queue_manager = QueueManager()
        self.download_manager = DownloadManager()

    async def _async_setup_hook(self):
        """Initialize services and load extensions."""
        # Load command extensions
        await self.load_extension("boss_bot.cogs.downloads")
        await self.load_extension("boss_bot.cogs.queue")

    async def on_ready(self):
        """Called when bot is ready and connected."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
