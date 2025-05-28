# Discord Integration

This document covers Bot-specific patterns for Discord.py integration, including bot client architecture, cog development, event handling, and Discord-specific testing strategies.

## Discord.py Bot Architecture

### BossBot Client Design

```python
# src/boss_bot/bot/client.py
import discord
from discord.ext import commands
from boss_bot.core.env import BossSettings
from boss_bot.core.queue.manager import QueueManager
from boss_bot.core.downloads.manager import DownloadManager

class BossBot(commands.Bot):
    """Main Discord bot client with dependency injection and lifecycle management."""

    def __init__(self, settings: BossSettings):
        # Store configuration
        self.settings = settings

        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.guilds = True
        intents.members = False  # Don't need member events

        # Initialize bot with configuration
        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None,  # Custom help command
            case_insensitive=True,
            strip_after_prefix=True
        )

        # Initialize subsystems with dependency injection
        self.queue_manager = QueueManager(settings)
        self.download_manager = DownloadManager(settings)

        # Bot state tracking
        self._startup_complete = False
        self._shutdown_requested = False

    async def setup_hook(self):
        """Called when bot is starting up. Load cogs and initialize services."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")

        # Load cogs
        await self.load_extension('boss_bot.bot.cogs.downloads')
        await self.load_extension('boss_bot.bot.cogs.queue')

        # Initialize services
        await self.queue_manager.start()
        await self.download_manager.start()

        # Sync slash commands (development only)
        if self.settings.guild_ids:
            for guild_id in self.settings.guild_ids:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"Synced commands to guild {guild_id}")

        self._startup_complete = True
        print("Bot startup complete!")

    async def close(self):
        """Graceful shutdown with cleanup."""
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        print("Bot shutdown requested...")

        # Stop services
        await self.queue_manager.stop()
        await self.download_manager.stop()

        # Unload cogs
        for extension in list(self.extensions.keys()):
            await self.unload_extension(extension)

        # Close Discord connection
        await super().close()
        print("Bot shutdown complete.")

    @property
    def is_ready_and_operational(self) -> bool:
        """Check if bot is fully operational."""
        return (
            self.is_ready()
            and self._startup_complete
            and not self._shutdown_requested
        )
```

### Bot Lifecycle Events

```python
# src/boss_bot/bot/events/lifecycle.py
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class LifecycleEvents(commands.Cog):
    """Handle bot lifecycle events."""

    def __init__(self, bot: BossBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when bot connects to Discord."""
        logger.info(f"Bot connected as {self.bot.user}")
        logger.info(f"Connected to {len(self.bot.guilds)} guilds")

        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.bot.guilds)} servers | {self.bot.settings.command_prefix}help"
        )
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

        # Send welcome message if possible
        system_channel = guild.system_channel
        if system_channel and system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="Thanks for adding Boss-Bot!",
                description=f"Use `{self.bot.settings.command_prefix}help` to get started.",
                color=discord.Color.green()
            )
            await system_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild."""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

        # Cleanup guild-specific data
        await self.bot.queue_manager.cleanup_guild_data(guild.id)
```

## Cog Development Patterns

### Base Cog Pattern

```python
# src/boss_bot/bot/cogs/base.py
from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boss_bot.bot.client import BossBot

class BaseCog(commands.Cog):
    """Base class for all Bot cogs with common functionality."""

    def __init__(self, bot: "BossBot"):
        self.bot = bot
        self.settings = bot.settings
        self.queue_manager = bot.queue_manager
        self.download_manager = bot.download_manager

    async def cog_load(self):
        """Called when cog is loaded."""
        print(f"Loaded cog: {self.__class__.__name__}")

    async def cog_unload(self):
        """Called when cog is unloaded."""
        print(f"Unloaded cog: {self.__class__.__name__}")

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors in this cog's commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: `{error.param.name}`")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")
            return

        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)

        await ctx.send("An unexpected error occurred. Please try again later.")
```

### Download Cog Implementation

```python
# src/boss_bot/bot/cogs/downloads.py
import discord
from discord.ext import commands
from boss_bot.bot.cogs.base import BaseCog
from boss_bot.core.downloads.exceptions import DownloadError, UnsupportedURLError, QuotaExceededError
from boss_bot.schemas.discord import MediaMetadata
from typing import Optional

class DownloadCog(BaseCog):
    """Commands for downloading media from supported platforms."""

    @commands.command(name="download", aliases=["dl"])
    async def download_command(self, ctx: commands.Context, url: str, quality: Optional[str] = None):
        """Download media from a supported URL.

        Args:
            url: URL to download from (Twitter, Reddit, Instagram, YouTube)
            quality: Video quality (720p, 1080p, etc.) for YouTube downloads

        Examples:
            $download https://twitter.com/user/status/123
            $download https://youtube.com/watch?v=abc 720p
        """
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            await ctx.send("❌ Please provide a valid URL starting with http:// or https://")
            return

        # Check if bot is operational
        if not self.bot.is_ready_and_operational:
            await ctx.send("⚠️ Bot is not fully operational. Please try again in a moment.")
            return

        # Send initial response
        processing_msg = await ctx.send(f"🔄 Processing download for: `{url}`")

        try:
            # Add to queue
            queue_item = await self.queue_manager.add_to_queue(
                url=url,
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None,
                channel_id=ctx.channel.id,
                quality=quality
            )

            # Update message with queue position
            if queue_item.position > 0:
                await processing_msg.edit(
                    content=f"📋 Added to queue (position {queue_item.position}): `{url}`"
                )
            else:
                await processing_msg.edit(content=f"⏳ Starting download: `{url}`")

            # Wait for completion
            result = await queue_item.wait_for_completion(timeout=300)  # 5 minutes

            # Send success response
            embed = self._create_success_embed(result, ctx.author)
            await processing_msg.edit(content="✅ Download completed!", embed=embed)

        except QuotaExceededError:
            await processing_msg.edit(
                content="❌ Storage quota exceeded. Please contact an administrator."
            )

        except UnsupportedURLError:
            await processing_msg.edit(
                content="❌ URL not supported. Supported platforms: Twitter, Reddit, Instagram, YouTube"
            )

        except asyncio.TimeoutError:
            await processing_msg.edit(
                content="⏱️ Download timed out. The file may be too large or the server is slow."
            )

        except DownloadError as e:
            await processing_msg.edit(content=f"❌ Download failed: {e}")

        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected download error: {e}", exc_info=True)

            await processing_msg.edit(
                content="❌ An unexpected error occurred. Please try again later."
            )

    def _create_success_embed(self, metadata: MediaMetadata, user: discord.User) -> discord.Embed:
        """Create embed for successful download."""
        embed = discord.Embed(
            title="Download Completed",
            color=discord.Color.green(),
            timestamp=metadata.download_timestamp
        )

        embed.add_field(name="Platform", value=metadata.platform.title(), inline=True)
        embed.add_field(name="Method", value=metadata.download_method.upper(), inline=True)

        if metadata.title:
            embed.add_field(name="Title", value=metadata.title[:100], inline=False)

        if metadata.author:
            embed.add_field(name="Author", value=metadata.author, inline=True)

        if metadata.duration:
            embed.add_field(
                name="Duration",
                value=f"{metadata.duration // 60}:{metadata.duration % 60:02d}",
                inline=True
            )

        if metadata.file_size_bytes:
            size_mb = metadata.file_size_bytes / 1024 / 1024
            embed.add_field(name="Size", value=f"{size_mb:.1f} MB", inline=True)

        embed.set_footer(text=f"Downloaded by {user.display_name}", icon_url=user.avatar.url)

        if metadata.thumbnail:
            embed.set_thumbnail(url=metadata.thumbnail)

        return embed

    @commands.command(name="formats")
    async def list_formats_command(self, ctx: commands.Context, url: str):
        """List available formats for a URL (YouTube only).

        Args:
            url: YouTube URL to check formats for
        """
        if 'youtube.com' not in url and 'youtu.be' not in url:
            await ctx.send("❌ Format listing is only supported for YouTube URLs.")
            return

        try:
            # Get format information without downloading
            formats = await self.download_manager.get_available_formats(url)

            embed = discord.Embed(
                title="Available Formats",
                description=f"Formats for: `{url}`",
                color=discord.Color.blue()
            )

            # Group formats by type
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']

            if video_formats:
                video_list = []
                for fmt in video_formats[:10]:  # Limit to 10 formats
                    resolution = fmt.get('height', 'unknown')
                    ext = fmt.get('ext', 'unknown')
                    video_list.append(f"{resolution}p ({ext})")

                embed.add_field(
                    name="Video Formats",
                    value="\n".join(video_list),
                    inline=True
                )

            if audio_formats:
                audio_list = []
                for fmt in audio_formats[:5]:  # Limit to 5 formats
                    ext = fmt.get('ext', 'unknown')
                    abr = fmt.get('abr', 'unknown')
                    audio_list.append(f"{ext} ({abr}kbps)")

                embed.add_field(
                    name="Audio Formats",
                    value="\n".join(audio_list),
                    inline=True
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to get format information: {e}")

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(DownloadCog(bot))
```

### Queue Management Cog

```python
# src/boss_bot/bot/cogs/queue.py
import discord
from discord.ext import commands
from boss_bot.bot.cogs.base import BaseCog

class QueueCog(BaseCog):
    """Commands for managing the download queue."""

    @commands.command(name="queue", aliases=["q"])
    async def show_queue(self, ctx: commands.Context):
        """Show current download queue status."""
        queue_status = await self.queue_manager.get_queue_status()

        embed = discord.Embed(
            title="Download Queue Status",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Queue Stats",
            value=f"Active: {queue_status.active_downloads}\n"
                  f"Pending: {queue_status.pending_count}\n"
                  f"Completed Today: {queue_status.completed_today}",
            inline=True
        )

        embed.add_field(
            name="System Stats",
            value=f"Uptime: {queue_status.uptime}\n"
                  f"Success Rate: {queue_status.success_rate:.1f}%",
            inline=True
        )

        # Show current queue items
        if queue_status.current_items:
            queue_list = []
            for i, item in enumerate(queue_status.current_items[:5]):  # Show first 5
                user = self.bot.get_user(item.user_id)
                username = user.display_name if user else "Unknown"
                queue_list.append(f"{i+1}. {item.platform} - {username}")

            embed.add_field(
                name="Current Queue",
                value="\n".join(queue_list) or "Queue is empty",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="clear_queue")
    @commands.has_permissions(manage_guild=True)
    async def clear_queue(self, ctx: commands.Context):
        """Clear the download queue (Admin only)."""
        cleared_count = await self.queue_manager.clear_queue()

        embed = discord.Embed(
            title="Queue Cleared",
            description=f"Removed {cleared_count} items from the queue.",
            color=discord.Color.orange()
        )

        await ctx.send(embed=embed)

    @commands.command(name="pause_queue")
    @commands.has_permissions(manage_guild=True)
    async def pause_queue(self, ctx: commands.Context):
        """Pause queue processing (Admin only)."""
        await self.queue_manager.pause()

        embed = discord.Embed(
            title="Queue Paused",
            description="Download queue processing has been paused.",
            color=discord.Color.orange()
        )

        await ctx.send(embed=embed)

    @commands.command(name="resume_queue")
    @commands.has_permissions(manage_guild=True)
    async def resume_queue(self, ctx: commands.Context):
        """Resume queue processing (Admin only)."""
        await self.queue_manager.resume()

        embed = discord.Embed(
            title="Queue Resumed",
            description="Download queue processing has been resumed.",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(QueueCog(bot))
```

## Error Handling Patterns

### Global Error Handler

```python
# src/boss_bot/bot/events/error_handler.py
import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class ErrorHandler(commands.Cog):
    """Global error handling for the bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors globally."""

        # Ignore these error types
        if isinstance(error, (commands.CommandNotFound, commands.DisabledCommand)):
            return

        # User errors (send helpful message)
        if isinstance(error, commands.UserInputError):
            await self._handle_user_input_error(ctx, error)
            return

        # Permission errors
        if isinstance(error, commands.CheckFailure):
            await self._handle_permission_error(ctx, error)
            return

        # Discord API errors
        if isinstance(error, discord.HTTPException):
            await self._handle_discord_error(ctx, error)
            return

        # Unexpected errors
        await self._handle_unexpected_error(ctx, error)

    async def _handle_user_input_error(self, ctx: commands.Context, error: commands.UserInputError):
        """Handle user input errors with helpful messages."""
        embed = discord.Embed(
            title="Invalid Command Usage",
            color=discord.Color.red()
        )

        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Missing required argument: `{error.param.name}`"
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`",
                inline=False
            )

        elif isinstance(error, commands.BadArgument):
            embed.description = f"Invalid argument: {error}"

        elif isinstance(error, commands.TooManyArguments):
            embed.description = "Too many arguments provided."

        else:
            embed.description = str(error)

        await ctx.send(embed=embed, delete_after=30)

    async def _handle_permission_error(self, ctx: commands.Context, error: commands.CheckFailure):
        """Handle permission-related errors."""
        embed = discord.Embed(
            title="Permission Denied",
            color=discord.Color.red()
        )

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed.description = f"You need the following permissions: {perms}"

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed.description = f"I need the following permissions: {perms}"

        elif isinstance(error, commands.NotOwner):
            embed.description = "This command is only available to the bot owner."

        else:
            embed.description = "You don't have permission to use this command."

        await ctx.send(embed=embed, delete_after=30)

    async def _handle_discord_error(self, ctx: commands.Context, error: discord.HTTPException):
        """Handle Discord API errors."""
        if error.status == 403:
            embed = discord.Embed(
                title="Permission Error",
                description="I don't have permission to perform this action.",
                color=discord.Color.red()
            )
        elif error.status == 404:
            embed = discord.Embed(
                title="Not Found",
                description="The requested resource was not found.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="Discord API Error",
                description="An error occurred while communicating with Discord.",
                color=discord.Color.red()
            )

        logger.warning(f"Discord API error in {ctx.command}: {error}")
        await ctx.send(embed=embed, delete_after=30)

    async def _handle_unexpected_error(self, ctx: commands.Context, error: Exception):
        """Handle unexpected errors with logging."""
        logger.error(
            f"Unexpected error in command {ctx.command} "
            f"(User: {ctx.author.id}, Guild: {ctx.guild.id if ctx.guild else None}): {error}",
            exc_info=error
        )

        embed = discord.Embed(
            title="Unexpected Error",
            description="An unexpected error occurred. The error has been logged.",
            color=discord.Color.red()
        )

        await ctx.send(embed=embed, delete_after=30)

async def setup(bot):
    """Setup function for loading the error handler."""
    await bot.add_cog(ErrorHandler(bot))
```

## Discord Testing Strategies

### Mocking Discord Objects

```python
# tests/conftest.py - Discord-specific fixtures
import pytest
from unittest.mock import Mock, AsyncMock
from pytest_mock import MockerFixture
import discord
from discord.ext import commands

@pytest.fixture(scope="function")
def fixture_discord_user_test(mocker: MockerFixture) -> Mock:
    """Create a mocked Discord user."""
    user = mocker.Mock(spec=discord.User)
    user.id = 12345
    user.name = "testuser"
    user.display_name = "Test User"
    user.avatar = mocker.Mock()
    user.avatar.url = "https://example.com/avatar.png"
    return user

@pytest.fixture(scope="function")
def fixture_discord_guild_test(mocker: MockerFixture) -> Mock:
    """Create a mocked Discord guild."""
    guild = mocker.Mock(spec=discord.Guild)
    guild.id = 98765
    guild.name = "Test Guild"
    guild.owner_id = 12345
    return guild

@pytest.fixture(scope="function")
def fixture_discord_channel_test(mocker: MockerFixture) -> Mock:
    """Create a mocked Discord channel."""
    channel = mocker.Mock(spec=discord.TextChannel)
    channel.id = 67890
    channel.name = "test-channel"
    channel.send = mocker.AsyncMock()
    return channel

@pytest.fixture(scope="function")
def fixture_discord_context_test(
    mocker: MockerFixture,
    fixture_discord_user_test: Mock,
    fixture_discord_guild_test: Mock,
    fixture_discord_channel_test: Mock
) -> Mock:
    """Create a comprehensive Discord context mock."""
    ctx = mocker.Mock(spec=commands.Context)

    # Essential async methods
    ctx.send = mocker.AsyncMock()
    ctx.reply = mocker.AsyncMock()

    # Context properties
    ctx.author = fixture_discord_user_test
    ctx.guild = fixture_discord_guild_test
    ctx.channel = fixture_discord_channel_test
    ctx.prefix = "$"

    # Command information
    ctx.command = mocker.Mock()
    ctx.command.name = "test_command"
    ctx.command.qualified_name = "test_command"
    ctx.command.signature = "<url>"

    return ctx
```

### Testing Cog Commands

```python
# tests/test_bot/test_cogs/test_downloads.py
import pytest
from unittest.mock import Mock, AsyncMock
from pytest_mock import MockerFixture

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.schemas.discord import MediaMetadata

class TestDownloadCog:
    """Test suite for DownloadCog commands."""

    @pytest.mark.asyncio
    async def test_download_command_success(
        self,
        mocker: MockerFixture,
        fixture_discord_context_test: Mock,
        fixture_mock_bot_test: Mock
    ):
        """Test successful download command execution."""
        # Setup
        cog = DownloadCog(fixture_mock_bot_test)

        # Mock queue manager
        mock_queue_item = mocker.Mock()
        mock_queue_item.position = 0
        mock_queue_item.wait_for_completion = mocker.AsyncMock(
            return_value=MediaMetadata(
                platform="twitter",
                url="https://twitter.com/test",
                title="Test Tweet",
                author="testuser"
            )
        )

        fixture_mock_bot_test.queue_manager.add_to_queue = mocker.AsyncMock(
            return_value=mock_queue_item
        )

        fixture_mock_bot_test.is_ready_and_operational = True

        # Execute command
        await cog.download_command.callback(
            cog,
            fixture_discord_context_test,
            "https://twitter.com/test"
        )

        # Verify queue interaction
        fixture_mock_bot_test.queue_manager.add_to_queue.assert_called_once()

        # Verify Discord responses
        assert fixture_discord_context_test.send.call_count >= 1

        # Check final response contains success message
        final_call = fixture_discord_context_test.send.call_args_list[-1]
        if 'content' in final_call.kwargs:
            assert "✅" in final_call.kwargs['content']

    @pytest.mark.asyncio
    async def test_download_command_invalid_url(
        self,
        mocker: MockerFixture,
        fixture_discord_context_test: Mock,
        fixture_mock_bot_test: Mock
    ):
        """Test download command with invalid URL."""
        cog = DownloadCog(fixture_mock_bot_test)
        fixture_mock_bot_test.is_ready_and_operational = True

        # Execute with invalid URL
        await cog.download_command.callback(
            cog,
            fixture_discord_context_test,
            "not-a-url"
        )

        # Verify error response
        fixture_discord_context_test.send.assert_called_once()
        sent_message = fixture_discord_context_test.send.call_args[1]['content']
        assert "❌" in sent_message
        assert "valid URL" in sent_message

    @pytest.mark.asyncio
    async def test_download_command_bot_not_ready(
        self,
        mocker: MockerFixture,
        fixture_discord_context_test: Mock,
        fixture_mock_bot_test: Mock
    ):
        """Test download command when bot is not operational."""
        cog = DownloadCog(fixture_mock_bot_test)
        fixture_mock_bot_test.is_ready_and_operational = False

        # Execute command
        await cog.download_command.callback(
            cog,
            fixture_discord_context_test,
            "https://twitter.com/test"
        )

        # Verify appropriate response
        fixture_discord_context_test.send.assert_called_once()
        sent_message = fixture_discord_context_test.send.call_args[1]['content']
        assert "⚠️" in sent_message
        assert "not fully operational" in sent_message
```

### Integration Testing with dpytest

```python
# tests/test_bot/test_integration.py
import pytest
import dpytest
from boss_bot.bot.client import BossBot

@pytest.mark.asyncio
async def test_bot_integration(fixture_settings_test):
    """Test bot integration with dpytest."""
    # Create bot instance
    bot = BossBot(fixture_settings_test)

    # Configure dpytest
    dpytest.configure(bot)

    # Load cogs for testing
    await bot.load_extension('boss_bot.bot.cogs.downloads')

    # Test command execution
    await dpytest.message("$help")
    assert dpytest.verify().message().contains().content("Available commands")

    # Test download command with mock
    await dpytest.message("$download https://twitter.com/test")

    # Verify response
    assert dpytest.verify().message().contains().content("Processing download")

    # Cleanup
    await dpytest.empty_queue()
```

## Custom Help Command

```python
# src/boss_bot/bot/bot_help.py
import discord
from discord.ext import commands
from typing import Optional, List, Mapping

class BossHelpCommand(commands.HelpCommand):
    """Custom help command with embeds and better formatting."""

    def __init__(self):
        super().__init__(
            command_attrs={
                'help': 'Show help information for commands',
                'aliases': ['h']
            }
        )

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        """Send help for the entire bot."""
        embed = discord.Embed(
            title="Boss-Bot Help",
            description="Download media from supported platforms",
            color=discord.Color.blue()
        )

        for cog, commands_list in mapping.items():
            if not commands_list:
                continue

            cog_name = getattr(cog, 'qualified_name', 'No Category')
            command_names = [f"`{cmd.name}`" for cmd in commands_list if not cmd.hidden]

            if command_names:
                embed.add_field(
                    name=cog_name,
                    value=" ".join(command_names),
                    inline=False
                )

        embed.add_field(
            name="Supported Platforms",
            value="Twitter/X, Reddit, Instagram, YouTube",
            inline=False
        )

        embed.set_footer(text=f"Use {self.context.prefix}help <command> for more info")

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        """Send help for a specific command."""
        embed = discord.Embed(
            title=f"Command: {command.qualified_name}",
            description=command.help or "No description available",
            color=discord.Color.blue()
        )

        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )

        embed.add_field(
            name="Usage",
            value=f"`{self.context.prefix}{command.qualified_name} {command.signature}`",
            inline=False
        )

        await self.get_destination().send(embed=embed)

    async def command_not_found(self, string: str) -> str:
        """Handle command not found."""
        return f"Command `{string}` not found."

    async def send_error_message(self, error: str):
        """Send error message."""
        embed = discord.Embed(
            title="Help Error",
            description=error,
            color=discord.Color.red()
        )
        await self.get_destination().send(embed=embed)
```

This Discord integration guide provides comprehensive patterns for building robust Discord bots with proper error handling, testing strategies, and modern Discord.py best practices.
