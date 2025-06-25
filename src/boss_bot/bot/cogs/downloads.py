"""Discord cog for handling downloads with upload functionality."""

import shutil
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
from boss_bot.core.uploads.manager import UploadManager

# AI agent imports for enhanced functionality
try:
    from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
    from boss_bot.ai.agents.context import AgentContext, AgentRequest
    from boss_bot.ai.agents.strategy_selector import StrategySelector

    AI_AGENTS_AVAILABLE = True
except ImportError:
    AI_AGENTS_AVAILABLE = False


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

        # Initialize upload manager
        self.upload_manager = UploadManager(bot.settings)

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
        # Traditional method - check each strategy
        for strategy in self.strategies.values():
            if strategy.supports_url(url):
                return strategy
        return None

    async def _get_ai_enhanced_strategy_for_url(
        self, url: str, ctx: commands.Context
    ) -> tuple[BaseDownloadStrategy | None, dict | None]:
        """Get strategy using AI agent if available, otherwise fall back to traditional method.

        Args:
            url: The URL to check
            ctx: Discord context for user information

        Returns:
            Tuple of (strategy, ai_metadata) where ai_metadata contains AI insights if used
        """
        ai_metadata = None

        # Check if AI strategy selection is available and enabled
        if (
            AI_AGENTS_AVAILABLE
            and hasattr(self.bot, "strategy_selector")
            and self.bot.strategy_selector
            and self.feature_flags.ai_strategy_selection_enabled
        ):
            try:
                # Create agent context
                agent_context = AgentContext(
                    request_id=f"{ctx.author.id}_{ctx.message.id}",
                    user_id=str(ctx.author.id),
                    guild_id=str(ctx.guild.id) if ctx.guild else None,
                )

                # Create agent request
                request = AgentRequest(
                    context=agent_context, action="select_strategy", data={"url": url, "user_preferences": {}}
                )

                # Process with AI agent
                response = await self.bot.strategy_selector.process_request(request)

                if response.success and response.result:
                    platform = response.result.get("platform")
                    strategy = self.strategies.get(platform)

                    if strategy and strategy.supports_url(url):
                        ai_metadata = {
                            "ai_enhanced": True,
                            "confidence": response.confidence,
                            "reasoning": response.reasoning,
                            "platform": platform,
                            "recommended_options": response.result.get("recommended_options", {}),
                        }
                        return strategy, ai_metadata

            except Exception as e:
                # Log but don't fail - fall back to traditional method
                print(f"AI strategy selection failed: {e}, falling back to traditional method")

        # Fall back to traditional method
        strategy = self._get_strategy_for_url(url)
        return strategy, ai_metadata

    @commands.command(name="download")
    async def download(self, ctx: commands.Context, url: str, upload: bool = True):
        """Download content and optionally upload to Discord.

        Args:
            url: URL to download
            upload: Whether to upload files to Discord (default: True)
        """
        # Try to find a strategy that supports this URL (with AI enhancement if available)
        strategy, ai_metadata = await self._get_ai_enhanced_strategy_for_url(url, ctx)

        if strategy:
            # Determine platform emoji and name
            platform_info = self._get_platform_info(url)
            emoji = platform_info["emoji"]
            name = platform_info["name"]

            await ctx.send(f"{emoji} Downloading {name} content: {url}")

            # Show AI enhancement status if used
            if ai_metadata and ai_metadata.get("ai_enhanced"):
                confidence = ai_metadata.get("confidence", 0)
                await ctx.send(f"🤖 AI selected {name} strategy (confidence: {confidence:.2f})")

            # Show feature flag status if API is enabled
            platform_key = strategy.__class__.__name__.lower().replace("downloadstrategy", "")
            if self.feature_flags.is_api_enabled_for_platform(platform_key):
                await ctx.send(f"🚀 Using experimental API-direct approach for {name}")

            try:
                # Create unique download directory for this request
                request_id = f"{ctx.author.id}_{ctx.message.id}"
                download_subdir = self.download_dir / request_id
                download_subdir.mkdir(exist_ok=True, parents=True)

                # Temporarily change strategy download directory
                original_dir = strategy.download_dir
                strategy.download_dir = download_subdir

                try:
                    metadata = await strategy.download(url)

                    # Check if download was successful
                    if metadata.error:
                        await ctx.send(f"❌ {name} download failed: {metadata.error}")
                        return

                    # Check if this was a duplicate
                    if metadata.raw_metadata and metadata.raw_metadata.get("duplicate"):
                        original_download = metadata.raw_metadata.get("original_download", {})
                        download_date = original_download.get("download_date", "unknown date")
                        await ctx.send(f"🔄 {name} content already downloaded on {download_date[:10]}")
                        await ctx.send("💡 Use `force_redownload=True` parameter to download again")
                        return

                    await ctx.send(f"✅ {name} download completed!")

                    # Show basic metadata if available
                    if metadata.title:
                        title_preview = metadata.title[:100] + "..." if len(metadata.title) > 100 else metadata.title
                        await ctx.send(f"📝 **Title:** {title_preview}")

                    if metadata.download_method:
                        method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                        await ctx.send(f"{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                    # For YouTube, show organized directory info
                    if name == "YouTube" and hasattr(strategy, "_extract_channel_info_from_metadata"):
                        if metadata.raw_metadata:
                            channel_name, channel_id = strategy._extract_channel_info_from_metadata(
                                metadata.raw_metadata
                            )
                            await ctx.send(f"📁 **Channel:** {channel_name}")

                    # Process and upload files if requested
                    if upload:
                        await ctx.send("📤 Processing files for upload...")

                        # For YouTube strategy, check for organized structure
                        upload_dir = download_subdir
                        if name == "YouTube":
                            # Look for yt-dlp organized structure
                            ytdlp_dir = download_subdir / "yt-dlp" / "youtube"
                            if ytdlp_dir.exists():
                                upload_dir = ytdlp_dir
                                await ctx.send("📂 Using organized YouTube directory structure")

                        upload_result = await self.upload_manager.process_downloaded_files(upload_dir, ctx, name)

                        if upload_result.success:
                            await ctx.send(f"🎉 {upload_result.message}")
                        else:
                            await ctx.send(f"⚠️ Upload issues: {upload_result.message}")
                            if upload_result.error:
                                await ctx.send(f"Error details: {upload_result.error}")
                    else:
                        # Show appropriate directory path
                        display_dir = download_subdir
                        if name == "YouTube":
                            ytdlp_dir = download_subdir / "yt-dlp" / "youtube"
                            if ytdlp_dir.exists():
                                display_dir = ytdlp_dir
                        await ctx.send(f"📁 Files saved to: `{display_dir.relative_to(Path.cwd())}`")

                finally:
                    # Restore original download directory
                    strategy.download_dir = original_dir

                    # Cleanup: Remove download directory after upload (optional)
                    if upload and getattr(self.bot.settings, "upload_cleanup_after_success", True):
                        try:
                            shutil.rmtree(download_subdir)
                        except Exception as cleanup_error:
                            print(f"Cleanup warning: {cleanup_error}")

            except Exception as e:
                await ctx.send(f"❌ Download error: {e!s}")
            return

        # Fallback to existing queue-based system for unsupported URLs
        if not await self.bot.download_manager.validate_url(url):
            await ctx.send("Invalid URL provided.")
            return

        try:
            await self.bot.queue_manager.add_to_queue(url, ctx.author.id, ctx.channel.id)
            await ctx.send(f"Added {url} to download queue.")
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name="download-only")
    async def download_only(self, ctx: commands.Context, url: str):
        """Download content without uploading to Discord."""
        await self.download(ctx, url, upload=False)

    @commands.command(name="yt-download")
    async def youtube_download(self, ctx: commands.Context, url: str, quality: str = "720p", audio_only: bool = False):
        """YouTube-specific download with quality and format options.

        Args:
            url: YouTube URL (video, shorts, playlist)
            quality: Video quality (4K, 1080p, 720p, 480p, 360p, best, worst)
            audio_only: Download audio only (default: False)

        Examples:
            $yt-download https://youtube.com/watch?v=VIDEO_ID
            $yt-download https://youtube.com/watch?v=VIDEO_ID 1080p
            $yt-download https://youtube.com/watch?v=VIDEO_ID 720p True
        """
        # Check if URL is YouTube
        if not ("youtube.com" in url.lower() or "youtu.be" in url.lower()):
            await ctx.send("❌ This command is for YouTube URLs only. Use `$download` for other platforms.")
            return

        # Get YouTube strategy
        strategy = self.strategies.get("youtube")
        if not strategy:
            await ctx.send("❌ YouTube strategy not available")
            return

        platform_info = self._get_platform_info(url)
        emoji = platform_info["emoji"]
        name = platform_info["name"]

        # Validate quality parameter
        valid_qualities = ["4K", "2160p", "1440p", "2K", "1080p", "FHD", "720p", "HD", "480p", "360p", "best", "worst"]
        if quality not in valid_qualities:
            await ctx.send(f"❌ Invalid quality: {quality}. Valid options: {', '.join(valid_qualities)}")
            return

        await ctx.send(
            f"{emoji} Downloading {name} content with quality: {quality}{' (audio-only)' if audio_only else ''}"
        )
        await ctx.send(f"🔗 URL: {url}")

        # Show feature flag status
        if self.feature_flags.is_api_enabled_for_platform("youtube"):
            await ctx.send("🚀 Using experimental API-direct approach")

        try:
            # Create unique download directory
            request_id = f"{ctx.author.id}_{ctx.message.id}"
            download_subdir = self.download_dir / request_id
            download_subdir.mkdir(exist_ok=True, parents=True)

            # Update strategy download directory
            original_dir = strategy.download_dir
            strategy.download_dir = download_subdir

            try:
                # Download with YouTube-specific options
                metadata = await strategy.download(url, quality=quality, audio_only=audio_only)

                if metadata.error:
                    await ctx.send(f"❌ {name} download failed: {metadata.error}")
                    return

                # Check if this was a duplicate
                if metadata.raw_metadata and metadata.raw_metadata.get("duplicate"):
                    original_download = metadata.raw_metadata.get("original_download", {})
                    download_date = original_download.get("download_date", "unknown date")
                    await ctx.send(f"🔄 {name} content already downloaded on {download_date[:10]}")
                    await ctx.send("💡 Use `force_redownload=True` parameter to download again")
                    return

                await ctx.send(f"✅ {name} download completed!")

                # Show detailed metadata
                if metadata.title:
                    title_preview = metadata.title[:100] + "..." if len(metadata.title) > 100 else metadata.title
                    await ctx.send(f"📝 **Title:** {title_preview}")

                if metadata.uploader:
                    await ctx.send(f"👤 **Channel:** {metadata.uploader}")

                if metadata.duration:
                    await ctx.send(f"⏱️ **Duration:** {metadata.duration}")

                if metadata.view_count:
                    await ctx.send(f"👁️ **Views:** {metadata.view_count:,}")

                if metadata.like_count:
                    await ctx.send(f"❤️ **Likes:** {metadata.like_count:,}")

                if metadata.download_method:
                    method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                    await ctx.send(f"{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                # Show organized directory info
                if hasattr(strategy, "_extract_channel_info_from_metadata") and metadata.raw_metadata:
                    channel_name, channel_id = strategy._extract_channel_info_from_metadata(metadata.raw_metadata)
                    await ctx.send(f"📁 **Organized in:** yt-dlp/youtube/{channel_name}/")

                # Process and upload files
                await ctx.send("📤 Processing files for upload...")

                # Check for organized structure
                upload_dir = download_subdir
                ytdlp_dir = download_subdir / "yt-dlp" / "youtube"
                if ytdlp_dir.exists():
                    upload_dir = ytdlp_dir
                    await ctx.send("📂 Using organized YouTube directory structure")

                upload_result = await self.upload_manager.process_downloaded_files(upload_dir, ctx, name)

                if upload_result.success:
                    await ctx.send(f"🎉 {upload_result.message}")
                else:
                    await ctx.send(f"⚠️ Upload issues: {upload_result.message}")
                    if upload_result.error:
                        await ctx.send(f"Error details: {upload_result.error}")

            finally:
                # Restore original download directory
                strategy.download_dir = original_dir

                # Cleanup
                if getattr(self.bot.settings, "upload_cleanup_after_success", True):
                    try:
                        shutil.rmtree(download_subdir)
                    except Exception as cleanup_error:
                        print(f"Cleanup warning: {cleanup_error}")

        except Exception as e:
            await ctx.send(f"❌ YouTube download error: {e!s}")

    @commands.command(name="yt-playlist")
    async def youtube_playlist(self, ctx: commands.Context, url: str, quality: str = "720p", max_videos: int = 10):
        """Download YouTube playlist with video limit.

        Args:
            url: YouTube playlist URL
            quality: Video quality for all videos (default: 720p)
            max_videos: Maximum number of videos to download (default: 10, max: 25)

        Examples:
            $yt-playlist https://youtube.com/playlist?list=PLAYLIST_ID
            $yt-playlist https://youtube.com/playlist?list=PLAYLIST_ID 480p 5
        """
        # Check if URL is YouTube playlist
        if not ("youtube.com" in url.lower() and "playlist" in url.lower()):
            await ctx.send("❌ This command is for YouTube playlist URLs only.")
            return

        # Validate max_videos parameter
        if max_videos < 1 or max_videos > 25:
            await ctx.send("❌ max_videos must be between 1 and 25")
            return

        # Get YouTube strategy
        strategy = self.strategies.get("youtube")
        if not strategy:
            await ctx.send("❌ YouTube strategy not available")
            return

        # Validate quality parameter
        valid_qualities = ["4K", "2160p", "1440p", "2K", "1080p", "FHD", "720p", "HD", "480p", "360p", "best", "worst"]
        if quality not in valid_qualities:
            await ctx.send(f"❌ Invalid quality: {quality}. Valid options: {', '.join(valid_qualities)}")
            return

        await ctx.send(f"📺 Starting YouTube playlist download (max {max_videos} videos, quality: {quality})")
        await ctx.send(f"🔗 Playlist: {url}")
        await ctx.send("⚠️ **Note:** Playlist downloads may take several minutes")

        # Show feature flag status
        if self.feature_flags.is_api_enabled_for_platform("youtube"):
            await ctx.send("🚀 Using experimental API-direct approach")

        try:
            # Create unique download directory
            request_id = f"{ctx.author.id}_{ctx.message.id}"
            download_subdir = self.download_dir / request_id
            download_subdir.mkdir(exist_ok=True, parents=True)

            # Update strategy download directory
            original_dir = strategy.download_dir
            strategy.download_dir = download_subdir

            try:
                # Download playlist with options
                metadata = await strategy.download(
                    url, quality=quality, max_playlist_items=max_videos, extract_flat=False
                )

                if metadata.error:
                    await ctx.send(f"❌ Playlist download failed: {metadata.error}")
                    return

                await ctx.send("✅ Playlist download completed!")

                # Show playlist metadata if available
                if metadata.title:
                    title_preview = metadata.title[:100] + "..." if len(metadata.title) > 100 else metadata.title
                    await ctx.send(f"📝 **Playlist:** {title_preview}")

                if metadata.uploader:
                    await ctx.send(f"👤 **Channel:** {metadata.uploader}")

                if metadata.download_method:
                    method_emoji = "🚀" if metadata.download_method == "api" else "🖥️"
                    await ctx.send(f"{method_emoji} Downloaded using {metadata.download_method.upper()} method")

                # Process and upload files
                await ctx.send("📤 Processing playlist files for upload...")

                # Check for organized structure
                upload_dir = download_subdir
                ytdlp_dir = download_subdir / "yt-dlp" / "youtube"
                if ytdlp_dir.exists():
                    upload_dir = ytdlp_dir
                    await ctx.send("📂 Using organized YouTube directory structure")

                upload_result = await self.upload_manager.process_downloaded_files(upload_dir, ctx, "YouTube Playlist")

                if upload_result.success:
                    await ctx.send(f"🎉 {upload_result.message}")
                else:
                    await ctx.send(f"⚠️ Upload issues: {upload_result.message}")
                    if upload_result.error:
                        await ctx.send(f"Error details: {upload_result.error}")

            finally:
                # Restore original download directory
                strategy.download_dir = original_dir

                # Cleanup
                if getattr(self.bot.settings, "upload_cleanup_after_success", True):
                    try:
                        shutil.rmtree(download_subdir)
                    except Exception as cleanup_error:
                        print(f"Cleanup warning: {cleanup_error}")

        except Exception as e:
            await ctx.send(f"❌ Playlist download error: {e!s}")

    @commands.command(name="yt-stats")
    async def youtube_stats(self, ctx: commands.Context):
        """Show YouTube download performance statistics.

        Examples:
            $yt-stats
        """
        # Get YouTube strategy
        strategy = self.strategies.get("youtube")
        if not strategy:
            await ctx.send("❌ YouTube strategy not available")
            return

        try:
            stats = strategy.get_performance_stats()

            if "error" in stats:
                await ctx.send(f"❌ Failed to get performance stats: {stats['error']}")
                return

            if stats["total_downloads"] == 0:
                await ctx.send("📊 **YouTube Performance Stats**\n\nNo downloads recorded yet.")
                return

            lines = [
                "📊 **YouTube Performance Statistics**",
                "",
                f"📈 **Total Downloads:** {stats['total_downloads']}",
                f"⏱️ **Average Duration:** {stats['avg_duration']:.2f}s",
                "",
            ]

            # Method breakdown
            if stats["method_breakdown"]:
                lines.append("🔧 **Download Methods:**")
                for method, count in stats["method_breakdown"].items():
                    percentage = (count / stats["total_downloads"]) * 100
                    emoji = "🚀" if method == "api" else "🖥️" if method == "cli" else "🔄"
                    lines.append(f"{emoji} {method.upper()}: {count} ({percentage:.1f}%)")
                lines.append("")

            # Performance records
            if stats["fastest_download"]:
                fastest = stats["fastest_download"]
                lines.append(f"🏆 **Fastest:** {fastest['duration']:.2f}s ({fastest['method']})")

            if stats["slowest_download"]:
                slowest = stats["slowest_download"]
                lines.append(f"🐌 **Slowest:** {slowest['duration']:.2f}s ({slowest['method']})")

            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error getting YouTube stats: {e!s}")

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

    async def _get_ai_enhanced_metadata(self, metadata, url: str, platform: str, ctx: commands.Context) -> dict | None:
        """Enhance metadata using AI Content Analyzer if available.

        Args:
            metadata: Basic metadata from strategy
            url: The URL being analyzed
            platform: Platform name
            ctx: Discord context

        Returns:
            Enhanced metadata dict or None if AI not available
        """
        if not (
            AI_AGENTS_AVAILABLE
            and hasattr(self.bot, "content_analyzer")
            and self.bot.content_analyzer
            and self.feature_flags.ai_content_analysis_enabled
        ):
            return None

        try:
            # Create agent context
            agent_context = AgentContext(
                request_id=f"{ctx.author.id}_{ctx.message.id}_metadata",
                user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id) if ctx.guild else None,
            )

            # Request metadata enrichment
            request = AgentRequest(
                context=agent_context,
                action="enrich_metadata",
                data={
                    "url": url,
                    "platform": platform,
                    "basic_metadata": {
                        "title": metadata.title,
                        "uploader": metadata.uploader,
                        "upload_date": metadata.upload_date,
                        "duration": metadata.duration,
                        "view_count": metadata.view_count,
                        "like_count": metadata.like_count,
                    },
                },
            )

            response = await self.bot.content_analyzer.process_request(request)

            if response.success and response.result:
                return response.result

        except Exception as e:
            print(f"AI metadata enrichment failed: {e}")

        return None

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

                # Try to enhance metadata with AI if available
                enhanced_metadata = await self._get_ai_enhanced_metadata(metadata, url, name.lower(), ctx)

                # Build info message
                ai_enhanced = enhanced_metadata is not None
                header = f"{emoji} **{name} Content Info**"
                if ai_enhanced:
                    header += " (AI Enhanced)"
                info_lines = [header]

                # If AI provided insights, show them
                if enhanced_metadata:
                    ai_insights = enhanced_metadata.get("ai_insights", [])
                    if ai_insights and len(ai_insights) > 0:
                        info_lines.append(f"🤖 **AI Insights:** {ai_insights[0]}")

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

        # Platform API status
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
                "🤖 **AI Enhancement Status**",
                f"- Strategy Selection: {'✅ Enabled' if info['ai_strategy_selection'] else '❌ Disabled'}",
                f"- Content Analysis: {'✅ Enabled' if info['ai_content_analysis'] else '❌ Disabled'}",
                f"- Workflow Orchestration: {'✅ Enabled' if info['ai_workflow_orchestration'] else '❌ Disabled'}",
                "",
                "💡 *Tip: Enable AI features with `AI_STRATEGY_SELECTION_ENABLED=true`*",
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

    @youtube_download.error
    async def youtube_download_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the yt-download command."""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"Please provide a YouTube URL. Usage: `{self.bot.command_prefix}yt-download <url> [quality] [audio_only]`",
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
            print(f"Unexpected error in yt-download command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while processing YouTube download.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @youtube_playlist.error
    async def youtube_playlist_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the yt-playlist command."""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"Please provide a YouTube playlist URL. Usage: `{self.bot.command_prefix}yt-playlist <url> [quality] [max_videos]`",
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
            print(f"Unexpected error in yt-playlist command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while processing YouTube playlist download.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @youtube_stats.error
    async def youtube_stats_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the yt-stats command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in yt-stats command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting YouTube statistics.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)


async def setup(bot: BossBot):
    """Load the DownloadCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(DownloadCog(bot))
