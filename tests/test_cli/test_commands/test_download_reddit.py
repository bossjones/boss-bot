"""Tests for Reddit CLI download commands."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from boss_bot.cli.commands.download import app


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestValidateRedditUrl:
    """Test Reddit URL validation."""

    def test_valid_reddit_urls(self):
        """Test validation of valid Reddit URLs."""
        runner = CliRunner()

        valid_urls = [
            "https://reddit.com/r/pics/comments/abc123/title/",
            "https://www.reddit.com/r/funny/comments/def456/funny_post/",
            "https://old.reddit.com/r/technology/comments/ghi789/tech_news/",
        ]

        for url in valid_urls:
            result = runner.invoke(app, ["reddit", url, "--metadata-only"])
            # Should not fail with URL validation error
            assert "URL is not a valid Reddit URL" not in result.stdout

    def test_invalid_reddit_urls(self):
        """Test validation of invalid Reddit URLs."""
        runner = CliRunner()

        invalid_urls = [
            "https://twitter.com/user/status/123",
            "https://youtube.com/watch?v=abc",
            "https://example.com",
            "not-a-url",
        ]

        for url in invalid_urls:
            result = runner.invoke(app, ["reddit", url])
            assert result.exit_code == 2  # Typer validation error
            assert "URL is not a valid Reddit URL" in result.stdout


class TestRedditCommands:
    """Test Reddit download commands."""

    def test_reddit_command_invalid_url(self):
        """Test Reddit command with invalid URL."""
        runner = CliRunner()
        result = runner.invoke(app, ["reddit", "https://invalid-url.com"])

        assert result.exit_code == 2
        assert "URL is not a valid Reddit URL" in result.stdout

    def test_reddit_command_metadata_only_success(self, mocker):
        """Test Reddit command with metadata-only flag."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True

        # Mock metadata
        mock_metadata = mocker.Mock()
        mock_metadata.title = "Test Reddit Post"
        mock_metadata.uploader = "testuser"
        mock_metadata.like_count = 42
        mock_metadata.upload_date = "2023-01-01"
        mock_metadata.raw_metadata = {"subreddit": "pics", "num_comments": 15}
        mock_handler.get_metadata.return_value = mock_metadata

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--metadata-only"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Test Reddit Post" in clean_stdout
        assert "testuser" in clean_stdout

    def test_reddit_command_metadata_only_async(self, mocker):
        """Test Reddit command with metadata-only and async flags."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True

        # Mock async metadata
        async def mock_aget_metadata(url, **options):
            metadata = mocker.Mock()
            metadata.title = "Async Reddit Post"
            metadata.uploader = "asyncuser"
            metadata.raw_metadata = {"subreddit": "test"}
            return metadata

        mock_handler.aget_metadata = mock_aget_metadata

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--metadata-only",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Metadata extracted successfully" in clean_stdout
        assert "Async Reddit Post" in clean_stdout

    def test_reddit_command_metadata_failure(self, mocker):
        """Test Reddit command with metadata extraction failure."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True
        mock_handler.get_metadata.side_effect = Exception("Metadata extraction failed")

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--metadata-only"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Failed to extract metadata" in clean_stdout
        assert "Metadata extraction failed" in clean_stdout

    def test_reddit_command_download_success(self, mocker):
        """Test Reddit command with successful download."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation

        # Mock successful download result
        async def mock_adownload(url, **options):
            result = mocker.Mock()
            result.success = True
            result.files = [Path("test1.jpg"), Path("test2.mp4")]
            result.stdout = "Download output"
            result.stderr = ""
            result.metadata = None
            return result

        def mock_download(url, **options):
            result = mocker.Mock()
            result.success = True
            result.files = [Path("test1.jpg"), Path("test2.mp4")]
            result.stdout = "Download output"
            result.stderr = ""
            result.metadata = None
            return result

        mock_handler.adownload = mock_adownload
        mock_handler.download = mock_download

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 2 files" in clean_stdout

    def test_reddit_command_download_async_success(self, mocker):
        """Test Reddit command with successful async download."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation

        # Mock successful async download result
        async def mock_adownload(url, **options):
            result = mocker.Mock()
            result.success = True
            result.files = [Path("async1.jpg"), Path("async2.mp4")]
            result.stdout = "Async download output"
            result.stderr = ""
            result.metadata = None
            return result

        mock_handler.adownload = mock_adownload

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--async"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Downloaded 2 files" in clean_stdout

    def test_reddit_command_download_failure(self, mocker):
        """Test Reddit command with download failure."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation

        # Mock failed download result
        def mock_download(url, **options):
            result = mocker.Mock()
            result.success = False
            result.error = "Download failed"
            result.stderr = "Error details"
            return result

        mock_handler.download = mock_download

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout

    def test_reddit_command_download_exception(self, mocker):
        """Test Reddit command with download exception."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation
        mock_handler.download.side_effect = Exception("Download exception")

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/"
        ])

        assert result.exit_code == 1
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download failed" in clean_stdout
        assert "Download exception" in clean_stdout

    def test_reddit_command_verbose_output(self, mocker):
        """Test Reddit command with verbose flag."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation

        # Mock successful download with verbose output
        def mock_download(url, **options):
            result = mocker.Mock()
            result.success = True
            result.files = [Path("verbose.jpg")]
            result.stdout = "Verbose download output"
            result.stderr = ""
            result.metadata = {"title": "Verbose Test"}
            return result

        mock_handler.download = mock_download

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--verbose"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Verbose download output" in clean_stdout

    def test_reddit_command_custom_options(self, mocker):
        """Test Reddit command with custom config and cookies."""
        runner = CliRunner()

        # Mock RedditHandler
        mock_handler_class = mocker.patch('boss_bot.cli.commands.download.RedditHandler')
        mock_handler = mock_handler_class.return_value
        mock_handler.supports_url.return_value = True  # For validation

        # Mock successful download
        def mock_download(url, **options):
            # Verify options are passed
            assert "config_file" in options
            assert "cookies_file" in options
            result = mocker.Mock()
            result.success = True
            result.files = [Path("custom.jpg")]
            result.stdout = "Custom download"
            result.stderr = ""
            result.metadata = None
            return result

        mock_handler.download = mock_download

        result = runner.invoke(app, [
            "reddit",
            "https://reddit.com/r/pics/comments/abc123/title/",
            "--config", "config.json",
            "--cookies", "cookies.txt"
        ])

        assert result.exit_code == 0
        clean_stdout = strip_ansi_codes(result.stdout)
        assert "Download completed successfully" in clean_stdout
        assert "Config File: config.json" in clean_stdout
        assert "Cookies File: cookies.txt" in clean_stdout

    def test_download_command_help(self):
        """Test download command help includes Reddit."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "reddit" in result.stdout
        assert "Download Reddit content" in result.stdout

    def test_reddit_command_help(self):
        """Test Reddit command specific help."""
        runner = CliRunner()
        result = runner.invoke(app, ["reddit", "--help"])

        assert result.exit_code == 0
        assert "Download Reddit content using gallery-dl" in result.stdout
        assert "--config" in result.stdout
        assert "--cookies" in result.stdout
        assert "--metadata-only" in result.stdout
