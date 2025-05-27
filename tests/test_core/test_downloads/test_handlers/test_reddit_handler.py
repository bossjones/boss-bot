"""Tests for RedditHandler."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from boss_bot.core.downloads.handlers.reddit_handler import RedditHandler
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


class TestRedditHandler:
    """Test class for RedditHandler."""

    @pytest.fixture(scope="function")
    def handler(self, tmp_path) -> RedditHandler:
        """Create a RedditHandler instance for testing."""
        return RedditHandler(download_dir=tmp_path)

    def test_platform_properties(self, handler):
        """Test platform name and supported domains."""
        assert handler.platform_name == "reddit"
        assert "reddit.com" in handler.supported_domains
        assert "www.reddit.com" in handler.supported_domains
        assert "old.reddit.com" in handler.supported_domains

    def test_supports_url(self, handler):
        """Test URL support detection."""
        # Valid Reddit URLs
        valid_urls = [
            "https://reddit.com/r/pics/comments/abc123/title/",
            "https://www.reddit.com/r/funny/comments/def456/funny_post/",
            "https://old.reddit.com/r/technology/comments/ghi789/tech_news/",
        ]

        for url in valid_urls:
            assert handler.supports_url(url), f"Should support URL: {url}"

        # Invalid URLs
        invalid_urls = [
            "https://twitter.com/user/status/123",
            "https://youtube.com/watch?v=abc",
            "https://example.com",
            "",
            "not-a-url",
            "https://reddit.com/r/pics/",  # Missing comment ID
        ]

        for url in invalid_urls:
            assert not handler.supports_url(url), f"Should not support URL: {url}"

    def test_build_gallery_dl_command(self, handler):
        """Test gallery-dl command building."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Basic command
        cmd = handler._build_gallery_dl_command(url)
        expected = [
            "gallery-dl",
            "--no-mtime",
            "-v",
            "--write-info-json",
            "--write-metadata",
            url
        ]
        assert cmd == expected

        # With options
        options = {
            "metadata_only": True,
            "config_file": "/path/to/config.json",
            "cookies_file": "/path/to/cookies.txt"
        }
        cmd = handler._build_gallery_dl_command(url, **options)

        assert "--simulate" in cmd
        assert "--config" in cmd
        assert "/path/to/config.json" in cmd
        assert "--cookies" in cmd
        assert "/path/to/cookies.txt" in cmd

    def test_download_unsupported_url(self, handler):
        """Test download with unsupported URL."""
        url = "https://example.com"

        with pytest.raises(ValueError, match="URL not supported"):
            handler.download(url)

    def test_download_success(self, handler, mocker):
        """Test successful download."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock _run_command
        mock_run = mocker.patch.object(handler, '_run_command')
        mock_run.return_value = ("Download successful", "", 0)

        # Mock file finding
        mock_files = [Path("test1.jpg"), Path("test2.json")]
        mocker.patch.object(handler, '_find_downloaded_files', return_value=mock_files)

        # Mock metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Post",
            uploader="testuser",
            platform="reddit"
        )
        mocker.patch.object(handler, '_extract_metadata_from_files', return_value=mock_metadata)

        result = handler.download(url)

        assert result.success is True
        assert result.files == mock_files
        assert result.metadata == mock_metadata
        assert result.stdout == "Download successful"
        assert result.stderr == ""

    def test_download_failure(self, handler, mocker):
        """Test download failure."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock _run_command failure
        mock_run = mocker.patch.object(handler, '_run_command')
        mock_run.return_value = ("", "Command failed", 1)

        with pytest.raises(RuntimeError, match="gallery-dl failed"):
            handler.download(url)

    async def test_adownload_unsupported_url(self, handler):
        """Test async download with unsupported URL."""
        url = "https://example.com"

        with pytest.raises(ValueError, match="URL not supported"):
            await handler.adownload(url)

    async def test_adownload_success(self, handler, mocker):
        """Test successful async download."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock _arun_command
        mock_run = mocker.patch.object(handler, '_arun_command')
        mock_run.return_value = ("Download successful", "", 0)

        # Mock file finding
        mock_files = [Path("test1.jpg"), Path("test2.json")]
        mocker.patch.object(handler, '_find_downloaded_files', return_value=mock_files)

        # Mock metadata extraction
        mock_metadata = MediaMetadata(
            title="Test Post",
            uploader="testuser",
            platform="reddit"
        )
        mocker.patch.object(handler, '_extract_metadata_from_files', return_value=mock_metadata)

        result = await handler.adownload(url)

        assert result.success is True
        assert result.files == mock_files
        assert result.metadata == mock_metadata

    def test_get_metadata_unsupported_url(self, handler):
        """Test metadata extraction with unsupported URL."""
        url = "https://example.com"

        metadata = handler.get_metadata(url)
        assert metadata is None

    def test_get_metadata_success(self, handler, mocker):
        """Test successful metadata extraction."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock download method to return metadata
        mock_result = DownloadResult(
            success=True,
            files=[],
            metadata=MediaMetadata(title="Test", platform="reddit"),
            stdout="",
            stderr=""
        )
        mocker.patch.object(handler, 'download', return_value=mock_result)

        metadata = handler.get_metadata(url)
        assert metadata is not None
        assert metadata.title == "Test"

    def test_get_metadata_failure(self, handler, mocker):
        """Test metadata extraction failure."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock download to raise exception
        mocker.patch.object(handler, 'download', side_effect=Exception("Download failed"))

        metadata = handler.get_metadata(url)
        assert metadata is None

    def test_get_metadata_json_parse_error(self, handler, tmp_path, mocker):
        """Test metadata extraction with JSON parse error."""
        # Create invalid JSON file
        json_file = tmp_path / "test.json"
        json_file.write_text("invalid json content")

        # Mock file finding to return the invalid JSON file
        mocker.patch.object(handler, '_find_downloaded_files', return_value=[json_file])

        metadata = handler._extract_metadata_from_files([json_file])
        assert metadata is None

    async def test_aget_metadata_success(self, handler, mocker):
        """Test successful async metadata extraction."""
        url = "https://reddit.com/r/pics/comments/abc123/title/"

        # Mock adownload method to return metadata
        mock_result = DownloadResult(
            success=True,
            files=[],
            metadata=MediaMetadata(title="Async Test", platform="reddit"),
            stdout="",
            stderr=""
        )
        mocker.patch.object(handler, 'adownload', return_value=mock_result)

        metadata = await handler.aget_metadata(url)
        assert metadata is not None
        assert metadata.title == "Async Test"

    @pytest.mark.skip_until(datetime.now() + timedelta(days=30), reason="file discovery mocking fixes needed")
    def test_find_downloaded_files(self, handler, mocker):
        """Test finding downloaded files."""
        # This test needs proper filesystem mocking
        # Skipping until we can properly mock the file discovery
        pass

    def test_extract_metadata_from_files_no_json(self, handler):
        """Test metadata extraction with no JSON files."""
        files = [Path("test.jpg"), Path("test.mp4")]
        metadata = handler._extract_metadata_from_files(files)
        assert metadata is None

    def test_extract_metadata_from_files_success(self, handler, tmp_path):
        """Test successful metadata extraction from JSON files."""
        # Create JSON file with Reddit metadata
        json_file = tmp_path / "test.json"
        reddit_data = {
            "title": "Test Reddit Post",
            "author": "testuser",
            "subreddit": "pics",
            "score": 42,
            "num_comments": 15,
            "created_utc": 1672531200,
            "url": "https://reddit.com/r/pics/comments/abc123/title/",
            "thumbnail": "https://reddit.com/thumb.jpg",
            "description": "Test description",
            "selftext": "Test selftext",
            "post_hint": "image",
            "domain": "i.redd.it",
            "permalink": "/r/pics/comments/abc123/title/"
        }
        json_file.write_text(json.dumps(reddit_data))

        files = [json_file]
        metadata = handler._extract_metadata_from_files(files)

        assert metadata is not None
        assert metadata.title == "Test Reddit Post"
        assert metadata.uploader == "testuser"
        assert metadata.like_count == 42
        assert metadata.platform == "reddit"
        assert metadata.raw_metadata["subreddit"] == "pics"
        assert metadata.raw_metadata["num_comments"] == 15

    def test_extract_metadata_from_files_json_error(self, handler, tmp_path):
        """Test metadata extraction with JSON decode error."""
        # Create invalid JSON file
        json_file = tmp_path / "test.json"
        json_file.write_text("invalid json")

        files = [json_file]
        metadata = handler._extract_metadata_from_files(files)
        assert metadata is None

    def test_parse_metadata(self, handler):
        """Test metadata parsing from Reddit data."""
        reddit_data = {
            "title": "Amazing Photo",
            "author": "photographer123",
            "subreddit": "EarthPorn",
            "score": 1337,
            "num_comments": 89,
            "created_utc": 1672531200,
            "url": "https://reddit.com/r/EarthPorn/comments/xyz789/amazing_photo/",
            "thumbnail": "https://reddit.com/thumb.jpg",
            "selftext": "Taken on my vacation",
            "post_hint": "image",
            "domain": "i.redd.it",
            "permalink": "/r/EarthPorn/comments/xyz789/amazing_photo/"
        }

        metadata = handler._parse_metadata(reddit_data)

        assert metadata.title == "Amazing Photo"
        assert metadata.uploader == "photographer123"
        assert metadata.description == "Taken on my vacation"
        assert metadata.like_count == 1337
        assert metadata.upload_date == 1672531200
        assert metadata.thumbnail == "https://reddit.com/thumb.jpg"
        assert metadata.platform == "reddit"
        assert metadata.url == "https://reddit.com/r/EarthPorn/comments/xyz789/amazing_photo/"
        assert metadata.raw_metadata["subreddit"] == "EarthPorn"
        assert metadata.raw_metadata["num_comments"] == 89
        assert metadata.raw_metadata["post_hint"] == "image"

    def test_parse_metadata_string_author(self, handler):
        """Test metadata parsing with string author instead of dict."""
        reddit_data = {
            "title": "Test Post",
            "author": "string_user",  # String instead of dict
            "subreddit": "test",
            "score": 10,
            "num_comments": 2
        }

        metadata = handler._parse_metadata(reddit_data)

        assert metadata.uploader == "string_user"
        assert metadata.title == "Test Post"
        assert metadata.raw_metadata["subreddit"] == "test"
