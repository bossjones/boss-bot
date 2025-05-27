"""Discord cog for handling downloads."""

from pathlib import Path
from typing import Dict, Optional

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

    @commands.command(name="info")
    async def info(self, ctx: commands.Context, url: str):
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


async def setup(bot: BossBot):
    """Load the DownloadCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(DownloadCog(bot))
