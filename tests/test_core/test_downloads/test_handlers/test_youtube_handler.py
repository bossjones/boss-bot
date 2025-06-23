"""Tests for YouTube download handler."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from pytest_mock import MockerFixture
from unittest.mock import Mock

from boss_bot.core.downloads.handlers.youtube_handler import YouTubeHandler
from boss_bot.core.downloads.handlers.base_handler import DownloadResult, MediaMetadata


class TestYouTubeHandler:
    """Test suite for YouTube download handler."""

    @pytest.fixture
    def fixture_youtube_handler_test(self, tmp_path: Path) -> YouTubeHandler:
        """Create YouTubeHandler instance for testing."""
        return YouTubeHandler(download_dir=tmp_path)

    def test_platform_properties(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test platform-specific properties."""
        handler = fixture_youtube_handler_test

        assert handler.platform_name == "youtube"
        assert "youtube.com" in handler.supported_domains
        assert "youtu.be" in handler.supported_domains
        assert "music.youtube.com" in handler.supported_domains

    def test_supports_url(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test URL support detection."""
        handler = fixture_youtube_handler_test

        # Valid YouTube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/iJw5lVbIwao",  # YouTube Shorts
            "https://youtube.com/shorts/dQw4w9WgXcQ",  # YouTube Shorts without www
            "https://www.youtube.com/playlist?list=PLrUhA8hnVy",
            "https://www.youtube.com/channel/UC123456789",
            "https://www.youtube.com/user/username",
            "https://www.youtube.com/c/channelname",
            "https://www.youtube.com/@handle",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

        for url in valid_urls:
            assert handler.supports_url(url), f"Should support: {url}"

        # Invalid URLs
        invalid_urls = [
            "https://twitter.com/user/status/123",
            "https://instagram.com/p/ABC123/",
            "https://reddit.com/r/test/comments/abc/",
            "https://vimeo.com/123456789",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert not handler.supports_url(url), f"Should not support: {url}"

    def test_build_yt_dlp_command(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test yt-dlp command building."""
        handler = fixture_youtube_handler_test
        url = "https://www.youtube.com/watch?v=test"

        # Test default command
        cmd = handler._build_yt_dlp_command(url)

        assert "yt-dlp" in cmd
        assert "--format" in cmd
        assert "best[height<=720]" in cmd  # Default quality
        assert "--write-info-json" in cmd
        assert "--write-description" in cmd
        assert "--write-thumbnail" in cmd
        assert "--no-playlist" in cmd  # Single video by default
        assert url in cmd

    def test_build_yt_dlp_command_with_quality(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test yt-dlp command building with quality options."""
        handler = fixture_youtube_handler_test
        url = "https://www.youtube.com/watch?v=test"

        # Test 1080p quality
        cmd = handler._build_yt_dlp_command(url, quality="1080p")
        cmd_str = " ".join(cmd)
        assert "best[height<=1080]" in cmd_str

        # Test 4K quality
        cmd = handler._build_yt_dlp_command(url, quality="4K")
        cmd_str = " ".join(cmd)
        assert "best[height<=2160]" in cmd_str

        # Test best quality
        cmd = handler._build_yt_dlp_command(url, quality="best")
        cmd_str = " ".join(cmd)
        assert "--format best" in cmd_str

    def test_build_yt_dlp_command_audio_only(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test yt-dlp command building for audio-only downloads."""
        handler = fixture_youtube_handler_test
        url = "https://www.youtube.com/watch?v=test"

        cmd = handler._build_yt_dlp_command(url, audio_only=True, audio_format="mp3")
        cmd_str = " ".join(cmd)

        assert "--format bestaudio" in cmd_str
        assert "--extract-audio" in cmd_str
        assert "--audio-format mp3" in cmd_str

    def test_build_yt_dlp_command_with_options(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test yt-dlp command building with various options."""
        handler = fixture_youtube_handler_test
        url = "https://www.youtube.com/watch?v=test"

        cmd = handler._build_yt_dlp_command(
            url,
            subtitle_langs="en,es",
            user_agent="Custom Agent",
            verbose=True,
            retries=5
        )
        cmd_str = " ".join(cmd)

        assert "--write-subs" in cmd_str
        assert "--sub-langs en,es" in cmd_str
        assert "--user-agent Custom Agent" in cmd_str
        assert "--verbose" in cmd_str
        assert "--retries 5" in cmd_str

    def test_build_yt_dlp_command_metadata_only(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test yt-dlp command building for metadata-only mode."""
        handler = fixture_youtube_handler_test
        url = "https://www.youtube.com/watch?v=test"

        cmd = handler._build_yt_dlp_command(url, metadata_only=True)
        cmd_str = " ".join(cmd)

        assert "--skip-download" in cmd_str
        assert "--write-info-json" in cmd_str

    def test_download_unsupported_url(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test download with unsupported URL."""
        handler = fixture_youtube_handler_test

        result = handler.download("https://twitter.com/user/status/123")

        assert not result.success
        assert "not supported" in result.error.lower()

    def test_download_success(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test successful download."""
        handler = fixture_youtube_handler_test

        # Mock successful command execution
        mock_result = DownloadResult(
            success=True,
            stdout="Download completed",
            stderr="",
            return_code=0
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[])

        result = handler.download("https://www.youtube.com/watch?v=test")

        assert result.success
        assert result.stdout == "Download completed"
        mock_run_command.assert_called_once()
        mock_find_files.assert_called_once()

    def test_download_failure(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test download failure."""
        handler = fixture_youtube_handler_test

        # Mock failed command execution
        mock_result = DownloadResult(
            success=False,
            stdout="",
            stderr="yt-dlp error",
            return_code=1,
            error="yt-dlp command failed with return code 1"
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        result = handler.download("https://www.youtube.com/watch?v=test")

        assert not result.success
        assert "return code 1" in result.error
        assert result.stderr == "yt-dlp error"

    @pytest.mark.asyncio
    async def test_adownload_unsupported_url(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test async download with unsupported URL."""
        handler = fixture_youtube_handler_test

        result = await handler.adownload("https://twitter.com/user/status/123")

        assert not result.success
        assert "not supported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_adownload_success(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test successful async download."""
        handler = fixture_youtube_handler_test

        # Mock successful async command execution
        mock_result = DownloadResult(
            success=True,
            stdout="Download completed",
            stderr="",
            return_code=0
        )

        mock_arun_command = mocker.patch.object(handler, '_arun_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[])

        result = await handler.adownload("https://www.youtube.com/watch?v=test")

        assert result.success
        mock_arun_command.assert_called_once()
        mock_find_files.assert_called_once()

    def test_get_metadata_unsupported_url(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata extraction with unsupported URL."""
        handler = fixture_youtube_handler_test

        with pytest.raises(ValueError, match="not supported"):
            handler.get_metadata("https://twitter.com/user/status/123")

    def test_get_metadata_success(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test successful metadata extraction."""
        handler = fixture_youtube_handler_test

        # Mock successful command execution
        mock_result = DownloadResult(
            success=True,
            stdout="Metadata extracted",
            stderr="",
            return_code=0
        )

        expected_metadata = MediaMetadata(
            platform="youtube",
            url="https://www.youtube.com/watch?v=test",
            title="Test Video"
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[])
        mock_extract_metadata = mocker.patch.object(
            handler, '_extract_metadata_from_files',
            return_value=expected_metadata
        )

        result = handler.get_metadata("https://www.youtube.com/watch?v=test")

        assert result == expected_metadata
        mock_run_command.assert_called_once()

    def test_get_metadata_failure(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test metadata extraction failure."""
        handler = fixture_youtube_handler_test

        # Mock failed command execution
        mock_result = DownloadResult(
            success=False,
            stdout="",
            stderr="yt-dlp error",
            return_code=1
        )

        mock_run_command = mocker.patch.object(handler, '_run_command', return_value=mock_result)

        with pytest.raises(RuntimeError, match="metadata extraction failed"):
            handler.get_metadata("https://www.youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_aget_metadata_success(self, fixture_youtube_handler_test: YouTubeHandler, mocker: MockerFixture):
        """Test successful async metadata extraction."""
        handler = fixture_youtube_handler_test

        # Mock successful async command execution
        mock_result = DownloadResult(
            success=True,
            stdout="Metadata extracted",
            stderr="",
            return_code=0
        )

        expected_metadata = MediaMetadata(
            platform="youtube",
            url="https://www.youtube.com/watch?v=test",
            title="Test Video"
        )

        mock_arun_command = mocker.patch.object(handler, '_arun_command', return_value=mock_result)
        mock_find_files = mocker.patch.object(handler, '_find_downloaded_files', return_value=[])
        mock_extract_metadata = mocker.patch.object(
            handler, '_extract_metadata_from_files',
            return_value=expected_metadata
        )

        result = await handler.aget_metadata("https://www.youtube.com/watch?v=test")

        assert result == expected_metadata
        mock_arun_command.assert_called_once()

    def test_find_downloaded_files(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test finding downloaded files."""
        handler = fixture_youtube_handler_test

        # Create some test files
        video_file = handler.download_dir / "test_video.mp4"
        info_file = handler.download_dir / "test_video.info.json"
        thumbnail_file = handler.download_dir / "test_video.jpg"

        video_file.touch()
        info_file.touch()
        thumbnail_file.touch()

        files = handler._find_downloaded_files("https://www.youtube.com/watch?v=test")

        assert len(files) == 3
        file_names = [f.name for f in files]
        assert "test_video.mp4" in file_names
        assert "test_video.info.json" in file_names
        assert "test_video.jpg" in file_names

    def test_extract_metadata_from_files_no_json(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata extraction with no JSON files."""
        handler = fixture_youtube_handler_test

        # Create non-JSON files
        video_file = handler.download_dir / "test_video.mp4"
        video_file.touch()

        metadata = handler._extract_metadata_from_files([video_file])

        assert metadata.platform == "youtube"
        assert metadata.title == ""

    def test_extract_metadata_from_files_success(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test successful metadata extraction from JSON file."""
        handler = fixture_youtube_handler_test

        # Create JSON info file
        info_file = handler.download_dir / "test_video.info.json"
        metadata_json = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 120,
            "view_count": 1000,
            "like_count": 50,
            "upload_date": "20231215",
            "webpage_url": "https://www.youtube.com/watch?v=test"
        }

        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(metadata_json, f)

        metadata = handler._extract_metadata_from_files([info_file])

        assert metadata.platform == "youtube"
        assert metadata.title == "Test Video"
        assert metadata.uploader == "Test Channel"
        assert metadata.duration == 120
        assert metadata.view_count == 1000
        assert metadata.like_count == 50

    def test_extract_metadata_from_files_json_error(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata extraction with invalid JSON."""
        handler = fixture_youtube_handler_test

        # Create invalid JSON file
        info_file = handler.download_dir / "test_video.info.json"
        with open(info_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        metadata = handler._extract_metadata_from_files([info_file])

        assert metadata.platform == "youtube"
        assert "Failed to parse metadata" in metadata.error

    def test_parse_metadata(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata parsing from yt-dlp JSON."""
        handler = fixture_youtube_handler_test

        data = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 120,
            "view_count": 1000,
            "like_count": 50,
            "comment_count": 10,
            "upload_date": "20231215",
            "description": "Test description",
            "thumbnail": "https://img.youtube.com/vi/test/maxresdefault.jpg",
            "tags": ["test", "video"],
            "webpage_url": "https://www.youtube.com/watch?v=test"
        }

        metadata = handler._parse_metadata(data)

        assert metadata.platform == "youtube"
        assert metadata.title == "Test Video"
        assert metadata.uploader == "Test Channel"
        assert metadata.duration == 120
        assert metadata.view_count == 1000
        assert metadata.like_count == 50
        assert metadata.comment_count == 10
        assert metadata.upload_date == "20231215"
        assert metadata.description == "Test description"
        assert metadata.thumbnail_url == "https://img.youtube.com/vi/test/maxresdefault.jpg"
        assert metadata.tags == ["test", "video"]
        assert metadata.url == "https://www.youtube.com/watch?v=test"
        assert metadata.raw_metadata == data

    def test_parse_metadata_string_uploader(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata parsing with string uploader."""
        handler = fixture_youtube_handler_test

        data = {
            "title": "Test Video",
            "uploader": "Test Channel",  # String uploader
        }

        metadata = handler._parse_metadata(data)

        assert metadata.uploader == "Test Channel"

    def test_parse_metadata_dict_uploader(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata parsing with dict uploader."""
        handler = fixture_youtube_handler_test

        data = {
            "title": "Test Video",
            "uploader": {"name": "Test Channel", "id": "UC123"},  # Dict uploader
        }

        metadata = handler._parse_metadata(data)

        assert metadata.uploader == "Test Channel"

    def test_parse_metadata_channel_fallback(self, fixture_youtube_handler_test: YouTubeHandler):
        """Test metadata parsing with channel fallback."""
        handler = fixture_youtube_handler_test

        data = {
            "title": "Test Video",
            "channel": "Test Channel",  # Use channel as fallback
        }

        metadata = handler._parse_metadata(data)

        assert metadata.uploader == "Test Channel"
