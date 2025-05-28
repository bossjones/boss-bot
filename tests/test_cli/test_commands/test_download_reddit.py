"""Tests for CLI Reddit download commands."""

import asyncio
import re
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from boss_bot.cli.commands.download import app
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestRedditCommands:
    """Test Reddit CLI commands using strategy pattern."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_reddit_command_invalid_url(self, runner):
        """Test Reddit download with invalid URL."""
        result = runner.invoke(app, ["reddit", "https://youtube.com/watch"])

        assert result.exit_code == 2  # typer.BadParameter exit code
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "URL is not a valid Reddit URL" in clean_stdout

    def test_reddit_command_metadata_only_success(self, runner, mocker):
        """Test Reddit metadata-only command success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Reddit Post",
            uploader="test_user",
            upload_date="2024-01-01",
            like_count=100,
            url="https://reddit.com/r/test/comments/abc123/title/",
            platform="reddit",
            raw_metadata={"subreddit": "test", "num_comments": 42}
        )
        mock_strategy.get_metadata = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--metadata-only"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Test Reddit Post" in clean_stdout
        assert "test_user" in clean_stdout
        mock_strategy.get_metadata.assert_called_once()

    def test_reddit_command_metadata_only_async(self, runner, mocker):
        """Test Reddit metadata-only command with async mode."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful async metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Reddit Post Async",
            uploader="test_user_async",
            upload_date="2024-01-01",
            like_count=50,
            url="https://reddit.com/r/test/comments/abc123/title/",
            platform="reddit",
            raw_metadata={"subreddit": "test", "num_comments": 24}
        )
        mock_strategy.get_metadata = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--metadata-only",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Test Reddit Post Async" in clean_stdout
        assert "test_user_async" in clean_stdout
        mock_strategy.get_metadata.assert_called_once()

    def test_reddit_command_metadata_failure(self, runner, mocker):
        """Test Reddit metadata command failure."""
        # Mock get_strategy_for_platform to raise exception
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True
        mock_strategy.get_metadata = mocker.AsyncMock(side_effect=Exception("Metadata extraction failed"))

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--metadata-only"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Failed to extract metadata" in clean_stdout

    def test_reddit_command_download_success(self, runner, mocker):
        """Test Reddit download command success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download
        mock_metadata = MediaMetadata(
            title="Test Reddit Post",
            uploader="test_user",
            platform="reddit",
            download_method="cli",
            files=["reddit_post.jpg", "reddit_video.mp4"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 2 files" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_reddit_command_download_async_success(self, runner, mocker):
        """Test Reddit download command with async mode success."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download
        mock_metadata = MediaMetadata(
            title="Test Reddit Post",
            uploader="test_user",
            platform="reddit",
            download_method="api",
            files=["reddit_post.jpg"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 1 files" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_reddit_command_download_failure(self, runner, mocker):
        """Test Reddit download command failure."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock download failure
        mock_metadata = MediaMetadata(
            platform="reddit",
            error="Download failed: Network error"
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout

    def test_reddit_command_download_exception(self, runner, mocker):
        """Test Reddit download command with exception."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True
        mock_strategy.download = mocker.AsyncMock(side_effect=Exception("Connection error"))

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout

    def test_reddit_command_verbose_output(self, runner, mocker):
        """Test Reddit command with verbose output."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download with metadata
        mock_metadata = MediaMetadata(
            title="Test Reddit Post",
            uploader="test_user",
            platform="reddit",
            raw_metadata={"test": "data"},
            files=["reddit_post.jpg"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--verbose"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_reddit_command_custom_options(self, runner, mocker, tmp_path):
        """Test Reddit command with custom config and cookies options."""
        # Mock get_strategy_for_platform function
        mock_strategy = mocker.Mock()
        mock_strategy.supports_url.return_value = True

        # Mock successful download
        mock_metadata = MediaMetadata(
            title="Test Reddit Post",
            platform="reddit",
            files=["reddit_post.jpg"]
        )
        mock_strategy.download = mocker.AsyncMock(return_value=mock_metadata)

        mocker.patch('boss_bot.cli.commands.download.get_strategy_for_platform', return_value=mock_strategy)

        # Create temp files for testing
        config_file = tmp_path / "config.json"
        config_file.write_text('{"test": "config"}')
        cookies_file = tmp_path / "cookies.txt"
        cookies_file.write_text('test=cookie')

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/test/comments/abc123/title/",
            "--config", str(config_file),
            "--cookies", str(cookies_file)
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        mock_strategy.download.assert_called_once()

    def test_reddit_command_help(self, runner):
        """Test Reddit command help message."""
        result = runner.invoke(app, ["reddit", "--help"])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download Reddit content using strategy pattern" in clean_stdout
        assert "--metadata-only" in clean_stdout
        assert "--async" in clean_stdout
        assert "--config" in clean_stdout
        assert "--cookies" in clean_stdout
