"""Discord cog for handling downloads."""

from pathlib import Path
from typing import Dict, Optional

import discord
from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags

# Legacy handlers kept for queue system fallback
from boss_bot.core.downloads.handlers import TwitterHandler
from boss_bot.core.downloads.handlers.reddit_handler import RedditHandler
from boss_bot.core.downloads.strategies import (
    BaseDownloadStrategy,
    InstagramDownloadStrategy,
    RedditDownloadStrategy,
    TwitterDownloadStrategy,
    YouTubeDownloadStrategy,
)


class DownloadCog(commands.Cog):
    """Cog for handling downloads."""

    def __init__(self, bot: BossBot):
        """Initialize the cog."""
        self.bot = bot
        # Initialize download directory for strategies
        self.download_dir = Path.cwd() / ".downloads"
        self.download_dir.mkdir(exist_ok=True, parents=True)

        # Initialize feature flags
        self.feature_flags = DownloadFeatureFlags(bot.settings)

        # Initialize strategies
        self.strategies: dict[str, BaseDownloadStrategy] = {}
        self._initialize_strategies()

        # Keep legacy handlers for fallback to queue system
        self.twitter_handler = TwitterHandler(download_dir=self.download_dir)
        self.reddit_handler = RedditHandler(download_dir=self.download_dir)

    def _initialize_strategies(self) -> None:
        """Initialize download strategies for each platform."""
        self.strategies["twitter"] = TwitterDownloadStrategy(
            feature_flags=self.feature_flags, download_dir=self.download_dir
        )
        self.strategies["reddit"] = RedditDownloadStrategy(
            feature_flags=self.feature_flags, download_dir=self.download_dir
        )
        self.strategies["youtube"] = YouTubeDownloadStrategy(
            feature_flags=self.feature_flags, download_dir=self.download_dir
        )
        self.strategies["instagram"] = InstagramDownloadStrategy(
            feature_flags=self.feature_flags, download_dir=self.download_dir
        )

    def _get_strategy_for_url(self, url: str) -> BaseDownloadStrategy | None:
        """Get the appropriate strategy for a URL.

        Args:
            url: The URL to check

        Returns:
            Strategy instance if supported, None otherwise
        """
        for strategy in self.strategies.values():
            if strategy.supports_url(url):
                return strategy
        return None

    @commands.command(name="download")
    async def download(self, ctx: commands.Context, url: str):
        """Download content from various platforms using strategy pattern."""
        # Try to find a strategy that supports this URL
        strategy = self._get_strategy_for_url(url)

        if strategy:
            # Determine platform emoji and name
            platform_info = self._get_platform_info(url)
            emoji = platform_info["emoji"]
            name = platform_info["name"]

            await ctx.send(f"{emoji} Downloading {name} content: {url}")

            # Show feature flag status if API is enabled
            platform_key = strategy.__class__.__name__.lower().replace("downloadstrategy", "")
            if self.feature_flags.is_api_enabled_for_platform(platform_key):
                await ctx.send(f"🚀 Using experimental API-direct approach for {name}")

            try:
                metadata = await strategy.download(url)

                # Check if download was successful (no error in metadata)
                if metadata.error:
                    await ctx.send(f"❌ {name} download failed: {metadata.error}")
                else:
                    await ctx.send(f"✅ {name} download completed! Files saved to `.downloads/`")

                    # Show basic metadata if available
                    if metadata.title:
                        title_preview = metadata.title[:100] + "..." if len(metadata.title) > 100 else metadata.title
                        await ctx.send(f"📝 **Title:** {title_preview}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        await ctx.send(f"{method_emoji} Downloaded using {metadata.download_method.upper()} method")

            except Exception as e:
                await ctx.send(f"❌ Download error: {e!s}")
            return

        # Fallback to existing queue-based system for unsupported URLs
        if not self.bot.download_manager.validate_url(url):
            await ctx.send("Invalid URL provided.")
            return

        try:
            await self.bot.queue_manager.add_to_queue(url, ctx.author.id, ctx.channel.id)
            await ctx.send(f"Added {url} to download queue.")
        except Exception as e:
            await ctx.send(str(e))

    def _get_platform_info(self, url: str) -> dict[str, str]:
        """Get platform-specific emoji and name for a URL.

        Args:
            url: The URL to analyze

        Returns:
            Dictionary with emoji and name
        """
        url_lower = url.lower()

        if "twitter.com" in url_lower or "x.com" in url_lower:
            return {"emoji": "🐦", "name": "Twitter/X"}
        elif "reddit.com" in url_lower:
            return {"emoji": "🤖", "name": "Reddit"}
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return {"emoji": "📺", "name": "YouTube"}
        elif "instagram.com" in url_lower:
            return {"emoji": "📷", "name": "Instagram"}
        else:
            return {"emoji": "🔗", "name": "Unknown"}

    @commands.command(name="metadata")
    async def metadata(self, ctx: commands.Context, url: str):
        """Get metadata information about a URL without downloading."""
        # Try to find a strategy that supports this URL
        strategy = self._get_strategy_for_url(url)

        if strategy:
            # Determine platform info
            platform_info = self._get_platform_info(url)
            emoji = platform_info["emoji"]
            name = platform_info["name"]

            await ctx.send(f"🔍 Getting {name} metadata: {url}")

            # Show feature flag status if API is enabled
            platform_key = strategy.__class__.__name__.lower().replace("downloadstrategy", "")
            if self.feature_flags.is_api_enabled_for_platform(platform_key):
                await ctx.send("🚀 Using experimental API-direct approach for metadata")

            try:
                metadata = await strategy.get_metadata(url)

                # Build info message
                info_lines = [f"{emoji} **{name} Content Info**"]

                if metadata.title:
                    info_lines.append(
                        f"📝 **Title:** {metadata.title[:200]}{'...' if len(metadata.title) > 200 else ''}"
                    )
                if metadata.uploader:
                    info_lines.append(f"👤 **Author:** {metadata.uploader}")
                if metadata.upload_date:
                    info_lines.append(f"📅 **Date:** {metadata.upload_date}")

                # Platform-specific metadata
                if name == "Twitter/X":
                    if metadata.like_count:
                        info_lines.append(f"❤️ **Likes:** {metadata.like_count}")
                    if metadata.view_count:
                        info_lines.append(f"🔄 **Retweets:** {metadata.view_count}")
                elif name == "Reddit":
                    if metadata.raw_metadata and metadata.raw_metadata.get("subreddit"):
                        info_lines.append(f"📂 **Subreddit:** r/{metadata.raw_metadata['subreddit']}")
                    if metadata.like_count:
                        info_lines.append(f"⬆️ **Score:** {metadata.like_count}")
                    if metadata.raw_metadata and metadata.raw_metadata.get("num_comments"):
                        info_lines.append(f"💬 **Comments:** {metadata.raw_metadata['num_comments']}")
                elif name == "YouTube":
                    if metadata.duration:
                        info_lines.append(f"⏱️ **Duration:** {metadata.duration}")
                    if metadata.view_count:
                        info_lines.append(f"👁️ **Views:** {metadata.view_count}")
                    if metadata.like_count:
                        info_lines.append(f"❤️ **Likes:** {metadata.like_count}")
                elif name == "Instagram":
                    if metadata.like_count:
                        info_lines.append(f"❤️ **Likes:** {metadata.like_count}")
                    if metadata.view_count:
                        info_lines.append(f"👁️ **Views:** {metadata.view_count}")

                await ctx.send("\n".join(info_lines))

            except Exception as e:
                await ctx.send(f"❌ Failed to get metadata: {e!s}")
        else:
            await ctx.send("ℹ️ Metadata extraction supported for Twitter/X, Reddit, YouTube, and Instagram URLs")

    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """Show the current download status."""
        active_downloads = self.bot.download_manager.get_active_downloads()
        queue_size = self.bot.queue_manager.queue_size
        await ctx.send(f"Active downloads: {active_downloads}\nQueue size: {queue_size}")

    @commands.command(name="strategies")
    async def show_strategies(self, ctx: commands.Context):
        """Show current download strategy configuration."""
        info = self.feature_flags.get_strategy_info()

        lines = ["🔧 **Download Strategy Configuration**", ""]

        platforms = [
            ("🐦 Twitter/X", "twitter_api"),
            ("🤖 Reddit", "reddit_api"),
            ("📺 YouTube", "youtube_api"),
            ("📷 Instagram", "instagram_api"),
        ]

        for emoji_name, key in platforms:
            status = "🚀 **API-Direct**" if info[key] else "🖥️ **CLI Mode**"
            lines.append(f"{emoji_name}: {status}")

        lines.extend(
            [
                "",
                f"🔄 **API Fallback**: {'✅ Enabled' if info['api_fallback'] else '❌ Disabled'}",
                "",
                "💡 *Tip: Enable experimental features with environment variables like `TWITTER_USE_API_CLIENT=true`*",
            ]
        )

        await ctx.send("\n".join(lines))

    @commands.command(name="validate-config")
    async def validate_config(self, ctx: commands.Context, platform: str = "instagram"):
        """Validate gallery-dl configuration for specified platform.

        Args:
            ctx: Discord command context
            platform: Platform to validate (default: instagram)

        Examples:
            $validate-config
            $validate-config instagram
        """
        platform = platform.lower()

        if platform == "instagram":
            if "instagram" not in self.strategies:
                await ctx.send("❌ Instagram strategy not available")
                return

            strategy = self.strategies["instagram"]

            # Perform validation
            try:
                is_valid, issues = strategy.validate_config()

                if is_valid:
                    await ctx.send("✅ **Instagram Configuration Valid**\n\nAll configuration settings are correct!")
                else:
                    lines = ["❌ **Instagram Configuration Issues**", ""]
                    lines.extend([f"• {issue}" for issue in issues[:10]])  # Limit to first 10 issues
                    if len(issues) > 10:
                        lines.append(f"... and {len(issues) - 10} more issues")
                    await ctx.send("\n".join(lines))
            except Exception as e:
                await ctx.send(f"❌ Configuration validation failed: {e!s}")
        else:
            await ctx.send(
                f"❌ Configuration validation not supported for platform: {platform}\n\nSupported platforms: instagram"
            )

    @commands.command(name="config-summary")
    async def config_summary(self, ctx: commands.Context, platform: str = "instagram"):
        """Show configuration summary for specified platform.

        Args:
            ctx: Discord command context
            platform: Platform to show summary for (default: instagram)

        Examples:
            $config-summary
            $config-summary instagram
        """
        platform = platform.lower()

        if platform == "instagram":
            if "instagram" not in self.strategies:
                await ctx.send("❌ Instagram strategy not available")
                return

            strategy = self.strategies["instagram"]

            # Get config summary
            try:
                from boss_bot.core.downloads.clients.config.gallery_dl_validator import InstagramConfigValidator

                result = InstagramConfigValidator.validate_config()

                lines = ["📷 **Instagram Configuration Summary**", ""]

                # Show key configuration values
                config_items = [
                    ("Base Directory", result.config_summary.get("extractor -> base-directory", "Not set")),
                    ("Archive", result.config_summary.get("extractor -> archive", "Not set")),
                    ("Videos Enabled", result.config_summary.get("extractor -> instagram -> videos", "Not set")),
                    ("Include", result.config_summary.get("extractor -> instagram -> include", "Not set")),
                    ("Filename Pattern", result.config_summary.get("extractor -> instagram -> filename", "Not set")),
                    ("Sleep Request", result.config_summary.get("extractor -> instagram -> sleep-request", "Not set")),
                    ("Downloader Retries", result.config_summary.get("downloader -> retries", "Not set")),
                    ("Downloader Timeout", result.config_summary.get("downloader -> timeout", "Not set")),
                ]

                for name, value in config_items:
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    lines.append(f"**{name}**: `{value}`")

                lines.append("")
                lines.append(f"**Status**: {'✅ Valid' if result.is_valid else '❌ Has Issues'}")

                await ctx.send("\n".join(lines))
            except Exception as e:
                await ctx.send(f"❌ Failed to get config summary: {e!s}")
        else:
            await ctx.send(
                f"❌ Configuration summary not supported for platform: {platform}\n\nSupported platforms: instagram"
            )

    # Event Handlers
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready."""
        print(f"{type(self).__name__} Cog ready.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        print(f"Bot joined new guild: {guild.name} (ID: {guild.id})")

        # Send a welcome message to the system channel if available
        if guild.system_channel is not None:
            try:
                embed = discord.Embed(
                    title="👋 Thanks for adding BossBot!",
                    description=f"Use `{self.bot.command_prefix}help` to see available commands.\n"
                    f"Use `{self.bot.command_prefix}download <url>` to download media from various platforms.",
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name="Supported Platforms",
                    value="• Twitter/X\n• Reddit\n• Instagram\n• YouTube\n• And more!",
                    inline=False,
                )
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                print(f"Cannot send welcome message to {guild.name} - missing permissions")

    # Command Error Handlers
    @download.error
    async def download_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the download command."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="Sorry, you need `MANAGE SERVER` permissions to use the download command!",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"Please provide a URL to download. Usage: `{self.bot.command_prefix}download <url>`",
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
            print(f"Unexpected error in download command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while processing your download request.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @metadata.error
    async def metadata_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the metadata command."""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"Please provide a URL to get metadata for. Usage: `{self.bot.command_prefix}metadata <url>`",
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
            print(f"Unexpected error in metadata command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting URL metadata.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @status.error
    async def status_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the status command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in status command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting status.", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @show_strategies.error
    async def strategies_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the strategies command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in strategies command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting strategy information.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)


async def setup(bot: BossBot):
    """Load the DownloadCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(DownloadCog(bot))
