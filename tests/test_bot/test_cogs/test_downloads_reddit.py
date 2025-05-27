"""Tests for Reddit download functionality in DownloadCog."""
# pylint: disable=no-member
# pylint: disable=possibly-used-before-assignment
# pyright: reportImportCycles=false
# pyright: reportFunctionMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportInvalidTypeForm=false
# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=consider-using-with, consider-using-min-builtin

from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from discord.ext import commands
from pytest_mock import MockerFixture

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.bot.client import BossBot
from boss_bot.core.downloads.handlers.reddit_handler import RedditHandler


class TestDownloadsCogReddit:
    """Test class for Reddit download functionality in DownloadCog."""

    @pytest.fixture(scope="function")
    def fixture_reddit_cog_test(self, fixture_mock_bot_test: BossBot, mocker: MockerFixture) -> DownloadCog:
        """Create DownloadCog instance with mocked RedditHandler for testing.

        Args:
            fixture_mock_bot_test: Mock bot instance
            mocker: Pytest mocker fixture

        Returns:
            Configured DownloadCog instance with mocked Reddit handler
        """
        mock_reddit_handler = mocker.Mock(spec=RedditHandler)
        mock_reddit_handler.adownload = mocker.AsyncMock()
        mock_reddit_handler.aget_metadata = mocker.AsyncMock()

        mock_handler_class = mocker.patch('boss_bot.bot.cogs.downloads.RedditHandler')
        mock_handler_class.return_value = mock_reddit_handler

        cog = DownloadCog(fixture_mock_bot_test)
        cog.reddit_handler = mock_reddit_handler
        # Store mock handler for test access
        setattr(cog, '_mock_reddit_handler', mock_reddit_handler)
        return cog

    async def test_reddit_url_success(self, fixture_reddit_cog_test: DownloadCog, mocker: MockerFixture) -> None:
        """Test successful Reddit URL download."""
        # Setup
        mock_ctx = mocker.Mock(spec=commands.Context)
        mock_ctx.send = mocker.AsyncMock()
        ctx = cast(commands.Context[BossBot], mock_ctx)
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock RedditHandler methods
        fixture_reddit_cog_test.reddit_handler.supports_url.return_value = True

        # Mock successful download result
        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [Path("test1.jpg"), Path("test2.jpg")]
        fixture_reddit_cog_test.reddit_handler.adownload.return_value = mock_result

        # Execute
        await fixture_reddit_cog_test.download.callback(fixture_reddit_cog_test, ctx, url)

        # Verify
        assert ctx.send.call_count == 3
        assert "🤖 Downloading Reddit content" in ctx.send.call_args_list[0][0][0]
        assert "✅ Reddit download completed" in ctx.send.call_args_list[1][0][0]
        assert "📄 test1.jpg" in ctx.send.call_args_list[2][0][0]

    async def test_reddit_url_failure(self, fixture_reddit_cog_test: DownloadCog, mocker: MockerFixture) -> None:
        """Test Reddit URL download failure."""
        # Setup
        mock_ctx = mocker.Mock(spec=commands.Context)
        mock_ctx.send = mocker.AsyncMock()
        ctx = cast(commands.Context[BossBot], mock_ctx)
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock RedditHandler methods
        fixture_reddit_cog_test.reddit_handler.supports_url.return_value = True

        # Mock failed download result
        mock_result = mocker.Mock()
        mock_result.success = False
        mock_result.error = "Download failed"
        fixture_reddit_cog_test.reddit_handler.adownload.return_value = mock_result

        # Execute
        await fixture_reddit_cog_test.download.callback(fixture_reddit_cog_test, ctx, url)

        # Verify
        assert ctx.send.call_count == 2
        assert "🤖 Downloading Reddit content" in ctx.send.call_args_list[0][0][0]
        assert "❌ Reddit download failed" in ctx.send.call_args_list[1][0][0]

    async def test_reddit_handler_exception(self, fixture_reddit_cog_test: DownloadCog, mocker: MockerFixture) -> None:
        """Test Reddit handler exception handling."""
        # Setup
        mock_ctx = mocker.Mock(spec=commands.Context)
        mock_ctx.send = mocker.AsyncMock()
        ctx = cast(commands.Context[BossBot], mock_ctx)
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock RedditHandler methods
        fixture_reddit_cog_test.reddit_handler.supports_url.return_value = True
        fixture_reddit_cog_test.reddit_handler.adownload.side_effect = Exception("Handler error")

        # Execute
        await fixture_reddit_cog_test.download.callback(fixture_reddit_cog_test, ctx, url)

        # Verify
        assert ctx.send.call_count == 2
        assert "🤖 Downloading Reddit content" in ctx.send.call_args_list[0][0][0]
        assert "❌ Download error: Handler error" in ctx.send.call_args_list[1][0][0]

    async def test_non_reddit_url_fallback(self, fixture_reddit_cog_test: DownloadCog, mocker: MockerFixture) -> None:
        """Test that non-Reddit URLs fall back to queue system."""
        # Setup
        mock_ctx = mocker.Mock(spec=commands.Context)
        mock_ctx.send = mocker.AsyncMock()
        ctx = cast(commands.Context[BossBot], mock_ctx)
        url = "https://example.com/video"

        # Mock handlers to reject URL
        # Need to patch since we're dealing with actual handler instances
        mocker.patch.object(fixture_reddit_cog_test.twitter_handler, 'supports_url', return_value=False)
        mocker.patch.object(fixture_reddit_cog_test.reddit_handler, 'supports_url', return_value=False)

        # Execute
        await fixture_reddit_cog_test.download.callback(fixture_reddit_cog_test, ctx, url)

        # Verify fallback was called
        fixture_reddit_cog_test.bot.download_manager.validate_url.assert_called_once_with(url)

    async def test_metadata_only_reddit(self, fixture_reddit_cog_test: DownloadCog, mocker: MockerFixture) -> None:
        """Test Reddit metadata extraction via info command."""
        # Setup
        mock_ctx = mocker.Mock(spec=commands.Context)
        mock_ctx.send = mocker.AsyncMock()
        ctx = cast(commands.Context[BossBot], mock_ctx)
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock RedditHandler methods
        fixture_reddit_cog_test.reddit_handler.supports_url.return_value = True

        # Mock metadata
        mock_metadata = mocker.Mock()
        mock_metadata.title = "Test Reddit Post"
        mock_metadata.uploader = "testuser"
        mock_metadata.like_count = 42
        mock_metadata.upload_date = "2023-01-01"
        mock_metadata.raw_metadata = {
            "subreddit": "pics",
            "num_comments": 15
        }
        fixture_reddit_cog_test.reddit_handler.aget_metadata.return_value = mock_metadata

        # Execute
        await fixture_reddit_cog_test.info.callback(fixture_reddit_cog_test, ctx, url)

        # Verify
        assert ctx.send.call_count == 2
        assert "🔍 Getting Reddit metadata" in ctx.send.call_args_list[0][0][0]
        info_message = str(ctx.send.call_args_list[1][0][0])
        assert "🤖 **Reddit Content Info**" in info_message
        assert "Test Reddit Post" in info_message
        assert "testuser" in info_message
        assert "r/pics" in info_message
        assert "42" in info_message
        assert "15" in info_message
