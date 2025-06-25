# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false
"""Discord bot client implementation."""

import asyncio
import datetime
import gc
import logging
from collections import Counter, OrderedDict, defaultdict, namedtuple
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine, Iterable, MutableMapping
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    NoReturn,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

import discord
from discord import (
    Activity,
    AllowedMentions,
    AppInfo,
    DMChannel,
    Game,
    Guild,
    Intents,
    Message,
    Status,
    TextChannel,
    Thread,
    User,
)
from discord.ext import commands

from boss_bot.__version__ import __version__
from boss_bot.bot.bot_help import BossHelpCommand
from boss_bot.core.downloads.manager import DownloadManager
from boss_bot.core.env import BossSettings
from boss_bot.core.queue.manager import QueueManager

# AI agent imports (optional)
try:
    from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
    from boss_bot.ai.agents.strategy_selector import StrategySelector

    AI_AGENTS_AVAILABLE = True
except ImportError:
    AI_AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from discord.ext.commands.hybrid import CommandCallback, ContextT, P

_T = TypeVar("_T")

NotMessage = namedtuple("NotMessage", "guild")

DataDeletionResults = namedtuple("DataDeletionResults", "failed_modules failed_cogs unhandled")

PreInvokeCoroutine = Callable[[commands.Context], Awaitable[Any]]
T_BIC = TypeVar("T_BIC", bound=PreInvokeCoroutine)
UserOrRole = Union[int, discord.Role, discord.Member, discord.User]


class BossBot(commands.Bot):
    """Main Discord bot class for Boss-Bot."""

    # user: discord.ClientUser
    # old_tree_error = Callable[[discord.Interaction, discord.app_commands.AppCommandError], Coroutine[Any, Any, None]]

    def __init__(self, settings: BossSettings | None = None, command_prefix: str | None = None):
        """Initialize the bot with required configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.bans = True
        intents.emojis = True
        intents.voice_states = True
        intents.messages = True
        intents.reactions = True

        allowed_mentions = AllowedMentions(roles=False, everyone=False, users=True)

        # Store settings
        self.settings = settings or BossSettings()
        self._command_prefix = command_prefix or self.settings.prefix

        # Initialize base bot with custom help command
        super().__init__(
            # command_prefix="$",
            command_prefix=self._command_prefix,
            # description="Boss-Bot: A Discord Media Download Assistant",
            description="Boss-Bot: A Discord Media Download Assistant",
            allowed_mentions=allowed_mentions,
            intents=intents,
            help_command=BossHelpCommand(),
            chunk_guilds_at_startup=True,  # Enable automatic guild chunking
        )

        # Initialize services
        self.queue_manager = QueueManager(max_queue_size=self.settings.max_queue_size)
        self.download_manager = DownloadManager(
            settings=self.settings, max_concurrent_downloads=self.settings.max_concurrent_downloads
        )

        # Initialize bot attributes
        self.version: str = __version__
        self.guild_data: dict[int, dict[str, Any]] = {}
        self.bot_app_info: AppInfo | None = None
        self.owner_id: int | None = None
        self.invite: str | None = None
        self.uptime: datetime.datetime | None = None

        # Initialize AI agents if available and enabled
        self.strategy_selector: StrategySelector | None = None
        self.content_analyzer: ContentAnalyzer | None = None
        self._initialize_ai_agents()

        # Set up logging only if not already configured
        if not logging.root.handlers:
            logging.basicConfig(
                level=getattr(logging, self.settings.log_level.upper()),
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

    def _initialize_ai_agents(self) -> None:
        """Initialize AI agents if available and enabled."""
        if not AI_AGENTS_AVAILABLE:
            logger.info("AI agents not available - modules not found")
            return

        try:
            # Initialize Strategy Selector if enabled
            if hasattr(self.settings, "ai_strategy_selection_enabled") and getattr(
                self.settings, "ai_strategy_selection_enabled", False
            ):
                # Create a simple mock model for now (will be replaced with actual LLM)
                from types import SimpleNamespace

                mock_model = SimpleNamespace()
                mock_model.invoke = lambda x: {"content": "AI response"}

                self.strategy_selector = StrategySelector(
                    name="discord-strategy-selector",
                    model=mock_model,
                    system_prompt="Select the best download strategy for Discord bot users",
                )
                logger.info("Initialized AI Strategy Selector agent")

            # Initialize Content Analyzer if enabled
            if hasattr(self.settings, "ai_content_analysis_enabled") and getattr(
                self.settings, "ai_content_analysis_enabled", False
            ):
                # Create a simple mock model for now (will be replaced with actual LLM)
                from types import SimpleNamespace

                mock_model = SimpleNamespace()
                mock_model.invoke = lambda x: {"content": "AI analysis"}

                self.content_analyzer = ContentAnalyzer(
                    name="discord-content-analyzer",
                    model=mock_model,
                    system_prompt="Analyze content metadata for Discord bot users",
                )
                logger.info("Initialized AI Content Analyzer agent")

        except Exception as e:
            logger.error(f"Failed to initialize AI agents: {e}", exc_info=True)
            # Don't fail bot startup if AI agents fail to initialize
            self.strategy_selector = None
            self.content_analyzer = None

    async def setup_hook(self):
        """Initialize services and load extensions."""
        logger.info("Setting up bot services and extensions...")

        try:
            # Load command extensions
            await self.load_extension("boss_bot.bot.cogs.downloads")
            await self.load_extension("boss_bot.bot.cogs.queue")
            await self.load_extension("boss_bot.bot.cogs.admin")
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

    # async def on_connect(self):
    #     """Called when bot connects to Discord."""
    #     logger.info("Bot connected to Discord")
    #     await self._async_setup_hook()

    # async def on_disconnect(self):
    #     """Called when bot disconnects from Discord."""
    #     logger.warning("Bot disconnected from Discord")

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

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
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
