"""Integration tests for downloads with upload functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import discord
from discord.ext import commands

from boss_bot.bot.cogs.downloads import DownloadCog


class TestDownloadsUploadIntegration:
    """Integration tests for downloads with upload functionality."""

    @pytest.fixture
    async def fixture_download_cog(self, fixture_mock_bot_test):
        """Create DownloadCog with mocked dependencies."""
        cog = DownloadCog(fixture_mock_bot_test)

        # Mock the upload manager
        cog.upload_manager = Mock()
        cog.upload_manager.process_downloaded_files = AsyncMock()

        return cog

    @pytest.fixture
    def fixture_mock_strategy(self, mocker):
        """Create mock download strategy."""
        strategy = mocker.Mock()
        strategy.supports_url.return_value = True
        strategy.download = AsyncMock()
        strategy.download_dir = Path("/tmp/downloads")

        # Mock successful download
        from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
        mock_metadata = MediaMetadata(
            url="https://twitter.com/test/status/123",
            title="Test Tweet",
            error=None,
            download_method="api"
        )
        strategy.download.return_value = mock_metadata

        return strategy

    @pytest.mark.asyncio
    async def test_download_command_with_upload_success(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command with successful upload."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock successful upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=True,
            message="Upload complete: 2/2 files uploaded",
            files_processed=2,
            successful_uploads=2,
            failed_uploads=0
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload processing was called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_called_once()

        # Verify success messages
        success_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "🎉" in call.args[0] or "✅" in call.args[0]
        ]
        assert len(success_messages) >= 2  # Download success + upload success

    @pytest.mark.asyncio
    async def test_download_command_upload_disabled(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command with upload disabled."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Execute with upload=False
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=False
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload was NOT called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_not_called()

        # Verify file location message
        location_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "📁 Files saved to" in call.args[0]
        ]
        assert len(location_messages) >= 1

    @pytest.mark.asyncio
    async def test_download_only_command_alias(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download-only command alias."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock the download method to verify it's called with upload=False
        fixture_download_cog.download = AsyncMock()

        # Execute
        await fixture_download_cog.download_only.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123"
        )

        # Verify download was called with upload=False
        fixture_download_cog.download.assert_called_once_with(
            ctx,
            "https://twitter.com/test/status/123",
            upload=False
        )

    @pytest.mark.asyncio
    async def test_download_command_upload_failure(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command when upload fails."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock failed upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=False,
            message="Upload failed: Files too large",
            files_processed=2,
            successful_uploads=0,
            failed_uploads=2,
            error="All files exceed Discord size limits"
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload processing was called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_called_once()

        # Verify warning messages
        warning_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "⚠️ Upload issues" in call.args[0]
        ]
        assert len(warning_messages) >= 1

        # Verify error details were sent
        error_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "Error details:" in call.args[0]
        ]
        assert len(error_messages) >= 1

    @pytest.mark.asyncio
    async def test_download_command_download_failure(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test download command when download itself fails."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock failed download
        from boss_bot.core.downloads.handlers.base_handler import MediaMetadata
        mock_metadata = MediaMetadata(
            url="https://twitter.com/test/status/123",
            title="Test Tweet",
            error="Network timeout during download",
            download_method="api"
        )
        fixture_mock_strategy.download.return_value = mock_metadata

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify download was called
        fixture_mock_strategy.download.assert_called_once()

        # Verify upload was NOT called due to download failure
        fixture_download_cog.upload_manager.process_downloaded_files.assert_not_called()

        # Verify error messages
        error_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "❌" in call.args[0] and "download failed" in call.args[0]
        ]
        assert len(error_messages) >= 1

    @pytest.mark.asyncio
    async def test_download_command_directory_management(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test that download command properly manages temporary directories."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock successful upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=True,
            message="Upload complete: 1/1 files uploaded",
            files_processed=1,
            successful_uploads=1,
            failed_uploads=0
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Capture the directory passed to the strategy
        original_dir = fixture_mock_strategy.download_dir
        captured_dirs = []

        def capture_download_dir(*args, **kwargs):
            captured_dirs.append(fixture_mock_strategy.download_dir)
            return fixture_mock_strategy.download.return_value

        fixture_mock_strategy.download.side_effect = capture_download_dir

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify strategy directory was temporarily changed
        assert len(captured_dirs) == 1
        temp_dir = captured_dirs[0]
        assert str(temp_dir) != str(original_dir)
        assert f"{ctx.author.id}_{ctx.message.id}" in str(temp_dir)

        # Verify directory was restored
        assert fixture_mock_strategy.download_dir == original_dir

    @pytest.mark.asyncio
    async def test_download_command_cleanup_configuration(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test that cleanup behavior respects settings configuration."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock successful upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=True,
            message="Upload complete: 1/1 files uploaded",
            files_processed=1,
            successful_uploads=1,
            failed_uploads=0
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Mock settings to disable cleanup
        fixture_download_cog.bot.settings.upload_cleanup_after_success = False

        # Mock shutil.rmtree to verify it's not called
        with patch('shutil.rmtree') as mock_rmtree:
            await fixture_download_cog.download.callback(
                fixture_download_cog,
                ctx,
                "https://twitter.com/test/status/123",
                upload=True
            )

            # Verify cleanup was not called when disabled
            mock_rmtree.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_command_platform_info_display(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test that platform-specific information is displayed correctly."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock feature flags
        fixture_download_cog.feature_flags.is_api_enabled_for_platform = mocker.Mock(
            return_value=True
        )

        # Mock successful upload
        from boss_bot.core.uploads.models import UploadResult
        mock_upload_result = UploadResult(
            success=True,
            message="Upload complete",
            files_processed=1,
            successful_uploads=1,
            failed_uploads=0
        )
        fixture_download_cog.upload_manager.process_downloaded_files.return_value = mock_upload_result

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify platform emoji and name are displayed
        download_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "🐦 Downloading Twitter/X content" in call.args[0]
        ]
        assert len(download_messages) >= 1

        # Verify API-direct message is shown
        api_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "🚀 Using experimental API-direct approach" in call.args[0]
        ]
        assert len(api_messages) >= 1

        # Verify method indication in metadata
        method_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "🚀 Downloaded using API method" in call.args[0]
        ]
        assert len(method_messages) >= 1

    @pytest.mark.asyncio
    async def test_download_command_exception_handling(
        self,
        fixture_download_cog,
        fixture_mock_strategy,
        mocker
    ):
        """Test that exceptions during download are handled gracefully."""
        # Setup
        ctx = mocker.Mock(spec=commands.Context)
        ctx.send = mocker.AsyncMock()
        ctx.author = mocker.Mock()
        ctx.author.id = 12345
        ctx.message = mocker.Mock()
        ctx.message.id = 67890

        # Mock strategy selection
        fixture_download_cog._get_strategy_for_url = mocker.Mock(
            return_value=fixture_mock_strategy
        )

        # Mock strategy to raise exception
        fixture_mock_strategy.download.side_effect = Exception("Network error")

        # Execute
        await fixture_download_cog.download.callback(
            fixture_download_cog,
            ctx,
            "https://twitter.com/test/status/123",
            upload=True
        )

        # Verify exception was handled and error message sent
        error_messages = [
            call.args[0] for call in ctx.send.call_args_list
            if "❌ Download error" in call.args[0]
        ]
        assert len(error_messages) >= 1

        # Verify upload was not called
        fixture_download_cog.upload_manager.process_downloaded_files.assert_not_called()
