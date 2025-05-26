"""Discord cog for handling downloads."""

from pathlib import Path

from discord.ext import commands

from boss_bot.bot.client import BossBot
from boss_bot.core.downloads.handlers import TwitterHandler
from boss_bot.core.downloads.handlers.reddit_handler import RedditHandler


class DownloadCog(commands.Cog):
    """Cog for handling downloads."""

    def __init__(self, bot: BossBot):
        """Initialize the cog."""
        self.bot = bot
        # Initialize download directory for handlers
        self.download_dir = Path.cwd() / ".downloads"
        self.download_dir.mkdir(exist_ok=True, parents=True)
        self.twitter_handler = TwitterHandler(download_dir=self.download_dir)
        self.reddit_handler = RedditHandler(download_dir=self.download_dir)

    @commands.command(name="download")
    async def download(self, ctx: commands.Context, url: str):
        """Download content from various platforms."""
        # Check if it's a Twitter/X URL and handle directly
        if self.twitter_handler.supports_url(url):
            await ctx.send(f"🐦 Downloading Twitter content: {url}")

            try:
                result = await self.twitter_handler.adownload(url)

                if result.success:
                    file_count = len(result.files) if result.files else 0
                    await ctx.send(f"✅ Twitter download completed! Downloaded {file_count} files to `.downloads/`")

                    # Show some files if available
                    if result.files and file_count <= 3:
                        file_list = "\n".join([f"📄 {f.name}" for f in result.files[:3]])
                        await ctx.send(f"Files:\n```\n{file_list}\n```")
                    elif file_count > 3:
                        await ctx.send(f"📄 {file_count} files downloaded (too many to list)")

                else:
                    await ctx.send(f"❌ Twitter download failed: {result.error}")

            except Exception as e:
                await ctx.send(f"❌ Download error: {e!s}")
            return

        # Check if it's a Reddit URL and handle directly
        if self.reddit_handler.supports_url(url):
            await ctx.send(f"🤖 Downloading Reddit content: {url}")

            try:
                result = await self.reddit_handler.adownload(url)

                if result.success:
                    file_count = len(result.files) if result.files else 0
                    await ctx.send(f"✅ Reddit download completed! Downloaded {file_count} files to `.downloads/`")

                    # Show some files if available
                    if result.files and file_count <= 3:
                        file_list = "\n".join([f"📄 {f.name}" for f in result.files[:3]])
                        await ctx.send(f"Files:\n```\n{file_list}\n```")
                    elif file_count > 3:
                        await ctx.send(f"📄 {file_count} files downloaded (too many to list)")

                else:
                    await ctx.send(f"❌ Reddit download failed: {result.error}")

            except Exception as e:
                await ctx.send(f"❌ Download error: {e!s}")
            return

        # Fallback to existing queue-based system for other URLs
        if not self.bot.download_manager.validate_url(url):
            await ctx.send("Invalid URL provided.")
            return

        try:
            await self.bot.queue_manager.add_to_queue(url, ctx.author.id, ctx.channel.id)
            await ctx.send(f"Added {url} to download queue.")
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name="info")
    async def info(self, ctx: commands.Context, url: str):
        """Get metadata information about a URL without downloading."""
        if self.twitter_handler.supports_url(url):
            await ctx.send(f"🔍 Getting Twitter metadata: {url}")

            try:
                metadata = await self.twitter_handler.aget_metadata(url)

                # Build info message
                info_lines = ["🐦 **Twitter Content Info**"]

                if metadata.title:
                    info_lines.append(
                        f"📝 **Content:** {metadata.title[:200]}{'...' if len(metadata.title) > 200 else ''}"
                    )
                if metadata.uploader:
                    info_lines.append(f"👤 **Author:** {metadata.uploader}")
                if metadata.upload_date:
                    info_lines.append(f"📅 **Date:** {metadata.upload_date}")
                if metadata.like_count:
                    info_lines.append(f"❤️ **Likes:** {metadata.like_count}")
                if metadata.view_count:
                    info_lines.append(f"🔄 **Retweets:** {metadata.view_count}")

                await ctx.send("\n".join(info_lines))

            except Exception as e:
                await ctx.send(f"❌ Failed to get metadata: {e!s}")

        elif self.reddit_handler.supports_url(url):
            await ctx.send(f"🔍 Getting Reddit metadata: {url}")

            try:
                metadata = await self.reddit_handler.aget_metadata(url)

                # Build info message
                info_lines = ["🤖 **Reddit Content Info**"]

                if metadata.title:
                    info_lines.append(
                        f"📝 **Title:** {metadata.title[:200]}{'...' if len(metadata.title) > 200 else ''}"
                    )
                if metadata.uploader:
                    info_lines.append(f"👤 **Author:** {metadata.uploader}")
                if metadata.raw_metadata and metadata.raw_metadata.get("subreddit"):
                    info_lines.append(f"📂 **Subreddit:** r/{metadata.raw_metadata['subreddit']}")
                if metadata.like_count:
                    info_lines.append(f"⬆️ **Score:** {metadata.like_count}")
                if metadata.raw_metadata and metadata.raw_metadata.get("num_comments"):
                    info_lines.append(f"💬 **Comments:** {metadata.raw_metadata['num_comments']}")
                if metadata.upload_date:
                    info_lines.append(f"📅 **Posted:** {metadata.upload_date}")

                await ctx.send("\n".join(info_lines))

            except Exception as e:
                await ctx.send(f"❌ Failed to get metadata: {e!s}")

        else:
            await ctx.send("ℹ️ Metadata extraction currently only supported for Twitter/X and Reddit URLs")

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
