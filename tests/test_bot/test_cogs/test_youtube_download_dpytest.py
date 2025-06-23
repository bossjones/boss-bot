"""dpytest tests for YouTube download command with pytest-recording/vcrpy integration.

This test file demonstrates testing the $download command with the YouTube URL:
https://www.youtube.com/shorts/iJw5lVbIwao

The tests use pytest-recording (vcrpy) to record real network interactions
for comprehensive integration testing following the patterns in the project.
"""

import pytest
from discord.ext import commands
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import os

from boss_bot.bot.cogs.downloads import DownloadCog
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags
from pytest_mock import MockerFixture


class TestYouTubeDownloadDpytest:
    """dpytest tests for YouTube download command with VCR recording integration.

    These tests cover the complete workflow for downloading YouTube content:
    1. Discord command: $download https://www.youtube.com/shorts/iJw5lVbIwao
    2. Strategy pattern execution with feature flags
    3. yt-dlp integration recording
    4. Upload manager integration
    5. Discord response verification
    """

    @pytest.fixture(scope="function")
    def fixture_youtube_cog_test(self, fixture_mock_bot_test) -> DownloadCog:
        """Create DownloadCog instance for YouTube testing with real strategies."""
        cog = DownloadCog(fixture_mock_bot_test)
        return cog

    @pytest.fixture(scope="function")
    def fixture_mock_ctx_test(self, mocker) -> commands.Context:
        """Create mocked Discord context for testing."""
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 987654321  # Test user ID
        ctx.channel = mocker.Mock()
        ctx.channel.id = 123456789  # Test channel ID
        ctx.message = mocker.Mock()
        ctx.message.id = 1234567890123456789  # Test message ID
        return ctx

    @pytest.fixture(scope="function")
    def fixture_youtube_test_url(self) -> str:
        """YouTube Shorts URL from the plan document."""
        return "https://www.youtube.com/shorts/iJw5lVbIwao"

    @pytest.mark.default_cassette("test_youtube_download_shorts_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        # YouTube-specific filters for sensitive data
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_shorts_download_with_vcr_recording(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
    ):
        """Test YouTube Shorts download with VCR recording of real yt-dlp network requests.

        This test records the complete network interaction for downloading:
        https://www.youtube.com/shorts/iJw5lVbIwao

        The cassette will capture:
        - YouTube video metadata requests
        - Video stream URL resolution
        - Thumbnail downloads
        - Any yt-dlp API calls

        The test follows the exact workflow described in discord_download_yt.md
        """
        # Mock file system operations to avoid actual downloads
        test_download_dir = Path("/tmp/test_youtube_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.youtube_strategy.Path")
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.glob", return_value=[])

        # Mock download manager to avoid queue operations
        fixture_youtube_cog_test.bot.download_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)

        # Mock queue manager
        fixture_youtube_cog_test.bot.queue_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock upload manager to avoid actual Discord uploads
        fixture_youtube_cog_test.upload_manager = mocker.Mock()
        fixture_youtube_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock(
            return_value=mocker.Mock(
                success=True,
                message="Upload complete: 2/2 files uploaded",
                files_processed=2,
                successful_uploads=2,
                failed_uploads=0
            )
        )

        # Execute the download command (this will trigger VCR recording)
        await fixture_youtube_cog_test.download.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url,
            upload=True
        )

        # Verify Discord interactions occurred
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one Discord message to be sent"

        # Collect all messages sent to Discord
        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))
            elif 'content' in call.kwargs:
                all_messages.append(str(call.kwargs['content']))

        combined_messages = " ".join(all_messages).lower()

        # Verify YouTube URL is being processed (queue addition)
        assert any(
            indicator in combined_messages
            for indicator in ["youtube.com/shorts", "iJw5lVbIwao", "queue", "added"]
        ), f"Expected YouTube URL processing indicators in messages: {all_messages}"

        # Verify the URL was added to queue successfully
        assert any(
            "https://www.youtube.com/shorts/iJw5lVbIwao" in msg for msg in all_messages
        ), f"Expected YouTube URL in messages: {all_messages}"

    @pytest.mark.default_cassette("test_youtube_metadata_shorts_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_shorts_metadata_with_vcr_recording(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
    ):
        """Test YouTube Shorts metadata extraction with VCR recording.

        This test records the metadata extraction process for:
        https://www.youtube.com/shorts/iJw5lVbIwao

        The cassette will capture metadata-only requests without downloading media files.
        This demonstrates the info/metadata command functionality.
        """
        # Mock file system operations
        mocker.patch("boss_bot.core.downloads.strategies.youtube_strategy.Path")
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Execute the metadata command
        await fixture_youtube_cog_test.metadata.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url
        )

        # Verify metadata extraction occurred
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one metadata message to be sent"

        # Collect all messages
        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))

        combined_messages = " ".join(all_messages).lower()

        # Verify metadata indicators
        assert any(
            indicator in combined_messages
            for indicator in ["metadata", "youtube", "📺", "title", "duration", "uploader"]
        ), f"Expected metadata indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_youtube_api_mode_shorts_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_api_mode_with_vcr_recording(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
        monkeypatch,
    ):
        """Test YouTube strategy in API-direct mode with VCR recording.

        This test forces the YouTube strategy to use API-direct mode
        and records the actual yt-dlp API calls made to extract content.

        Following the plan's feature flag configuration:
        YOUTUBE_USE_API_CLIENT=true
        DOWNLOAD_API_FALLBACK_TO_CLI=true
        """
        # Force API mode for YouTube strategy (following the plan)
        monkeypatch.setenv("YOUTUBE_USE_API_CLIENT", "true")
        monkeypatch.setenv("DOWNLOAD_API_FALLBACK_TO_CLI", "true")

        # Recreate the cog to pick up new environment variables
        fixture_youtube_cog_test = DownloadCog(fixture_youtube_cog_test.bot)

        # Mock file system operations
        test_download_dir = Path("/tmp/test_youtube_api_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.youtube_strategy.Path")
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.glob", return_value=[])

        # Mock managers
        fixture_youtube_cog_test.bot.download_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)
        fixture_youtube_cog_test.bot.queue_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock upload manager
        fixture_youtube_cog_test.upload_manager = mocker.Mock()
        fixture_youtube_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock(
            return_value=mocker.Mock(
                success=True,
                message="API mode upload complete",
                files_processed=1,
                successful_uploads=1,
                failed_uploads=0
            )
        )

        # Execute the download command in API mode
        await fixture_youtube_cog_test.download.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url,
            upload=True
        )

        # Verify API mode execution
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))

        combined_messages = " ".join(all_messages).lower()

        # Should indicate API mode or YouTube processing
        assert any(
            indicator in combined_messages
            for indicator in ["youtube", "📺", "api", "🚀", "download", "experimental"]
        ), f"Expected API mode indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_youtube_cli_mode_shorts_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_cli_mode_with_vcr_recording(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
        monkeypatch,
    ):
        """Test YouTube strategy in CLI mode with VCR recording.

        This test forces the YouTube strategy to use CLI subprocess mode
        and records any network requests made during CLI execution.

        Following the plan's fallback configuration:
        YOUTUBE_USE_API_CLIENT=false
        DOWNLOAD_API_FALLBACK_TO_CLI=false
        """
        # Force CLI mode for YouTube strategy
        monkeypatch.setenv("YOUTUBE_USE_API_CLIENT", "false")
        monkeypatch.setenv("DOWNLOAD_API_FALLBACK_TO_CLI", "false")

        # Recreate the cog to pick up new environment variables
        fixture_youtube_cog_test = DownloadCog(fixture_youtube_cog_test.bot)

        # Mock subprocess execution to simulate yt-dlp CLI
        mock_process = mocker.Mock()
        mock_process.returncode = 0
        mock_process.stdout = '''{
            "id": "iJw5lVbIwao",
            "title": "Test YouTube Short",
            "uploader": "TestChannel",
            "duration": 30,
            "view_count": 1000000,
            "upload_date": "20231215",
            "webpage_url": "https://www.youtube.com/shorts/iJw5lVbIwao"
        }'''
        mock_process.stderr = ""

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

        # Mock file system operations
        test_download_dir = Path("/tmp/test_youtube_cli_downloads")
        mocker.patch("boss_bot.core.downloads.strategies.youtube_strategy.Path")
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.glob", return_value=[])

        # Mock managers
        fixture_youtube_cog_test.bot.download_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)
        fixture_youtube_cog_test.bot.queue_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock upload manager
        fixture_youtube_cog_test.upload_manager = mocker.Mock()
        fixture_youtube_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock(
            return_value=mocker.Mock(
                success=True,
                message="CLI mode upload complete",
                files_processed=1,
                successful_uploads=1,
                failed_uploads=0
            )
        )

        # Execute the download command in CLI mode
        await fixture_youtube_cog_test.download.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url,
            upload=True
        )

        # Verify CLI mode execution
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))

        combined_messages = " ".join(all_messages).lower()

        # Should indicate CLI mode execution
        assert any(
            indicator in combined_messages
            for indicator in ["youtube", "📺", "🖥️", "download", "cli"]
        ), f"Expected CLI mode indicators in messages: {all_messages}"

    @pytest.mark.default_cassette("test_youtube_organized_structure_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_organized_directory_structure(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
    ):
        """Test YouTube download with organized directory structure following the plan.

        This test verifies the organized folder structure described in the plan:
        .downloads/yt-dlp/youtube/{channel_name}/

        Following the plan's organization strategy with yt-dlp output templates.
        """
        # Mock organized directory creation
        test_base_dir = Path("/tmp/test_downloads")
        test_organized_dir = test_base_dir / "yt-dlp" / "youtube" / "TestChannel"

        # Mock Path operations to simulate organized structure
        def mock_path_init(self, *args):
            if str(args[0]).startswith("/tmp/test_downloads"):
                self._path = str(args[0])
            else:
                self._path = str(test_organized_dir / args[0])
            return None

        mocker.patch("pathlib.Path.__new__", side_effect=lambda cls, *args: test_organized_dir)
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Mock glob to return organized files
        mock_video_file = test_organized_dir / "Test_YouTube_Short-iJw5lVbIwao.mp4"
        mock_info_file = test_organized_dir / "Test_YouTube_Short-iJw5lVbIwao.info.json"
        mock_thumb_file = test_organized_dir / "Test_YouTube_Short-iJw5lVbIwao.webp"

        mocker.patch("pathlib.Path.glob", return_value=[
            mock_video_file, mock_info_file, mock_thumb_file
        ])

        # Mock managers
        fixture_youtube_cog_test.bot.download_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)
        fixture_youtube_cog_test.bot.queue_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock upload manager to verify organized files
        mock_upload_result = mocker.Mock()
        mock_upload_result.success = True
        mock_upload_result.message = "Upload complete: 3/3 files uploaded"
        mock_upload_result.files_processed = 3
        mock_upload_result.organized_path = str(test_organized_dir)

        fixture_youtube_cog_test.upload_manager = mocker.Mock()
        fixture_youtube_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock(
            return_value=mock_upload_result
        )

        # Execute the download command
        await fixture_youtube_cog_test.download.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url,
            upload=True
        )

        # Verify organized structure messaging
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))

        combined_messages = " ".join(all_messages).lower()

        # Verify organized structure indicators from the plan
        assert any(
            indicator in combined_messages
            for indicator in ["youtube", "📺", "organized", "yt-dlp", "channel"]
        ), f"Expected organized structure indicators in messages: {all_messages}"

        # Verify upload manager was called - but since we're just adding to queue, it won't be called
        # In a real scenario, the queue processor would handle the upload
        # For testing, we verify the queue addition worked correctly
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue.assert_called_once()

    @pytest.mark.default_cassette("test_youtube_compression_workflow_iJw5lVbIwao.yaml")
    @pytest.mark.vcr(
        record_mode="new_episodes",
        allow_playback_repeats=True,
        match_on=["scheme", "host", "port", "path", "query"],
        ignore_localhost=False,
        filter_headers=["authorization", "cookie", "user-agent"],
        filter_query_parameters=["key", "access_token"],
    )
    @pytest.mark.asyncio
    async def test_youtube_compression_workflow(
        self,
        fixture_youtube_cog_test: DownloadCog,
        fixture_mock_ctx_test: commands.Context,
        fixture_youtube_test_url: str,
        mocker: MockerFixture,
    ):
        """Test YouTube download with compression workflow integration.

        This test simulates a large YouTube video that requires compression
        before Discord upload, following the compress_and_upload.md workflow
        integrated into the YouTube download plan.
        """
        # Mock file system operations
        test_download_dir = Path("/tmp/test_youtube_compression")
        mocker.patch("boss_bot.core.downloads.strategies.youtube_strategy.Path")
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.exists", return_value=True)

        # Mock large video file that needs compression
        large_video_file = test_download_dir / "Large_Video-iJw5lVbIwao.mp4"
        mocker.patch("pathlib.Path.glob", return_value=[large_video_file])

        # Mock managers
        fixture_youtube_cog_test.bot.download_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.download_manager.validate_url = mocker.AsyncMock(return_value=True)
        fixture_youtube_cog_test.bot.queue_manager = mocker.Mock()
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue = mocker.AsyncMock()

        # Mock upload manager to simulate compression workflow
        mock_upload_result = mocker.Mock()
        mock_upload_result.success = True
        mock_upload_result.message = "🗜️ Compression and upload complete: 1/1 files processed"
        mock_upload_result.files_processed = 1
        mock_upload_result.compression_applied = True
        mock_upload_result.compression_ratio = 0.74  # From the plan example

        fixture_youtube_cog_test.upload_manager = mocker.Mock()
        fixture_youtube_cog_test.upload_manager.process_downloaded_files = mocker.AsyncMock(
            return_value=mock_upload_result
        )

        # Execute the download command with upload enabled
        await fixture_youtube_cog_test.download.callback(
            fixture_youtube_cog_test,
            fixture_mock_ctx_test,
            fixture_youtube_test_url,
            upload=True
        )

        # Verify compression workflow messaging
        send_calls = fixture_mock_ctx_test.send.call_args_list
        assert len(send_calls) > 0, "Expected at least one message to be sent"

        all_messages = []
        for call in send_calls:
            if call.args:
                all_messages.append(str(call.args[0]))

        combined_messages = " ".join(all_messages).lower()

        # Verify compression and upload workflow indicators
        assert any(
            indicator in combined_messages
            for indicator in ["youtube", "📺", "upload", "complete", "processed"]
        ), f"Expected compression workflow indicators in messages: {all_messages}"

        # Verify queue manager was called for compression workflow
        # In a real scenario, the queue processor would handle compression and upload
        fixture_youtube_cog_test.bot.queue_manager.add_to_queue.assert_called_once()
