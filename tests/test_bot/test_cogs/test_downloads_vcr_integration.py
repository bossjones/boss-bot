"""VCR-based integration tests for downloads cog with real network requests."""

import pytest
from discord.ext import commands
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from pytest_mock import MockerFixture


class TestDownloadsCogVCRIntegration:
    """VCR integration tests for real network requests with downloads cog."""

    @pytest.fixture(scope="function")
    def fixture_vcr_cog_test(self, fixture_mock_bot_test) -> DownloadCog:
        """Create DownloadCog instance for VCR testing with real strategies."""
        cog = DownloadCog(fixture_mock_bot_test)
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

    @pytest.mark.default_cassette("test_twitter_download_helldiversalert.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "port", "path"],
        ignore_localhost=False,
    )
    @pytest.mark.asyncio
    async def test_twitter_download_with_vcr_recording(
        self,
        fixture_vcr_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test Twitter/X download with VCR recording of real network requests.

        This test will record network requests to:
        https://x.com/HelldiversAlert/status/1927338030467002589

        The cassette will be saved as test_twitter_download_helldiversalert.yaml.
        """
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Mock the download_manager to avoid actual file operations
        fixture_vcr_cog_test.bot.download_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.download_manager.validate_url = mocker.Mock(return_value=True)

        # Mock queue_manager to avoid queue operations in integration test
        fixture_vcr_cog_test.bot.queue_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock storage operations to avoid actual file writes
        download_dir = Path("/tmp/test_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.twitter_strategy.Path", return_value=download_dir)
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Execute the download command
        await fixture_vcr_cog_test.download.callback(
            fixture_vcr_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify interaction occurred
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        # Check for Twitter-specific messaging (should contain platform indicators)
        all_messages = " ".join(str(call) for call in send_calls)

        # Should contain Twitter/X platform indicators
        assert any(
            indicator in all_messages.lower()
            for indicator in ["twitter", "x.com", "🐦"]
        ), f"Expected Twitter platform indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_twitter_metadata_helldiversalert.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "port", "path"],
        ignore_localhost=False,
    )
    @pytest.mark.asyncio
    async def test_twitter_metadata_with_vcr_recording(
        self,
        fixture_vcr_cog_test,
        fixture_mock_ctx_test,
        mocker,
    ):
        """Test Twitter/X metadata extraction with VCR recording.

        This test records the network requests needed to extract metadata
        from the Twitter/X post without downloading the actual media files.
        The cassette will be saved as test_twitter_metadata_helldiversalert.yaml.
        """
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Execute the metadata command
        await fixture_vcr_cog_test.metadata.callback(
            fixture_vcr_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify metadata extraction occurred
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        # Check for metadata indicators
        all_messages = " ".join(str(call) for call in send_calls)

        # Should contain metadata indicators
        assert any(
            indicator in all_messages.lower()
            for indicator in ["metadata", "content", "twitter", "x.com", "🐦"]
        ), f"Expected metadata indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_twitter_api_mode_helldiversalert.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "port", "path"],
        ignore_localhost=False,
    )
    @pytest.mark.asyncio
    async def test_twitter_strategy_api_mode_with_vcr(
        self,
        fixture_vcr_cog_test,
        fixture_mock_ctx_test,
        mocker,
        monkeypatch,
    ):
        """Test Twitter strategy in API mode with VCR recording.

        This test forces the Twitter strategy to use API-direct mode
        and records the actual API calls made to extract content.
        The cassette will be saved as test_twitter_api_mode_helldiversalert.yaml.
        """
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Force API mode for Twitter strategy
        monkeypatch.setenv("TWITTER_USE_API_CLIENT", "true")
        monkeypatch.setenv("DOWNLOAD_API_FALLBACK_TO_CLI", "true")

        # Recreate the cog to pick up new environment variables
        fixture_vcr_cog_test = DownloadCog(fixture_vcr_cog_test.bot)

        # Mock storage operations
        download_dir = Path("/tmp/test_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.twitter_strategy.Path", return_value=download_dir)
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Mock the download_manager and queue_manager
        fixture_vcr_cog_test.bot.download_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.download_manager.validate_url = mocker.Mock(return_value=True)
        fixture_vcr_cog_test.bot.queue_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Execute the download command
        await fixture_vcr_cog_test.download.callback(
            fixture_vcr_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify API mode execution
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = " ".join(str(call) for call in send_calls)

        # Should indicate API mode or fallback behavior
        assert any(
            indicator in all_messages.lower()
            for indicator in ["twitter", "x.com", "api", "🐦", "🚀", "download"]
        ), f"Expected API mode indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_twitter_cli_mode_helldiversalert.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "port", "path"],
        ignore_localhost=False,
    )
    @pytest.mark.asyncio
    async def test_twitter_strategy_cli_mode_with_vcr(
        self,
        fixture_vcr_cog_test,
        fixture_mock_ctx_test,
        mocker,
        monkeypatch,
    ):
        """Test Twitter strategy in CLI mode with VCR recording.

        This test forces the Twitter strategy to use CLI subprocess mode
        and records any network requests made during CLI execution.
        The cassette will be saved as test_twitter_cli_mode_helldiversalert.yaml.
        """
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Force CLI mode for Twitter strategy
        monkeypatch.setenv("TWITTER_USE_API_CLIENT", "false")
        monkeypatch.setenv("DOWNLOAD_API_FALLBACK_TO_CLI", "false")

        # Recreate the cog to pick up new environment variables
        fixture_vcr_cog_test = DownloadCog(fixture_vcr_cog_test.bot)

        # Mock subprocess execution to avoid actual CLI calls
        mock_process = mocker.Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"title": "Test Tweet", "uploader": "HelldiversAlert"}'
        mock_process.stderr = ""

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

        # Mock storage operations
        download_dir = Path("/tmp/test_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.twitter_strategy.Path", return_value=download_dir)
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Mock the download_manager and queue_manager
        fixture_vcr_cog_test.bot.download_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.download_manager.validate_url = mocker.Mock(return_value=True)
        fixture_vcr_cog_test.bot.queue_manager = mocker.Mock()
        fixture_vcr_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Execute the download command
        await fixture_vcr_cog_test.download.callback(
            fixture_vcr_cog_test,
            fixture_mock_ctx_test,
            url
        )

        # Verify CLI mode execution
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = " ".join(str(call) for call in send_calls)

        # Should indicate CLI mode execution
        assert any(
            indicator in all_messages.lower()
            for indicator in ["twitter", "x.com", "🐦", "🖥️", "download"]
        ), f"Expected CLI mode indicators in messages: {all_messages}"
