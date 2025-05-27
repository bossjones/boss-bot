"""Tests for Twitter download functionality in downloads cog."""

import pytest
from discord.ext import commands
from pathlib import Path

from boss_bot.bot.cogs.downloads import DownloadCog
from pytest_mock import MockerFixture


class TestDownloadsCogTwitter:
    """Tests for Twitter-specific functionality in DownloadCog."""

    @pytest.fixture(scope="function")
    def fixture_twitter_cog_test(self, fixture_mock_bot_test, mocker) -> DownloadCog:
        """Create DownloadCog instance with mocked TwitterHandler for testing."""
        # Mock TwitterHandler class before cog instantiation
        mock_twitter_handler = mocker.Mock()
        # Make async methods return AsyncMock
        mock_twitter_handler.adownload = mocker.AsyncMock()
        mock_twitter_handler.aget_metadata = mocker.AsyncMock()

        # Patch the TwitterHandler class import
        mock_handler_class = mocker.patch('boss_bot.bot.cogs.downloads.TwitterHandler')
        mock_handler_class.return_value = mock_twitter_handler

        cog = DownloadCog(fixture_mock_bot_test)

        # Replace the instance's handler with our mock for testing
        cog.twitter_handler = mock_twitter_handler

        # Store the mock for easy access in tests
        cog._mock_twitter_handler = mock_twitter_handler
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
    async def test_twitter_url_success(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker,
        tmp_path
    ):
        """Test successful Twitter URL download."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = True

        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [tmp_path / "video.mp4"]
        mock_handler.adownload.return_value = mock_result

        url = "https://twitter.com/user/status/123456789"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)
        assert fixture_mock_ctx_test.send.call_count >= 2

    @pytest.mark.asyncio
    async def test_x_url_success(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker,
        tmp_path
    ):
        """Test successful X.com URL download."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = True

        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [tmp_path / "image.jpg", tmp_path / "video.mp4"]
        mock_handler.adownload.return_value = mock_result

        url = "https://x.com/user/status/987654321"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)
        assert fixture_mock_ctx_test.send.call_count >= 2

    @pytest.mark.asyncio
    async def test_twitter_url_failure(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test failed Twitter URL download."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = True

        mock_result = mocker.Mock()
        mock_result.success = False
        mock_result.error = "Failed to download tweet"
        mock_handler.adownload.return_value = mock_result

        url = "https://twitter.com/user/status/invalid"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)
        assert fixture_mock_ctx_test.send.call_count >= 2

    @pytest.mark.asyncio
    async def test_twitter_handler_exception(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test Twitter handler raising exception."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = True
        mock_handler.adownload.side_effect = Exception("Gallery-dl not found")

        url = "https://twitter.com/user/status/123"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        assert fixture_mock_ctx_test.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_non_twitter_url_fallback(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test non-Twitter URL falls back to queue system."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = False

        # Mock bot's download manager and queue manager
        fixture_twitter_cog_test.bot.download_manager.validate_url = mocker.Mock(return_value=True)
        fixture_twitter_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        url = "https://youtube.com/watch?v=123"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_not_called()
        fixture_twitter_cog_test.bot.queue_manager.add_to_queue.assert_called_once()
        assert fixture_mock_ctx_test.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_metadata_only_twitter(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test Twitter download with metadata display."""
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler
        mock_handler.supports_url.return_value = True

        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [Path("video.mp4")]
        mock_result.metadata = {
            "title": "Amazing video!",
            "author": "testuser",
            "upload_date": "2024-01-15",
            "description": "This is a test tweet"
        }
        mock_handler.adownload.return_value = mock_result

        url = "https://twitter.com/testuser/status/123456789"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)
        assert fixture_mock_ctx_test.send.call_count >= 2
