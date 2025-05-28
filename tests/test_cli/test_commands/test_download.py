"""Tests for CLI download commands."""

import asyncio
import re
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from boss_bot.cli.commands.download import app, validate_twitter_url
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestDownloadCommands:
    """Test download CLI commands using strategy pattern."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_download_info_command(self, runner):
        """Test download info command."""
        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "BossBot Download Commands" in clean_stdout
        assert "Twitter/X" in clean_stdout
        assert "gallery-dl" in clean_stdout

    def test_twitter_command_invalid_url(self, runner):
        """Test Twitter download with invalid URL."""
        result = runner.invoke(app, ["twitter", "https://youtube.com/watch"])

        assert result.exit_code == 2  # typer.BadParameter exit code
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "URL is not a valid Twitter/X URL" in clean_stdout

    def test_twitter_command_metadata_only_success(self, runner, mocker):
        """Test Twitter metadata-only command success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

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
        mock_strategy.get_metadata = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Test Tweet" in clean_stdout
        assert "Test User" in clean_stdout
        mock_strategy.get_metadata.assert_called_once()

    def test_twitter_command_metadata_only_async(self, runner, mocker):
        """Test Twitter metadata-only command with async mode."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful async metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Tweet Async",
            uploader="Test User Async",
            upload_date="2024-01-01",
            like_count=24,
            view_count=5,
            url="https://twitter.com/user/status/123",
            platform="twitter"
        )
        mock_strategy.get_metadata = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Test Tweet Async" in clean_stdout
        assert "Test User Async" in clean_stdout
        mock_strategy.get_metadata.assert_called_once()

    def test_twitter_command_metadata_failure(self, runner, mocker):
        """Test Twitter metadata command failure."""
        # Mock get_strategy_for_platform to raise exception
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True
        mock_strategy.get_metadata = mocker.AsyncMock(side_effect=Exception("Metadata extraction failed"))

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--metadata-only"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Failed to extract metadata" in clean_stdout

    def test_twitter_command_download_success(self, runner, mocker):
        """Test Twitter download command success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download
        mock_metadata = MediaMetadata(
            title="Test Tweet",
            uploader="Test User",
            platform="twitter",
            download_method="cli",
            files=["file1.jpg", "file2.mp4"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 2 files" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_twitter_command_download_async_success(self, runner, mocker):
        """Test Twitter download command with async mode success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download
        mock_metadata = MediaMetadata(
            title="Test Tweet",
            uploader="Test User",
            platform="twitter",
            download_method="api",
            files=["file1.jpg"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 1 files" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_twitter_command_download_failure(self, runner, mocker):
        """Test Twitter download command failure."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock download failure
        mock_metadata = MediaMetadata(
            platform="twitter",
            error="Download failed: Network error"
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout

    def test_twitter_command_download_exception(self, runner, mocker):
        """Test Twitter download command with exception."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True
        mock_strategy.download = mocker.AsyncMock(side_effect=Exception("Connection error"))

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout

    def test_twitter_command_verbose_output(self, runner, mocker):
        """Test Twitter command with verbose output."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download with metadata
        mock_metadata = MediaMetadata(
            title="Test Tweet",
            uploader="Test User",
            platform="twitter",
            raw_metadata={"test": "data"},
            files=["file1.jpg"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--verbose"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_twitter_command_custom_output_dir(self, runner, mocker, tmp_path):
        """Test Twitter command with custom output directory."""
        # Mock get_strategy_for_platform function to check download_dir
        def mock_get_strategy(platform, download_dir):
            mock_strategy = mocker.Mock()
            mock_strategy.supports_url.return_value = True

            # Mock successful download
            mock_metadata = MediaMetadata(
                title="Test Tweet",
                platform="twitter",
                files=["file1.jpg"]
            )
            mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)
            return mock_strategy

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', side_effect=mock_get_strategy)

        custom_dir = tmp_path / "custom_downloads"
        result = runner.invoke(app, [
            "twitter",
            "https://twitter.com/user/status/123",
            "--output-dir", str(custom_dir)
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        # Check that custom directory was created
        assert custom_dir.exists()
