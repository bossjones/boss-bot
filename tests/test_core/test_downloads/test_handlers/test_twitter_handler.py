"""Tests for TwitterHandler."""

import json
from pathlib import Path

import pytest

from boss_bot.core.downloads.handlers.twitter_handler import TwitterHandler
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


class TestTwitterHandler:
    """Test TwitterHandler functionality."""

    @pytest.fixture
    def handler(self, tmp_path):
        """Create TwitterHandler with temporary directory."""
        return TwitterHandler(download_dir=tmp_path)

    def test_platform_properties(self, handler):
        """Test platform properties."""
        assert handler.platform_name == "twitter"
        assert handler.supported_domains == ["twitter.com", "x.com"]

    def test_supports_url(self, handler):
        """Test URL support detection."""
        # Supported URLs
        assert handler.supports_url("https://twitter.com/username/status/123456789")
        assert handler.supports_url("https://x.com/username/status/123456789")
        assert handler.supports_url("https://twitter.com/username")
        assert handler.supports_url("https://x.com/username")
        assert handler.supports_url("HTTPS://TWITTER.COM/USER/STATUS/123")  # Case insensitive

        # Unsupported URLs
        assert not handler.supports_url("https://youtube.com/watch")
        assert not handler.supports_url("https://facebook.com/post")
        assert not handler.supports_url("https://instagram.com/p/123")
        assert not handler.supports_url("not-a-url")

    def test_build_gallery_dl_command(self, handler):
        """Test gallery-dl command building."""
        url = "https://twitter.com/user/status/123"
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

    def test_download_unsupported_url(self, handler):
        """Test download with unsupported URL."""
        result = handler.download("https://youtube.com/watch")

        assert result.success is False
        assert "URL not supported by TwitterHandler" in result.error

    def test_download_success(self, handler, mocker):
        """Test successful download."""
        # Mock successful command execution
        mock_result = DownloadResult(
            success=True,
            stdout="gallery-dl output",
            return_code=0
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[Path("test.jpg")])
        mock_extract_metadata = mocker.patch.object(handler, '_extract_metadata_from_files', return_value={"title": "Test"})

        url = "https://twitter.com/user/status/123"
        result = handler.download(url)

        assert result.success is True
        assert result.files == [Path("test.jpg")]
        assert result.metadata == {"title": "Test"}

        # Verify method calls
        mock_run_command.assert_called_once()
        mock_find_files.assert_called_once_with(url)
        mock_extract_metadata.assert_called_once_with([Path("test.jpg")])

    def test_download_failure(self, handler, mocker):
        """Test failed download."""
        mock_result = DownloadResult(
            success=False,
            error="gallery-dl failed",
            return_code=1
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        url = "https://twitter.com/user/status/123"
        result = handler.download(url)

        assert result.success is False
        assert result.error == "gallery-dl failed"

    @pytest.mark.asyncio
    async def test_adownload_unsupported_url(self, handler):
        """Test async download with unsupported URL."""
        result = await handler.adownload("https://youtube.com/watch")

        assert result.success is False
        assert "URL not supported by TwitterHandler" in result.error

    @pytest.mark.asyncio
    async def test_adownload_success(self, handler, mocker):
        """Test successful async download."""
        # Mock successful async command execution
        mock_result = DownloadResult(
            success=True,
            stdout="gallery-dl output",
            return_code=0
        )

        mock_arun_command = mocker.patch.object(handler, '_arun_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[Path("test.jpg")])
        mock_extract_metadata = mocker.patch.object(handler, '_extract_metadata_from_files', return_value={"title": "Test"})

        url = "https://twitter.com/user/status/123"
        result = await handler.adownload(url)

        assert result.success is True
        assert result.files == [Path("test.jpg")]
        assert result.metadata == {"title": "Test"}

    def test_get_metadata_unsupported_url(self, handler):
        """Test metadata extraction with unsupported URL."""
        metadata = handler.get_metadata("https://youtube.com/watch")

        assert metadata.url == "https://youtube.com/watch"
        assert metadata.platform == "twitter"
        assert "URL not supported" in metadata.raw_metadata["error"]

    def test_get_metadata_success(self, handler, mocker):
        """Test successful metadata extraction."""
        mock_json_data = {
            "content": "Test tweet content",
            "author": {"name": "Test User"},
            "date": "2024-01-01",
            "favorite_count": 42,
            "retweet_count": 10
        }

        mock_result = DownloadResult(
            success=True,
            stdout=json.dumps(mock_json_data),
            return_code=0
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        url = "https://twitter.com/user/status/123"
        metadata = handler.get_metadata(url)

        assert metadata.title == "Test tweet content"
        assert metadata.uploader == "Test User"
        assert metadata.upload_date == "2024-01-01"
        assert metadata.like_count == 42
        assert metadata.view_count == 10
        assert metadata.platform == "twitter"
        assert metadata.url == url

    def test_get_metadata_failure(self, handler, mocker):
        """Test failed metadata extraction."""
        mock_result = DownloadResult(
            success=False,
            error="gallery-dl failed",
            return_code=1
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        url = "https://twitter.com/user/status/123"
        metadata = handler.get_metadata(url)

        assert metadata.url == url
        assert metadata.platform == "twitter"
        assert "gallery-dl failed" in metadata.raw_metadata["error"]

    def test_get_metadata_json_parse_error(self, handler, mocker):
        """Test metadata extraction with JSON parse error."""
        mock_result = DownloadResult(
            success=True,
            stdout="invalid json",
            return_code=0
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        url = "https://twitter.com/user/status/123"
        metadata = handler.get_metadata(url)

        assert metadata.url == url
        assert metadata.platform == "twitter"
        assert "Failed to parse metadata" in metadata.raw_metadata["error"]

    @pytest.mark.asyncio
    async def test_aget_metadata_success(self, handler, mocker):
        """Test successful async metadata extraction."""
        mock_json_data = {
            "content": "Test tweet content",
            "author": "Test User",
            "date": "2024-01-01"
        }

        mock_result = DownloadResult(
            success=True,
            stdout=json.dumps(mock_json_data),
            return_code=0
        )

        mock_arun_command = mocker.patch.object(handler, '_arun_command', return_value=mock_result)

        url = "https://twitter.com/user/status/123"
        metadata = await handler.aget_metadata(url)

        assert metadata.title == "Test tweet content"
        assert metadata.uploader == "Test User"
        assert metadata.platform == "twitter"

    def test_find_downloaded_files(self, handler, mocker):
        """Test finding downloaded files."""
        # Mock time.time to control file filtering
        mock_time = mocker.patch('time.time', return_value=1000.0)

        # Create mock files with different modification times
        old_file = mocker.Mock(spec=Path)
        old_file.stat.return_value.st_mtime = 500.0  # Too old

        recent_file = mocker.Mock(spec=Path)
        recent_file.stat.return_value.st_mtime = 800.0  # Recent enough

        # Mock glob to return our test files
        mock_glob = mocker.patch.object(handler.download_dir, 'glob')
        mock_glob.return_value = [old_file, recent_file]

        url = "https://twitter.com/user/status/123"
        files = handler._find_downloaded_files(url)

        # Should only return recent file
        assert files == [recent_file]

    def test_extract_metadata_from_files_no_json(self, handler):
        """Test metadata extraction with no JSON files."""
        files = [Path("test.jpg"), Path("test.mp4")]
        metadata = handler._extract_metadata_from_files(files)
        assert metadata is None

    def test_extract_metadata_from_files_success(self, handler, tmp_path):
        """Test successful metadata extraction from files."""
        # Create actual JSON file using tmp_path
        json_file = tmp_path / "test.json"
        test_metadata = {"title": "Test", "author": "User"}
        json_file.write_text(json.dumps(test_metadata))

        files = [tmp_path / "test.jpg", json_file]
        metadata = handler._extract_metadata_from_files(files)
        assert metadata == test_metadata

    def test_extract_metadata_from_files_json_error(self, handler, tmp_path):
        """Test metadata extraction with JSON error."""
        # Create invalid JSON file using tmp_path
        json_file = tmp_path / "test.json"
        json_file.write_text("invalid json")

        files = [json_file]
        metadata = handler._extract_metadata_from_files(files)
        assert metadata is None

    def test_parse_metadata(self, handler):
        """Test metadata parsing."""
        data = {
            "content": "Test tweet",
            "author": {"name": "Test User"},
            "date": "2024-01-01",
            "favorite_count": 100,
            "retweet_count": 50,
            "avatar": "https://example.com/avatar.jpg"
        }

        url = "https://twitter.com/user/status/123"
        metadata = handler._parse_metadata(data, url)

        assert metadata.title == "Test tweet"
        assert metadata.description == "Test tweet"
        assert metadata.uploader == "Test User"
        assert metadata.upload_date == "2024-01-01"
        assert metadata.like_count == 100
        assert metadata.view_count == 50
        assert metadata.thumbnail == "https://example.com/avatar.jpg"
        assert metadata.url == url
        assert metadata.platform == "twitter"
        assert metadata.raw_metadata == data

    def test_parse_metadata_string_author(self, handler):
        """Test metadata parsing with string author field."""
        data = {
            "content": "Test tweet",
            "author": "String Author",  # String instead of dict
            "date": "2024-01-01"
        }

        url = "https://twitter.com/user/status/123"
        metadata = handler._parse_metadata(data, url)

        assert metadata.uploader == "String Author"
        assert metadata.title == "Test tweet"
