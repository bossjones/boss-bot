"""Minimal tests for Twitter download functionality in downloads cog."""

import pytest
from discord.ext import commands
from pathlib import Path

from boss_bot.bot.cogs.downloads import DownloadCog


class TestDownloadsCogTwitterMinimal:
    """Minimal tests for Twitter-specific functionality in DownloadCog."""

    @pytest.fixture(scope="function")
    def fixture_twitter_cog_minimal_test(self, fixture_mock_bot_test, mocker) -> DownloadCog:
        """Create DownloadCog instance with mocked TwitterHandler for testing."""
        # Mock TwitterHandler before cog instantiation
        mock_twitter_handler = mocker.Mock()
        # Make async methods return AsyncMock
        mock_twitter_handler.adownload = mocker.AsyncMock()
        mock_twitter_handler.aget_metadata = mocker.AsyncMock()
        mocker.patch('boss_bot.bot.cogs.downloads.TwitterHandler', return_value=mock_twitter_handler)

        cog = DownloadCog(fixture_mock_bot_test)
        # Store the mock for easy access in tests
        cog._mock_twitter_handler = mock_twitter_handler
        return cog

    @pytest.fixture(scope="function")
    def fixture_mock_ctx_minimal_test(self, mocker) -> commands.Context:
        """Create mocked Discord context for testing."""
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.channel = mocker.Mock()
        ctx.channel.id = 67890
        return ctx

    @pytest.mark.asyncio
    async def test_twitter_url_success(
        self,
        fixture_twitter_cog_minimal_test,
        fixture_mock_ctx_minimal_test,
        mocker,
        tmp_path
    ):
        """Test successful Twitter URL download."""
        # Use the pre-mocked TwitterHandler from fixture
        mock_handler = fixture_twitter_cog_minimal_test._mock_twitter_handler

        # Mock URL support check
        mock_handler.supports_url.return_value = True

        # Mock successful download result
        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [tmp_path / "video.mp4"]
        mock_handler.adownload.return_value = mock_result

        # Test Twitter URL
        url = "https://twitter.com/user/status/123456789"

        await fixture_twitter_cog_minimal_test.download.callback(
            fixture_twitter_cog_minimal_test,
            fixture_mock_ctx_minimal_test,
            url
        )

        # Verify TwitterHandler methods were called
        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)

        # Verify messages were sent
        assert fixture_mock_ctx_minimal_test.send.call_count >= 2

    @pytest.mark.asyncio
    async def test_twitter_url_failure(
        self,
        fixture_twitter_cog_minimal_test,
        fixture_mock_ctx_minimal_test,
        mocker
    ):
        """Test failed Twitter URL download."""
        # Use the pre-mocked TwitterHandler from fixture
        mock_handler = fixture_twitter_cog_minimal_test._mock_twitter_handler

        # Mock URL support check
        mock_handler.supports_url.return_value = True

        # Mock failed download result
        mock_result = mocker.Mock()
        mock_result.success = False
        mock_result.error = "Failed to download tweet"
        mock_handler.adownload.return_value = mock_result

        # Test Twitter URL
        url = "https://twitter.com/user/status/invalid"

        await fixture_twitter_cog_minimal_test.download.callback(
            fixture_twitter_cog_minimal_test,
            fixture_mock_ctx_minimal_test,
            url
        )

        # Verify TwitterHandler methods were called
        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)

        # Verify error message was sent
        assert fixture_mock_ctx_minimal_test.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_non_twitter_url_fallback(
        self,
        fixture_twitter_cog_minimal_test,
        fixture_mock_ctx_minimal_test,
        mocker
    ):
        """Test non-Twitter URL falls back to queue system."""
        # Use the pre-mocked TwitterHandler from fixture
        mock_handler = fixture_twitter_cog_minimal_test._mock_twitter_handler

        # Mock URL support check to return False (not a Twitter URL)
        mock_handler.supports_url.return_value = False

        # Mock bot's download manager and queue manager
        fixture_twitter_cog_minimal_test.bot.download_manager.validate_url = mocker.Mock(return_value=True)
        fixture_twitter_cog_minimal_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Test non-Twitter URL
        url = "https://youtube.com/watch?v=123"

        await fixture_twitter_cog_minimal_test.download.callback(
            fixture_twitter_cog_minimal_test,
            fixture_mock_ctx_minimal_test,
            url
        )

        # Verify TwitterHandler was checked but not used
        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_not_called()

        # Verify queue manager was called (fallback behavior)
        fixture_twitter_cog_minimal_test.bot.queue_manager.add_to_queue.assert_called_once()

        # Verify message was sent
        assert fixture_mock_ctx_minimal_test.send.call_count >= 1
