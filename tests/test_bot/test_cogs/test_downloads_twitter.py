"""Tests for Twitter download functionality in downloads cog."""

import pytest
from discord.ext import commands
from pathlib import Path

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.downloads.handlers.twitter_handler import TwitterHandler


class TestDownloadsCogTwitter:
    """Test Twitter-specific functionality in DownloadCog."""

    @pytest.fixture(scope="function")
    def fixture_twitter_cog_test(self, fixture_mock_bot_test, mocker) -> DownloadCog:
        """Create DownloadCog instance for testing."""
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
    async def test_download_twitter_url_success(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker,
        tmp_path
    ):
        """Test successful Twitter URL download."""
        # Use the pre-mocked TwitterHandler from fixture
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler

        # Mock URL support check
        mock_handler.supports_url.return_value = True

        # Mock successful download result
        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [tmp_path / "video.mp4"]
        mock_result.metadata = {"title": "Test Tweet"}
        mock_handler.adownload.return_value = mock_result

        # Test Twitter URL
        url = "https://twitter.com/user/status/123456789"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify TwitterHandler methods were called
        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)

        # Verify success message sent (multiple calls expected)
        assert fixture_mock_ctx_test.send.call_count >= 2

        # Check messages sent
        sent_messages = [call[0][0] for call in fixture_mock_ctx_test.send.call_args_list]

        # Should have downloading message and success message
        assert any("🐦 Downloading Twitter content:" in msg for msg in sent_messages)
        assert any("✅ Twitter download completed!" in msg for msg in sent_messages)

    @pytest.mark.asyncio
    async def test_download_x_url_success(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker,
        tmp_path
    ):
        """Test successful X.com URL download."""
        # Use the pre-mocked TwitterHandler from fixture
        mock_handler = fixture_twitter_cog_test._mock_twitter_handler

        # Mock URL support check
        mock_handler.supports_url.return_value = True

        # Mock successful download result
        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [tmp_path / "image.jpg", tmp_path / "video.mp4"]
        mock_result.metadata = {"title": "Test X Post"}
        mock_handler.adownload.return_value = mock_result

        # Test X.com URL
        url = "https://x.com/user/status/987654321"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify TwitterHandler methods were called
        mock_handler.supports_url.assert_called_once_with(url)
        mock_handler.adownload.assert_called_once_with(url)

        # Verify success message sent (multiple calls expected)
        assert fixture_mock_ctx_test.send.call_count >= 2

        # Check messages sent
        sent_messages = [call[0][0] for call in fixture_mock_ctx_test.send.call_args_list]

        # Should have downloading message and success message
        assert any("🐦 Downloading Twitter content:" in msg for msg in sent_messages)
        assert any("✅ Twitter download completed!" in msg for msg in sent_messages)

    @pytest.mark.asyncio
    async def test_download_twitter_url_failure(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test failed Twitter URL download."""
        # Mock TwitterHandler
        mock_handler = mocker.patch('boss_bot.bot.cogs.downloads.TwitterHandler')
        mock_instance = mock_handler.return_value

        # Mock failed download result
        mock_result = mocker.Mock()
        mock_result.success = False
        mock_result.error = "Failed to download tweet"
        mock_result.files = []
        mock_instance.download.return_value = mock_result

        # Test Twitter URL
        url = "https://twitter.com/user/status/invalid"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify TwitterHandler was used
        mock_handler.assert_called_once()
        mock_instance.download.assert_called_once_with(url)

        # Verify error message sent
        fixture_mock_ctx_test.send.assert_called()
        call_args = fixture_mock_ctx_test.send.call_args[0][0]
        assert "❌ Twitter download failed:" in call_args
        assert "Failed to download tweet" in call_args

    @pytest.mark.asyncio
    async def test_download_twitter_handler_exception(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test Twitter handler raising exception."""
        # Mock TwitterHandler to raise exception
        mock_handler = mocker.patch('boss_bot.bot.cogs.downloads.TwitterHandler')
        mock_instance = mock_handler.return_value
        mock_instance.download.side_effect = Exception("Gallery-dl not found")

        # Test Twitter URL
        url = "https://twitter.com/user/status/123"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify exception message sent to user
        fixture_mock_ctx_test.send.assert_called()
        call_args = fixture_mock_ctx_test.send.call_args[0][0]
        assert "Gallery-dl not found" in call_args

    @pytest.mark.asyncio
    async def test_download_non_twitter_url_fallback(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test non-Twitter URL falls back to queue system."""
        # Mock bot's queue manager
        fixture_twitter_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Test non-Twitter URL
        url = "https://youtube.com/watch?v=123"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify queue manager was called (fallback behavior)
        fixture_twitter_cog_test.bot.queue_manager.add_to_queue.assert_called_once_with(url)

        # Verify queue confirmation message sent
        fixture_mock_ctx_test.send.assert_called()
        call_args = fixture_mock_ctx_test.send.call_args[0][0]
        assert "Added to download queue:" in call_args

    @pytest.mark.asyncio
    async def test_download_metadata_only_twitter(
        self,
        fixture_twitter_cog_test,
        fixture_mock_ctx_test,
        mocker
    ):
        """Test Twitter download with metadata display."""
        # Mock TwitterHandler
        mock_handler = mocker.patch('boss_bot.bot.cogs.downloads.TwitterHandler')
        mock_instance = mock_handler.return_value

        # Mock successful download with rich metadata
        mock_result = mocker.Mock()
        mock_result.success = True
        mock_result.files = [Path("video.mp4")]
        mock_result.metadata = {
            "title": "Amazing video!",
            "author": "testuser",
            "upload_date": "2024-01-15",
            "description": "This is a test tweet"
        }
        mock_instance.download.return_value = mock_result

        # Test Twitter URL
        url = "https://twitter.com/testuser/status/123456789"

        await fixture_twitter_cog_test.download.callback(
            fixture_twitter_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify success message includes metadata
        fixture_mock_ctx_test.send.assert_called()
        call_args = fixture_mock_ctx_test.send.call_args[0][0]
        assert "🐦 Twitter download completed!" in call_args
        assert "📄 Title: Amazing video!" in call_args
        assert "👤 Author: testuser" in call_args
