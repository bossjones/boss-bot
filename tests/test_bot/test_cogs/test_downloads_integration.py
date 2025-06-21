"""Integration tests for platform-specific download functionality in downloads cog."""

import pytest
from discord.ext import commands
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata
from pytest_mock import MockerFixture


class TestDownloadsCogIntegration:
    """Integration tests for DownloadCog with platform strategies."""

    @pytest.fixture(scope="function")
    def fixture_integration_cog_test(self, fixture_mock_bot_test, mocker) -> DownloadCog:
        """Create DownloadCog instance with mocked strategies for testing."""
        cog = DownloadCog(fixture_mock_bot_test)

        # Mock all strategies for controlled testing
        for platform_name, strategy in cog.strategies.items():
            mock_strategy = mocker.Mock()
            mock_strategy.supports_url = mocker.Mock(return_value=False)  # Default to False
            mock_strategy.download = mocker.AsyncMock()
            mock_strategy.get_metadata = mocker.AsyncMock()
            cog.strategies[platform_name] = mock_strategy

        return cog

    @pytest.fixture(scope="function")
    def fixture_mock_ctx_test(self, mocker) -> commands.Context:
        """Create mocked Discord context for testing."""
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.channel = mocker.Mock()
        ctx.channel.id = 67890
        return ctx

    @pytest.mark.asyncio
    async def test_twitter_url_strategy_selection(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test that Twitter URLs select the correct strategy."""
        url = "https://twitter.com/user/status/123456789"

        # Configure ONLY twitter strategy to support the URL
        for platform_name, strategy in fixture_integration_cog_test.strategies.items():
            if platform_name == "twitter":
                strategy.supports_url.return_value = True
            else:
                strategy.supports_url.return_value = False

        twitter_strategy = fixture_integration_cog_test.strategies["twitter"]

        # Mock successful download
        mock_result = Mock()
        mock_result.error = None
        mock_result.title = "Test Tweet"
        mock_result.download_method = "cli"
        twitter_strategy.download.return_value = mock_result

        # Mock upload manager to avoid upload processing in tests
        fixture_integration_cog_test.upload_manager = mocker.Mock()
        fixture_integration_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock()

        # Mock context message for download directory creation
        fixture_mock_ctx_test.message = mocker.Mock()
        fixture_mock_ctx_test.message.id = 123456789

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url,
            upload=False
        )

        # Verify Twitter strategy was selected and used
        twitter_strategy.supports_url.assert_called_with(url)
        twitter_strategy.download.assert_called_once_with(url)

        # Verify correct platform messaging
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any("🐦 Downloading Twitter/X content:" in str(call) for call in send_calls)
        assert any("✅ Twitter/X download completed!" in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_reddit_url_strategy_selection(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test that Reddit URLs select the correct strategy."""
        url = "https://www.reddit.com/r/test/comments/abc123/test_post"

        # Configure ONLY reddit strategy to support the URL
        for platform_name, strategy in fixture_integration_cog_test.strategies.items():
            if platform_name == "reddit":
                strategy.supports_url.return_value = True
            else:
                strategy.supports_url.return_value = False

        reddit_strategy = fixture_integration_cog_test.strategies["reddit"]

        # Mock successful download
        mock_result = Mock()
        mock_result.error = None
        mock_result.title = "Test Reddit Post"
        mock_result.download_method = "api"
        reddit_strategy.download.return_value = mock_result

        # Mock upload manager to avoid upload processing in tests
        fixture_integration_cog_test.upload_manager = mocker.Mock()
        fixture_integration_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock()

        # Mock context message for download directory creation
        fixture_mock_ctx_test.message = mocker.Mock()
        fixture_mock_ctx_test.message.id = 123456789

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url,
            upload=False
        )

        # Verify Reddit strategy was selected and used
        reddit_strategy.supports_url.assert_called_with(url)
        reddit_strategy.download.assert_called_once_with(url)

        # Verify correct platform messaging
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any("🤖 Downloading Reddit content:" in str(call) for call in send_calls)
        assert any("✅ Reddit download completed!" in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_youtube_url_strategy_selection(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test that YouTube URLs select the correct strategy."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Configure ONLY youtube strategy to support the URL
        for platform_name, strategy in fixture_integration_cog_test.strategies.items():
            if platform_name == "youtube":
                strategy.supports_url.return_value = True
            else:
                strategy.supports_url.return_value = False

        youtube_strategy = fixture_integration_cog_test.strategies["youtube"]

        # Mock successful download
        mock_result = Mock()
        mock_result.error = None
        mock_result.title = "Test YouTube Video"
        mock_result.download_method = "cli"
        youtube_strategy.download.return_value = mock_result

        # Mock upload manager to avoid upload processing in tests
        fixture_integration_cog_test.upload_manager = mocker.Mock()
        fixture_integration_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock()

        # Mock context message for download directory creation
        fixture_mock_ctx_test.message = mocker.Mock()
        fixture_mock_ctx_test.message.id = 123456789

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url,
            upload=False
        )

        # Verify YouTube strategy was selected and used
        youtube_strategy.supports_url.assert_called_with(url)
        youtube_strategy.download.assert_called_once_with(url)

        # Verify correct platform messaging
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any("📺 Downloading YouTube content:" in str(call) for call in send_calls)
        assert any("✅ YouTube download completed!" in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_strategy_download_failure(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test strategy download failure handling."""
        url = "https://twitter.com/user/status/123456789"

        # Configure twitter strategy to support the URL
        twitter_strategy = fixture_integration_cog_test.strategies["twitter"]
        twitter_strategy.supports_url.return_value = True

        # Mock failed download
        mock_result = Mock()
        mock_result.error = "Download failed: Network error"
        mock_result.title = None
        twitter_strategy.download.return_value = mock_result

        # Mock upload manager to avoid upload processing in tests
        fixture_integration_cog_test.upload_manager = mocker.Mock()
        fixture_integration_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock()

        # Mock context message for download directory creation
        fixture_mock_ctx_test.message = mocker.Mock()
        fixture_mock_ctx_test.message.id = 123456789

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url,
            upload=False
        )

        # Verify error message was sent
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any("❌ Twitter/X download failed: Download failed: Network error" in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_strategy_exception_handling(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test strategy exception handling."""
        url = "https://twitter.com/user/status/123456789"

        # Configure twitter strategy to support the URL but throw exception
        twitter_strategy = fixture_integration_cog_test.strategies["twitter"]
        twitter_strategy.supports_url.return_value = True
        twitter_strategy.download.side_effect = Exception("Strategy crashed")

        # Mock upload manager to avoid upload processing in tests
        fixture_integration_cog_test.upload_manager = mocker.Mock()
        fixture_integration_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock()

        # Mock context message for download directory creation
        fixture_mock_ctx_test.message = mocker.Mock()
        fixture_mock_ctx_test.message.id = 123456789

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url,
            upload=False
        )

        # Verify error message was sent
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any("❌ Download error: Strategy crashed" in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_unsupported_url_fallback_to_queue(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test fallback to queue system for unsupported URLs."""
        url = "https://unsupported-site.com/content/123"

        # Configure all strategies to not support the URL
        for strategy in fixture_integration_cog_test.strategies.values():
            strategy.supports_url.return_value = False

        # Mock bot managers for fallback
        fixture_integration_cog_test.bot.download_manager.validate_url.return_value = True
        fixture_integration_cog_test.bot.queue_manager.add_to_queue = AsyncMock()

        await fixture_integration_cog_test.download.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify fallback to queue system
        fixture_integration_cog_test.bot.queue_manager.add_to_queue.assert_called_once_with(
            url,
            fixture_mock_ctx_test.author.id,
            fixture_mock_ctx_test.channel.id
        )

        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert any(f"Added {url} to download queue." in str(call) for call in send_calls)

    @pytest.mark.asyncio
    async def test_metadata_command_with_twitter_metadata(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test metadata command with Twitter metadata."""
        url = "https://twitter.com/user/status/123456789"

        # Configure twitter strategy
        twitter_strategy = fixture_integration_cog_test.strategies["twitter"]
        twitter_strategy.supports_url.return_value = True

        # Mock metadata response
        mock_metadata = Mock()
        mock_metadata.title = "Test Tweet Content"
        mock_metadata.uploader = "@testuser"
        mock_metadata.upload_date = "2024-01-01"
        mock_metadata.like_count = 100
        mock_metadata.view_count = 50  # This becomes retweets for Twitter
        twitter_strategy.get_metadata.return_value = mock_metadata

        await fixture_integration_cog_test.metadata.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify metadata extraction was called
        twitter_strategy.get_metadata.assert_called_once_with(url)

        # Verify metadata display
        send_calls = fixture_mock_ctx_test.send.call_args_list
        info_message = str(send_calls[-1])  # Last message should be the info

        assert "🐦 **Twitter/X Content Info**" in info_message
        assert "Test Tweet Content" in info_message
        assert "@testuser" in info_message
        assert "2024-01-01" in info_message
        assert "❤️ **Likes:** 100" in info_message
        assert "🔄 **Retweets:** 50" in info_message

    @pytest.mark.asyncio
    async def test_metadata_command_with_reddit_metadata(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test metadata command with Reddit metadata."""
        url = "https://www.reddit.com/r/test/comments/abc123/test_post"

        # Configure ONLY reddit strategy to support the URL
        for platform_name, strategy in fixture_integration_cog_test.strategies.items():
            if platform_name == "reddit":
                strategy.supports_url.return_value = True
            else:
                strategy.supports_url.return_value = False

        reddit_strategy = fixture_integration_cog_test.strategies["reddit"]

        # Mock metadata response
        mock_metadata = Mock()
        mock_metadata.title = "Test Reddit Post"
        mock_metadata.uploader = "testuser"
        mock_metadata.upload_date = "2024-01-01"
        mock_metadata.like_count = 250
        mock_metadata.raw_metadata = {
            "subreddit": "test",
            "num_comments": 42
        }
        reddit_strategy.get_metadata.return_value = mock_metadata

        await fixture_integration_cog_test.metadata.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify metadata extraction was called
        reddit_strategy.get_metadata.assert_called_once_with(url)

        # Verify metadata display
        send_calls = fixture_mock_ctx_test.send.call_args_list
        info_message = str(send_calls[-1])  # Last message should be the info

        assert "🤖 **Reddit Content Info**" in info_message
        assert "Test Reddit Post" in info_message
        assert "testuser" in info_message
        assert "📂 **Subreddit:** r/test" in info_message
        assert "⬆️ **Score:** 250" in info_message
        assert "💬 **Comments:** 42" in info_message

    @pytest.mark.asyncio
    async def test_strategies_command_display(
        self,
        fixture_integration_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test strategies command showing current configuration."""
        await fixture_integration_cog_test.show_strategies.callback(
            fixture_integration_cog_test,
            fixture_mock_ctx_test
        )

        # Verify strategies display
        send_calls = fixture_mock_ctx_test.send.call_args_list
        strategies_message = str(send_calls[-1])

        assert "🔧 **Download Strategy Configuration**" in strategies_message
        assert "🐦 Twitter/X:" in strategies_message
        assert "🤖 Reddit:" in strategies_message
        assert "📺 YouTube:" in strategies_message
        assert "📷 Instagram:" in strategies_message
        assert "🔄 **API Fallback**" in strategies_message
