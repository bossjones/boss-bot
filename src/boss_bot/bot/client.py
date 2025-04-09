"""Discord bot client implementation."""

import logging
from typing import Optional

import discord
from discord.ext import commands

from boss_bot.bot.bot_help import BossHelpCommand
from boss_bot.core.core_queue import QueueManager
from boss_bot.core.env import BossSettings
from boss_bot.downloaders.base import DownloadManager

logger = logging.getLogger(__name__)


class BossBot(commands.Bot):
    """Main Discord bot class for Boss-Bot."""

    def __init__(self, settings: BossSettings | None = None):
        """Initialize the bot with required configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize base bot with custom help command
        super().__init__(
            command_prefix="$",
            intents=intents,
            description="Boss-Bot: A Discord Media Download Assistant",
            help_command=BossHelpCommand(),
        )

        # Store settings
        self.settings = settings or BossSettings()

        # Initialize services
        self.queue_manager = QueueManager(max_queue_size=self.settings.max_queue_size)
        self.download_manager = DownloadManager(max_concurrent_downloads=self.settings.max_concurrent_downloads)

        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def _async_setup_hook(self):
        """Initialize services and load extensions."""
        logger.info("Setting up bot services and extensions...")

        try:
            # Load command extensions
            await self.load_extension("boss_bot.cogs.downloads")
            await self.load_extension("boss_bot.cogs.queue")
            logger.info("Successfully loaded all extensions")

        except Exception as e:
            logger.error(f"Failed to load extensions: {e}", exc_info=True)
            raise

    async def on_ready(self):
        """Called when bot is ready and connected."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"downloads | {self.command_prefix}help")
        await self.change_presence(activity=activity)

        logger.info("Bot is ready!")
        print("------")

    async def on_connect(self):
        """Called when bot connects to Discord."""
        logger.info("Bot connected to Discord")
        await self._async_setup_hook()

    async def on_disconnect(self):
        """Called when bot disconnects from Discord."""
        logger.warning("Bot disconnected from Discord")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"You don't have permission to use this command. Required permissions: {', '.join(error.missing_permissions)}"
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"You're on cooldown. Try again in {error.retry_after:.1f} seconds.")

        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command not found. Use {self.command_prefix}help to see available commands.")

        else:
            logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
            if self.settings.debug:
                await ctx.send(f"An error occurred: {error!s}")
            else:
                await ctx.send("An error occurred while processing your command. Please try again later.")

    async def on_error(self, event_method: str, *args, **kwargs):
        """Handle non-command errors."""
        logger.error(f"Error in {event_method}", exc_info=True)

        # If in debug mode, we might want to do additional error handling
        if self.settings.debug:
            logger.debug(f"Error details - Event: {event_method}, Args: {args}, Kwargs: {kwargs}")

    async def close(self):
        """Clean up resources when bot is shutting down."""
        logger.info("Bot is shutting down...")

        try:
            # Clean up services
            await self.queue_manager.cleanup()
            await self.download_manager.cleanup()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

        finally:
            await super().close()
