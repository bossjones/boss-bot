"""Discord bot for managing downloads."""

import discord
from discord.ext import commands

from boss_bot.downloaders.base import DownloadManager
from boss_bot.settings import BossSettings


class BossBot(commands.Bot):
    """Discord bot for managing downloads."""

    def __init__(self, settings: BossSettings, **kwargs):
        """Initialize the bot.

        Args:
            settings: BossSettings instance
            **kwargs: Additional arguments to pass to discord.Client
        """
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize with command prefix and intents
        super().__init__(command_prefix="$", intents=intents, **kwargs)
        self.settings = settings
        self.download_manager = DownloadManager(settings=self.settings)
