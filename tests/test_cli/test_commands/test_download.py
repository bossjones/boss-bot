"""Tests for CLI download commands."""

import asyncio
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from boss_bot.cli.commands.download import app, validate_twitter_url
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


class TestValidateTwitterUrl:
    """Test URL validation function."""

    def test_valid_twitter_urls(self):
        """Test validation of valid Twitter URLs."""
        valid_urls = [
            "https://twitter.com/user/status/123456789",
            "https://x.com/user/status/123456789",
            "https://twitter.com/username",
            "https://x.com/username"
        ]

        for url in valid_urls:
            assert validate_twitter_url(url) == url

    def test_invalid_twitter_urls(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "https://youtube.com/watch",
            "https://facebook.com/post",
            "not-a-url",
            "https://example.com"
        ]

        for url in invalid_urls:
            with pytest.raises(typer.BadParameter):
                validate_twitter_url(url)


class TestDownloadCommands:
    """Test download CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_download_info_command(self, runner):
        """Test download info command."""
        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "BossBot Download Commands" in result.stdout
        assert "Twitter/X" in result.stdout
        assert "gallery-dl" in result.stdout

    def test_twitter_command_invalid_url(self, runner):
        """Test Twitter download with invalid URL."""
        result = runner.invoke(app, ["twitter", "https://youtube.com/watch"])

        assert result.exit_code == 2  # typer.BadParameter exit code
        assert "URL is not a valid Twitter/X URL" in result.stdout

    def test_twitter_command_metadata_only_success(self, runner, mocker):
        """Test Twitter metadata-only command success."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock successful metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Tweet",
            uploader="Test User",
            upload_date="2024-01-01",
            like_count=42,
            view_count=10,
            url="https://twitter.com/user/status/123",
            platform="twitter"
        )
        mock_handler.get_metadata.return_value = mock_metadata

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only"
        ])

        assert result.exit_code == 0
        assert "Metadata extracted successfully" in result.stdout
        assert "Test Tweet" in result.stdout
        assert "Test User" in result.stdout
        mock_handler.get_metadata.assert_called_once()

    def test_twitter_command_metadata_only_async(self, runner, mocker):
        """Test Twitter metadata-only command with async mode."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock asyncio.run and async metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Tweet",
            uploader="Test User",
            platform="twitter"
        )

        async def mock_aget_metadata(url):
            return mock_metadata

        mock_handler.aget_metadata = mock_aget_metadata
        mock_asyncio_run = mocker.patch('asyncio.run', return_value=mock_metadata)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only",
            "--async"
        ])

        assert result.exit_code == 0
        assert "Metadata extracted successfully" in result.stdout
        mock_asyncio_run.assert_called_once()

    def test_twitter_command_metadata_failure(self, runner, mocker):
        """Test Twitter metadata command failure."""
        # Mock TwitterHandler to raise exception
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.get_metadata.side_effect = Exception("API Error")

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only"
        ])

        assert result.exit_code == 1
        assert "Failed to extract metadata" in result.stdout

    def test_twitter_command_download_success(self, runner, mocker, tmp_path):
        """Test Twitter download command success."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock successful download
        test_files = [tmp_path / "test1.jpg", tmp_path / "test2.mp4"]
        for f in test_files:
            f.touch()  # Create empty files

        mock_result = DownloadResult(
            success=True,
            files=test_files,
            metadata={"title": "Test"}
        )
        mock_handler.download.return_value = mock_result

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--output-dir", str(tmp_path)
        ])

        assert result.exit_code == 0
        assert "Download completed successfully" in result.stdout
        assert "Downloaded 2 files" in result.stdout
        mock_handler.download.assert_called_once()

    def test_twitter_command_download_async_success(self, runner, mocker, tmp_path):
        """Test Twitter async download command success."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock successful async download
        test_files = [tmp_path / "test.jpg"]
        test_files[0].touch()

        mock_result = DownloadResult(
            success=True,
            files=test_files
        )

        async def mock_adownload(url):
            return mock_result

        mock_handler.adownload = mock_adownload
        mock_asyncio_run = mocker.patch('asyncio.run', return_value=mock_result)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--async"
        ])

        assert result.exit_code == 0
        assert "Download completed successfully" in result.stdout
        mock_asyncio_run.assert_called_once()

    def test_twitter_command_download_failure(self, runner, mocker):
        """Test Twitter download command failure."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock failed download
        mock_result = DownloadResult(
            success=False,
            error="Download failed",
            stderr="Error details"
        )
        mock_handler.download.return_value = mock_result

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123"
        ])

        assert result.exit_code == 1
        assert "Download failed" in result.stdout

    def test_twitter_command_download_exception(self, runner, mocker):
        """Test Twitter download command with exception."""
        # Mock TwitterHandler to raise exception
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.download.side_effect = Exception("Unexpected error")

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123"
        ])

        assert result.exit_code == 1
        assert "Download failed: Unexpected error" in result.stdout

    def test_twitter_command_verbose_output(self, runner, mocker, tmp_path):
        """Test Twitter command with verbose output."""
        # Mock TwitterHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock successful download with verbose data
        mock_result = DownloadResult(
            success=True,
            files=[tmp_path / "test.jpg"],
            stdout="gallery-dl verbose output",
            metadata={"title": "Test", "author": "User"}
        )
        mock_handler.download.return_value = mock_result

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--verbose"
        ])

        assert result.exit_code == 0
        assert "Command Output:" in result.stdout
        assert "gallery-dl verbose output" in result.stdout
        assert "Metadata:" in result.stdout

    def test_twitter_command_custom_output_dir(self, runner, mocker, tmp_path):
        """Test Twitter command with custom output directory."""
        custom_dir = tmp_path / "custom_downloads"

        # Mock TwitterHandler initialization
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.TwitterHandler')
        mock_handler = mock_handler_class.return_value

        # Mock both the validation and download handlers
        mock_handler.supports_url.return_value = True  # For validation
        mock_handler.download.return_value = DownloadResult(success=True)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--output-dir", str(custom_dir)
        ])

        # Verify TwitterHandler was called twice (validation + download)
        assert mock_handler_class.call_count == 2

        # Check the second call (download handler) has custom directory
        call_args = mock_handler_class.call_args_list[1]  # Second call
        assert call_args[1]['download_dir'] == custom_dir

        # Verify directory was created
        assert custom_dir.exists()

    def test_download_command_help(self, runner):
        """Test download command help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Download content from various platforms" in result.stdout
        assert "twitter" in result.stdout
        assert "info" in result.stdout

    def test_twitter_command_help(self, runner):
        """Test Twitter command help output."""
        result = runner.invoke(app, ["twitter", "--help"])

        assert result.exit_code == 0
        assert "Download Twitter/X content" in result.stdout
        assert "--metadata-only" in result.stdout
        assert "--async" in result.stdout
        assert "--verbose" in result.stdout
        assert "--output-dir" in result.stdout
